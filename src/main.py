import os
import sys
import bootstrap
bootstrap.setup_pavo_env()

from PySide6.QtWidgets import (QApplication, QMainWindow, QGridLayout, QWidget, 
                             QGraphicsOpacityEffect, QMenu, QLabel)
from PySide6.QtGui import QSurfaceFormat, QAction, QKeyEvent
from PySide6.QtCore import Qt, QTimer, QEvent, QPropertyAnimation, QEasingCurve, QPoint, QUrl

from engine import PavoEngine
from video_widget import PavoVideoWidget
from components.hud_panel import HUDPanel

class PavoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pavo") 
        self.resize(1000, 600)
        self.setStyleSheet("background-color: black;")
        
        # 兜底：主窗口也开启拖拽接收
        self.setAcceptDrops(True)

        self.engine = PavoEngine()
        
        self.hud_timer = QTimer(self)
        self.hud_timer.setInterval(2000)
        self.hud_timer.timeout.connect(self.hide_hud)

        self.init_ui()

        QApplication.instance().installEventFilter(self)
        self.hud_timer.start()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QGridLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.video_canvas = PavoVideoWidget(self.engine)
        self.main_layout.addWidget(self.video_canvas, 0, 0)

        self.hud = HUDPanel(self.central_widget)
        self.hud.raise_()

        # ==========================================
        # 👑 顶部 OSD 信息栏 (显示文件名/拖拽提示)
        # ==========================================
        self.top_osd = QLabel(self.central_widget)
        self.top_osd.setAlignment(Qt.AlignCenter)
        self.top_osd.setText("✨ 请将视频文件拖拽至此播放")
        self.top_osd.setStyleSheet("""
            QLabel {
                background-color: rgba(40, 40, 40, 180);
                color: rgba(255, 255, 255, 230);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 12px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
        """)
        self.top_osd.adjustSize()
        self.top_osd.raise_()

        # --- 底部 HUD 的动画引擎 ---
        self.opacity_effect = QGraphicsOpacityEffect(self.hud)
        self.opacity_effect.setOpacity(1.0)
        self.hud.setGraphicsEffect(self.opacity_effect)

        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(250)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.finished.connect(self._on_fade_finished)

        # --- 顶部 OSD 的同步动画引擎 ---
        self.osd_opacity_effect = QGraphicsOpacityEffect(self.top_osd)
        self.osd_opacity_effect.setOpacity(1.0)
        self.top_osd.setGraphicsEffect(self.osd_opacity_effect)

        self.osd_fade_anim = QPropertyAnimation(self.osd_opacity_effect, b"opacity")
        self.osd_fade_anim.setDuration(250)
        self.osd_fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.osd_fade_anim.setEndValue(1.0)

        # ==========================================
        # 👑 信号与槽连线
        # ==========================================
        # 1. HUD 控制连线
        self.hud.play_state_changed.connect(self.engine.set_playing)
        self.hud.volume_changed.connect(self.engine.set_volume)
        self.hud.mute_changed.connect(self.engine.set_mute)
        self.hud.seek_requested.connect(self.engine.seek_to_percent)
        
        self.hud.skip_requested.connect(self.on_skip)
        self.hud.fullscreen_requested.connect(self.toggle_fullscreen)
        
        if hasattr(self.hud, 'settings_btn'):
            self.hud.settings_btn.clicked.connect(self.show_settings_menu)

        if hasattr(self.hud, 'user_activity'):
            self.hud.user_activity.connect(self.wake_hud)

        # 2. 画布交互连线 (单双击 + 拖拽接受)
        if hasattr(self.video_canvas, 'clicked'):
            self.video_canvas.clicked.connect(self.hud.toggle_play_ui)
        if hasattr(self.video_canvas, 'double_clicked'):
            self.video_canvas.double_clicked.connect(self.toggle_fullscreen)
        
        # 👑 最核心的一步：接住画布发来的拖拽路径！
        if hasattr(self.video_canvas, 'file_dropped'):
            self.video_canvas.file_dropped.connect(self.load_local_video)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sync_progress)
        self.timer.start(500)

    # ==========================================
    # 👑 拖拽播放核心逻辑
    # ==========================================
    def dragEnterEvent(self, event):
        # 兜底机制：如果拖拽事件漏到了主窗口，也接收它
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        # 兜底机制
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.load_local_video(file_path)

    def load_local_video(self, file_path):
        """加载本地视频并更新 UI"""
        # 提取文件名
        filename = os.path.basename(file_path)
        self.top_osd.setText(f"正在播放：{filename}")
        self.top_osd.adjustSize()
        self.resizeEvent(None)  # 重新居中 OSD

        # 唤醒面板展示信息
        self.wake_hud()
        
        # 通知引擎播放新视频！
        self.engine.play(file_path)

        # 确保播放按钮状态重置为“暂停”图标 (表示正在播放)
        if hasattr(self.hud, 'is_playing'):
            self.hud.is_playing = True
            self.hud.play_btn.setIcon(self.hud.icons['pause'])

    # ==========================================
    # 基础功能逻辑
    # ==========================================
    def on_skip(self, seconds):
        curr, total = self.engine.get_progress()
        if total <= 0: return
        new_time = max(0, min(total, curr + seconds))
        self.engine.seek_to_percent(new_time / total)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
        self.resizeEvent(None)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
        elif event.key() == Qt.Key_Space:
            self.hud.toggle_play_ui()
        super().keyPressEvent(event)

    def show_settings_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(45, 45, 45, 230);
                color: white;
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 6px 25px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #007AFF;
            }
        """)

        speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        current_speed = getattr(self.engine, 'playback_speed', 1.0)

        for s in speeds:
            action = QAction(f"{s}x", self)
            action.setCheckable(True)
            if s == current_speed:
                action.setChecked(True)
            action.triggered.connect(lambda checked, val=s: self.change_speed(val))
            menu.addAction(action)

        btn_pos = self.hud.settings_btn.mapToGlobal(QPoint(0, 0))
        menu.exec(btn_pos - QPoint(0, menu.sizeHint().height() + 5))

    def change_speed(self, speed):
        if hasattr(self.engine, 'set_speed'):
            self.engine.set_speed(speed)
            self.engine.playback_speed = speed 

    def resizeEvent(self, event):
        if event: super().resizeEvent(event)
        
        # 动态居中顶部 OSD
        if hasattr(self, 'top_osd'):
            osd_w = self.top_osd.width()
            osd_x = (self.width() - osd_w) // 2
            self.top_osd.move(osd_x, 30)

        # 动态响应底部 HUD
        if hasattr(self, 'hud'):
            hud_w = min(520, self.width() - 40)
            self.hud.setFixedWidth(hud_w)
            if not getattr(self.hud, '_user_dragged', False):
                x = (self.width() - hud_w) // 2
                y = self.height() - self.hud.height() - 40
                self.hud.move(x, y)
            else:
                max_x = self.width() - hud_w
                max_y = self.height() - self.hud.height()
                new_x = max(0, min(self.hud.x(), max_x))
                new_y = max(0, min(self.hud.y(), max_y))
                self.hud.move(new_x, new_y)

    def sync_progress(self):
        current, total = self.engine.get_progress()
        self.hud.update_progress(current, total)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove:
            self.wake_hud()
        return super().eventFilter(obj, event)

    def leaveEvent(self, event):
        self.hud_timer.stop()
        self.hide_hud()
        super().leaveEvent(event)

    # ==========================================
    # 👑 同步呼吸动画：底部面板与顶部 OSD 同进同退
    # ==========================================
    def wake_hud(self):
        if self.opacity_effect.opacity() < 1.0 and self.fade_anim.endValue() != 1.0:
            self.hud.show()
            self.top_osd.show()

            self.fade_anim.stop()
            self.fade_anim.setStartValue(self.opacity_effect.opacity())
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()

            self.osd_fade_anim.stop()
            self.osd_fade_anim.setStartValue(self.osd_opacity_effect.opacity())
            self.osd_fade_anim.setEndValue(1.0)
            self.osd_fade_anim.start()

        if getattr(self.hud, 'is_playing', True):
            self.hud_timer.start()

    def hide_hud(self):
        if not self.hud.isHidden() and getattr(self.hud, 'is_playing', True) and self.fade_anim.endValue() != 0.0:
            self.fade_anim.stop()
            self.fade_anim.setStartValue(self.opacity_effect.opacity())
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()

            self.osd_fade_anim.stop()
            self.osd_fade_anim.setStartValue(self.osd_opacity_effect.opacity())
            self.osd_fade_anim.setEndValue(0.0)
            self.osd_fade_anim.start()

    def _on_fade_finished(self):
        if self.fade_anim.endValue() == 0.0:
            self.hud.hide()
            self.top_osd.hide()

if __name__ == "__main__":
    fmt = QSurfaceFormat()
    fmt.setVersion(4, 1)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    window = PavoPlayer()
    window.show()
    sys.exit(app.exec())