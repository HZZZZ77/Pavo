from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt

class HUDPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # 定义一个状态变量，记录当前是否正在播放
        self.is_playing = True 
        
        self.init_ui()

    def init_ui(self):
        # 【严谨修正】：将 QWidget 改为 HUDPanel，防止样式“污染”到内部的按钮
        self.setStyleSheet("""
            HUDPanel {
                background-color: rgba(30, 30, 30, 220);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 20px;
            }
            /* 新增：专门针对按钮的极简样式 */
            QPushButton {
                color: white;
                background-color: transparent;
                border: none;
                font-size: 48px;
            }
            /* 新增：鼠标悬停时的微交互（颜色微微变暗） */
            QPushButton:hover {
                color: rgba(255, 255, 255, 150);
            }
        """)
        self.setFixedHeight(80)
        self.setMinimumWidth(400)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 0, 20, 0)

        # === 核心添加：纯净几何播放按钮 ===
        # 因为视频是默认自动播放的，所以初始图标设为“暂停(⏸)”
        self.play_btn = QPushButton("⏸")
        self.play_btn.setFixedSize(70, 70)
        self.play_btn.setCursor(Qt.PointingHandCursor) # 鼠标放上去变小手
        
        # 将按钮点击事件，连接到我们自定义的开关函数上
        self.play_btn.clicked.connect(self.toggle_play_ui)

        # 把按钮加进面板的布局里，并强制居中
        self.layout.addWidget(self.play_btn, alignment=Qt.AlignCenter)

    # UI 层的状态切换函数
    def toggle_play_ui(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_btn.setText("⏸") # 正在播放，显示暂停图标
        else:
            self.play_btn.setText("▶") # 已暂停，显示播放图标