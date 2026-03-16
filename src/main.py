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
        self.setAcceptDrops(True)

        self.engine = PavoEngine()
        
        self.hud_timer = QTimer(self)
        self.hud_timer.setInterval(2000)
        self.hud_timer.timeout.connect(self.hide_hud)
        
        # 用于记录画中画状态和恢复前的尺寸
        self._is_pip = False
        self._normal_geometry = None

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

        # 顶部 OSD
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

        # 动画引擎
        self.opacity_effect = QGraphicsOpacityEffect(self.hud)
        self.opacity_effect.setOpacity(1.0)
        self.hud.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(250)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.finished.connect(self._on_fade_finished)

        self.osd_opacity_effect = QGraphicsOpacityEffect(self.top_osd)
        self.osd_opacity_effect.setOpacity(1.0)
        self.top_osd.setGraphicsEffect(self.osd_opacity_effect)
        self.osd_fade_anim = QPropertyAnimation(self.osd_opacity_effect, b"opacity")
        self.osd_fade_anim.setDuration(250)
        self.osd_fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.osd_fade_anim.setEndValue(1.0)

        # 连线
        self.hud.play_state_changed.connect(self.engine.set_playing)
        self.hud.volume_changed.connect(self.engine.set_volume)
        self.hud.mute_changed.connect(self.engine.set_mute)
        self.hud.seek_requested.connect(self.engine.seek_to_percent)
        self.hud.skip_requested.connect(self.on_skip)
        self.hud.fullscreen_requested.connect(self.toggle_fullscreen)
        
        # 连接新的 CC 和 PiP 按钮信号
        if hasattr(self.hud, 'settings_btn'):
            self.hud.settings_btn.clicked.connect(self.show_settings_menu)
        if hasattr(self.hud, 'subtitle_btn'):
            self.hud.subtitle_requested.connect(self.show_subtitle_menu)
        if hasattr(self.hud, 'pip_btn'):
            self.hud.pip_requested.connect(self.toggle_pip)

        if hasattr(self.hud, 'user_activity'):
            self.hud.user_activity.connect(self.wake_hud)

        if hasattr(self.video_canvas, 'clicked'):
            self.video_canvas.clicked.connect(self.hud.toggle_play_ui)
        if hasattr(self.video_canvas, 'double_clicked'):
            self.video_canvas.double_clicked.connect(self.toggle_fullscreen)
        if hasattr(self.video_canvas, 'file_dropped'):
            self.video_canvas.file_dropped.connect(self.handle_dropped_file)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sync_progress)
        self.timer.start(500)

    # ==========================================
    # 👑 画中画模式 (PiP) 核心逻辑与精简模式切换
    # ==========================================
    def toggle_pip(self):
        if not self._is_pip:
            # 开启画中画
            self._normal_geometry = self.geometry()
            self._is_pip = True
            
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.showNormal() 
            self.resize(480, 270) 
            self.show()
            
            # 命令 HUD 进入精简模式
            if hasattr(self.hud, 'set_pip_mode'):
                self.hud.set_pip_mode(True)
            
            self.top_osd.setText("🚀 已进入画中画模式")
            self.top_osd.adjustSize()
            self.resizeEvent(None)
            self.wake_hud()
        else:
            # 退出画中画
            self._is_pip = False
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            if self._normal_geometry:
                self.setGeometry(self._normal_geometry)
            self.show()
            
            # 命令 HUD 恢复完全体
            if hasattr(self.hud, 'set_pip_mode'):
                self.hud.set_pip_mode(False)
                
            # 👑 核心修复：强制取消用户的拖拽状态，让面板乖乖回到默认底部中央！
            if hasattr(self.hud, '_user_dragged'):
                self.hud._user_dragged = False
                
            # 👑 核心修复：更新提示文字，并触发重新排版
            self.top_osd.setText("🔙 已恢复正常模式")
            self.top_osd.adjustSize()
            self.resizeEvent(None)
            self.wake_hud()

    def handle_dropped_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.srt', '.ass', '.vtt', '.ssa']:
            self.engine.add_external_subtitle(file_path)
            self.top_osd.setText(f"💬 字幕已加载：{os.path.basename(file_path)}")
            self.top_osd.adjustSize()
            self.resizeEvent(None)
            self.wake_hud()
        else:
            self.load_local_video(file_path)

    def load_local_video(self, file_path):
        filename = os.path.basename(file_path)
        self.top_osd.setText(f"🎬 正在播放：{filename}")
        self.top_osd.adjustSize()
        self.resizeEvent(None) 
        self.wake_hud()
        self.engine.play(file_path)
        if hasattr(self.hud, 'is_playing'):
            self.hud.is_playing = True
            self.hud.play_btn.setIcon(self.hud.icons['pause'])

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

    # ==========================================
    # 👑 独立出来的 CC 字幕菜单
    # ==========================================
    def show_subtitle_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(45, 45, 45, 240);
                color: white;
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 30px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #007AFF;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 30);
                margin: 4px 10px;
            }
        """)
        
        sub_tracks = self.engine.get_subtitle_tracks()
        
        action_disable = QAction("🚫 关闭字幕", self)
        action_disable.setCheckable(True)
        has_selected_sub = any(t['selected'] for t in sub_tracks)
        if not has_selected_sub: action_disable.setChecked(True)
        action_disable.triggered.connect(lambda: self.engine.set_subtitle_track('no'))
        menu.addAction(action_disable)
        menu.addSeparator()

        for t in sub_tracks:
            action = QAction(t['name'], self)
            action.setCheckable(True)
            if t['selected']: action.setChecked(True)
            action.triggered.connect(lambda checked, val=t['id']: self.engine.set_subtitle_track(val))
            menu.addAction(action)

        btn_pos = self.hud.subtitle_btn.mapToGlobal(QPoint(0, 0))
        menu.exec(btn_pos - QPoint(0, menu.sizeHint().height() + 10))

    # ==========================================
    # 👑 设置菜单 (现在只管音轨和倍速)
    # ==========================================
    def show_settings_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(45, 45, 45, 240);
                color: white;
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 30px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #007AFF;
            }
        """)

        speed_menu = menu.addMenu("⏩ 倍速播放")
        speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        current_speed = getattr(self.engine, 'playback_speed', 1.0)
        for s in speeds:
            action = QAction(f"{s}x", self)
            action.setCheckable(True)
            if s == current_speed: action.setChecked(True)
            action.triggered.connect(lambda checked, val=s: self.change_speed(val))
            speed_menu.addAction(action)

        audio_tracks = self.engine.get_audio_tracks()
        if audio_tracks:
            audio_menu = menu.addMenu("🎧 切换音轨")
            for t in audio_tracks:
                action = QAction(t['name'], self)
                action.setCheckable(True)
                if t['selected']: action.setChecked(True)
                action.triggered.connect(lambda checked, val=t['id']: self.engine.set_audio_track(val))
                audio_menu.addAction(action)

        btn_pos = self.hud.settings_btn.mapToGlobal(QPoint(0, 0))
        menu.exec(btn_pos - QPoint(0, menu.sizeHint().height() + 10))

    def change_speed(self, speed):
        if hasattr(self.engine, 'set_speed'):
            self.engine.set_speed(speed)
            self.engine.playback_speed = speed 

    def resizeEvent(self, event):
        if event: super().resizeEvent(event)
        if hasattr(self, 'top_osd'):
            osd_w = self.top_osd.width()
            osd_x = (self.width() - osd_w) // 2
            self.top_osd.move(osd_x, 30)
        if hasattr(self, 'hud'):
            hud_w = min(600, self.width() - 40)
            self.hud.setFixedWidth(hud_w)
            
            # 这一行就是靠 _user_dragged 决定要不要居中的！
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