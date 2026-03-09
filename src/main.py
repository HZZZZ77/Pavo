import sys
import bootstrap
bootstrap.setup_pavo_env()

from PySide6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QVBoxLayout
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtCore import Qt

from engine import PavoEngine
from video_widget import PavoVideoWidget
from components.hud_panel import HUDPanel

class PavoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        # 【你的试金石】：如果你运行后标题不是下面这个，说明你没保存成功！
        self.setWindowTitle("Pavo - 悬浮测试版") 
        self.resize(1000, 600)
        self.setStyleSheet("background-color: black;")

        self.engine = PavoEngine()
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QGridLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.video_canvas = PavoVideoWidget(self.engine)
        self.main_layout.addWidget(self.video_canvas, 0, 0)

        self.overlay = QWidget()
        self.overlay.setAttribute(Qt.WA_TranslucentBackground) 
        
        self.overlay_layout = QVBoxLayout(self.overlay)
        self.overlay_layout.setContentsMargins(0, 0, 0, 40) 
        
        self.hud = HUDPanel()
        self.overlay_layout.addWidget(self.hud, 0, Qt.AlignHCenter | Qt.AlignBottom)

        self.main_layout.addWidget(self.overlay, 0, 0)

if __name__ == "__main__":
    fmt = QSurfaceFormat()
    fmt.setVersion(4, 1)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    window = PavoPlayer()
    window.show()
    sys.exit(app.exec())