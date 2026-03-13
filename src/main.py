import sys
import bootstrap
bootstrap.setup_pavo_env()

# 👑 引入 QMenu 和 QAction 用于实现“三个点”菜单
from PySide6.QtWidgets import (QApplication, QMainWindow, QGridLayout, QWidget, 
                             QGraphicsOpacityEffect, QMenu)
from PySide6.QtGui import QSurfaceFormat, QAction, QKeyEvent
from PySide6.QtCore import Qt, QTimer, QEvent, QPropertyAnimation, QEasingCurve, QPoint

from engine import PavoEngine
from video_widget import PavoVideoWidget
from components.hud_panel import HUDPanel

class PavoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pavo") 
        self.resize(1000, 600)
        self.setStyleSheet("background-color: black;")

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

        self.overlay = QWidget()
        self.overlay.setAttribute(Qt.WA_TranslucentBackground) 
        
        self.hud = HUDPanel(self.overlay)

        self.opacity_effect = QGraphicsOpacityEffect(self.hud)
        self.opacity_effect.setOpacity(1.0)
        self.hud.setGraphicsEffect(self.opacity_effect)

        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(250)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.finished.connect(self._on_fade_finished)

        self.main_layout.addWidget(self.overlay, 0, 0)

        # ==========================================
        # 👑 V0.9.1 核心连线：激活所有按钮功能
        # ==========================================
        self.hud.play_state_changed.connect(self.engine.set_playing)
        self.hud.volume_changed.connect(self.engine.set_volume)
        self.hud.mute_changed.connect(self.engine.set_mute)
        self.hud.seek_requested.connect(self.engine.seek_to_percent)
        
        # 1. 激活快进快退 (10秒)
        self.hud.skip_requested.connect(self.on_skip)
        
        # 2. 激活全屏切换
        self.hud.fullscreen_requested.connect(self.toggle_fullscreen)
        
        # 3. 激活设置菜单 (三个点)
        if hasattr(self.hud, 'settings_btn'):
            self.hud.settings_btn.clicked.connect(self.show_settings_menu)

        if hasattr(self.hud, 'user_activity'):
            self.hud.user_activity.connect(self.wake_hud)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sync_progress)
        self.timer.start(500)

    # ==========================================
    # 👑 V0.9.1 功能实现逻辑
    # ==========================================
    
    def on_skip(self, seconds):
        """处理前后跳转逻辑"""
        curr, total = self.engine.get_progress()
        if total <= 0: return
        # 计算新位置的百分比
        new_time = max(0, min(total, curr + seconds))
        self.engine.seek_to_percent(new_time / total)

    def toggle_fullscreen(self):
        """切换全屏状态"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
        # 强制触发一次 resize 逻辑以纠正 HUD 位置
        self.resizeEvent(None)

    def keyPressEvent(self, event: QKeyEvent):
        """键盘快捷键支持"""
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
        elif event.key() == Qt.Key_Space:
            # 空格键控制播放/暂停
            self.hud.toggle_play_ui()
        super().keyPressEvent(event)

    def show_settings_menu(self):
        """点击三个点弹出倍速菜单"""
        menu = QMenu(self)
        # 👑 给菜单也加上一点 IINA 的暗色高级感
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
            # 使用 lambda 传参切换倍速
            action.triggered.connect(lambda checked, val=s: self.change_speed(val))
            menu.addAction(action)

        # 在按钮上方弹出菜单
        btn_pos = self.hud.settings_btn.mapToGlobal(QPoint(0, 0))
        menu.exec(btn_pos - QPoint(0, menu.sizeHint().height() + 5))

    def change_speed(self, speed):
        """调用引擎切换倍速"""
        if hasattr(self.engine, 'set_speed'):
            self.engine.set_speed(speed)
            self.engine.playback_speed = speed # 记录状态

    # ==========================================
    # 👑 基础 UI 维护逻辑 (保持不变)
    # ==========================================

    def resizeEvent(self, event):
        if event: super().resizeEvent(event)
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

    def wake_hud(self):
        if self.opacity_effect.opacity() < 1.0 and self.fade_anim.endValue() != 1.0:
            self.hud.show()
            self.fade_anim.stop()
            self.fade_anim.setStartValue(self.opacity_effect.opacity())
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()
        if getattr(self.hud, 'is_playing', True):
            self.hud_timer.start()

    def hide_hud(self):
        if not self.hud.isHidden() and getattr(self.hud, 'is_playing', True) and self.fade_anim.endValue() != 0.0:
            self.fade_anim.stop()
            self.fade_anim.setStartValue(self.opacity_effect.opacity())
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()

    def _on_fade_finished(self):
        if self.fade_anim.endValue() == 0.0:
            self.hud.hide()

if __name__ == "__main__":
    fmt = QSurfaceFormat()
    fmt.setVersion(4, 1)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    window = PavoPlayer()
    window.show()
    sys.exit(app.exec())