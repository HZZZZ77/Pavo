import sys
import bootstrap
bootstrap.setup_pavo_env()

from PySide6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtCore import Qt, QTimer, QEvent # 👑 仅新增了 QEvent

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
        
        # 👑 新增 1：设定 2 秒自动隐藏的定时炸弹
        self.hud_timer = QTimer(self)
        self.hud_timer.setInterval(2000)
        self.hud_timer.timeout.connect(self.hide_hud)

        self.init_ui()

        # 👑 新增 2：给整个应用装上“隐形雷达”，捕捉鼠标移动，绝不干扰底层视频
        QApplication.instance().installEventFilter(self)

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QGridLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.video_canvas = PavoVideoWidget(self.engine)
        self.main_layout.addWidget(self.video_canvas, 0, 0)

        self.overlay = QWidget()
        self.overlay.setAttribute(Qt.WA_TranslucentBackground) 
        
        # 👑 修改：删除了 overlay_layout，直接把 hud 作为 overlay 的绝对子组件，这样才能随意拖拽！
        self.hud = HUDPanel(self.overlay)

        self.main_layout.addWidget(self.overlay, 0, 0)

        # 核心连线
        self.hud.play_state_changed.connect(self.engine.set_playing)
        self.hud.volume_changed.connect(self.engine.set_volume)
        self.hud.mute_changed.connect(self.engine.set_mute)
        self.hud.seek_requested.connect(self.engine.seek_to_percent)

        # 👑 新增 3：接收面板传来的鼠标操作信号，重置 2 秒隐藏倒计时
        if hasattr(self.hud, 'user_activity'):
            self.hud.user_activity.connect(self.wake_hud)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sync_progress)
        self.timer.start(500)

    # 👑 新增 4：因为去掉了 Layout 布局，我们需要在窗口缩放时手动帮 UI 居中
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 如果用户还没有手动拖拽过 UI，就自动帮它水平居中并在底部对齐
        if hasattr(self, 'hud') and not getattr(self.hud, '_user_dragged', False):
            hud_w = int(self.width() * 0.7)
            self.hud.setFixedWidth(hud_w)
            x = (self.width() - hud_w) // 2
            y = self.height() - self.hud.height() - 40
            self.hud.move(x, y)

    def sync_progress(self):
        current, total = self.engine.get_progress()
        self.hud.update_progress(current, total)

    # ==========================================
    # 👑 新增 5：沉浸式感知雷达处理中枢
    # ==========================================
    def eventFilter(self, obj, event):
        # 只要鼠标在窗口内滑动，就立刻唤醒 UI
        if event.type() == QEvent.MouseMove:
            self.wake_hud()
        return super().eventFilter(obj, event)

    def leaveEvent(self, event):
        # 鼠标移出播放窗口外，立刻隐藏 UI
        self.hud_timer.stop()
        self.hide_hud()
        super().leaveEvent(event)

    def wake_hud(self):
        if self.hud.isHidden():
            self.hud.show()
        # 只要正在播放，就开始 2 秒倒计时
        if getattr(self.hud, 'is_playing', True):
            self.hud_timer.start()

    def hide_hud(self):
        if not self.hud.isHidden() and getattr(self.hud, 'is_playing', True):
            self.hud.hide()

# ==========================================
# 启动块保持原封不动！
# ==========================================
if __name__ == "__main__":
    fmt = QSurfaceFormat()
    fmt.setVersion(4, 1)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    window = PavoPlayer()
    window.show()
    sys.exit(app.exec())