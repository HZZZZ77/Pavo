import sys
import bootstrap
bootstrap.setup_pavo_env()

# 👑 引入动画需要的核心组件
from PySide6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QGraphicsOpacityEffect
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtCore import Qt, QTimer, QEvent, QPropertyAnimation, QEasingCurve

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
        
        # ==========================================
        # 👑 修复 Bug：程序启动时，主动点燃第一发 2 秒倒计时炸弹！
        # 这样无论鼠标初始在哪，UI 都会在 2 秒后乖乖按照呼吸效果隐藏
        # ==========================================
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

        # ==========================================
        # 👑 新增：给面板装配独立的透明度引擎
        # ==========================================
        self.opacity_effect = QGraphicsOpacityEffect(self.hud) # 只作用于 hud，不作用于全屏
        self.opacity_effect.setOpacity(1.0)
        self.hud.setGraphicsEffect(self.opacity_effect)

        # 装配动画曲线
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(250) # 250毫秒的丝滑过渡
        self.fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_anim.setEndValue(1.0) # 初始化状态
        self.fade_anim.finished.connect(self._on_fade_finished)

        self.main_layout.addWidget(self.overlay, 0, 0)

        # 核心连线
        self.hud.play_state_changed.connect(self.engine.set_playing)
        self.hud.volume_changed.connect(self.engine.set_volume)
        self.hud.mute_changed.connect(self.engine.set_mute)
        self.hud.seek_requested.connect(self.engine.seek_to_percent)

        if hasattr(self.hud, 'user_activity'):
            self.hud.user_activity.connect(self.wake_hud)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sync_progress)
        self.timer.start(500)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        if hasattr(self, 'hud'):
            # 👑 1. 无论是否被拖拽过，UI 的“宽度”都必须保持绝对的响应式！
            # 保证它最大 520px，但在极小窗口下也能自动缩窄，绝不溢出
            hud_w = min(520, self.width() - 40)
            self.hud.setFixedWidth(hud_w)
            
            # 👑 2. 处理“位置”逻辑
            if not getattr(self.hud, '_user_dragged', False):
                # 状态 A：没拖拽过，乖乖在底部居中
                x = (self.width() - hud_w) // 2
                y = self.height() - self.hud.height() - 40
                self.hud.move(x, y)
            else:
                # 状态 B：用户手动拖拽过。
                # 尊重用户放置的位置，但是加上“动态空气墙”，防止窗口缩小时把 UI 吞掉！
                current_x = self.hud.x()
                current_y = self.hud.y()
                
                # 计算当前窗口的安全边界
                max_x = self.width() - hud_w
                max_y = self.height() - self.hud.height()
                
                # 强制修正坐标：绝不小于0（左上角），也绝不大于最大边界（右下角）
                new_x = max(0, min(current_x, max_x))
                new_y = max(0, min(current_y, max_y))
                
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
    # 👑 升级：带“防抖锁”的呼吸淡入淡出逻辑
    # ==========================================
    def wake_hud(self):
        # 【防抖锁】：只有在透明度未满，且没有在向1.0淡入时，才启动动画
        if self.opacity_effect.opacity() < 1.0 and self.fade_anim.endValue() != 1.0:
            self.hud.show()
            self.fade_anim.stop()
            self.fade_anim.setStartValue(self.opacity_effect.opacity())
            self.fade_anim.setEndValue(1.0) # 目标：完全显示
            self.fade_anim.start()

        # 无论如何都要重置自动隐藏的倒计时
        if getattr(self.hud, 'is_playing', True):
            self.hud_timer.start()

    def hide_hud(self):
        # 【防抖锁】：只有在显示状态，且没有在向0.0淡出时，才启动动画
        if not self.hud.isHidden() and getattr(self.hud, 'is_playing', True) and self.fade_anim.endValue() != 0.0:
            self.fade_anim.stop()
            self.fade_anim.setStartValue(self.opacity_effect.opacity())
            self.fade_anim.setEndValue(0.0) # 目标：完全透明
            self.fade_anim.start()

    def _on_fade_finished(self):
        # 物理隐藏：当淡出彻底完成时，隐藏组件，防止“看不见的面板”阻挡底层的鼠标点击
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