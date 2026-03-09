import sys
import bootstrap
bootstrap.setup_pavo_env()

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtGui import QSurfaceFormat

from engine import PavoEngine
from video_widget import PavoVideoWidget

class PavoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        # 【修改点】：极简且专业的标题
        self.setWindowTitle("Pavo") 
        self.resize(1000, 600)

        self.engine = PavoEngine()
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.video_canvas = PavoVideoWidget(self.engine)
        self.layout.addWidget(self.video_canvas)

if __name__ == "__main__":
    fmt = QSurfaceFormat()
    fmt.setVersion(4, 1)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    fmt.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    window = PavoPlayer()
    window.show()
    
    sys.exit(app.exec())