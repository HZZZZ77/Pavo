from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSlider, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

class HUDPanel(QWidget):
    play_state_changed = Signal(bool)
    volume_changed = Signal(int)
    mute_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.is_playing = True 
        self.is_muted = False      
        self.current_volume = 100  
        self.init_ui()

    def init_ui(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40) 
        shadow.setColor(QColor(0, 0, 0, 180)) 
        shadow.setOffset(0, 15) 
        self.setGraphicsEffect(shadow)

        # 这一次，我保证里面没有任何非法的 '#' 注释！
        self.setStyleSheet("""
            HUDPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 rgba(255, 255, 255, 30),
                                            stop:0.5 rgba(200, 200, 200, 15),
                                            stop:1 rgba(150, 150, 150, 25));
                border-top: 1px solid rgba(255, 255, 255, 160);
                border-left: 1px solid rgba(255, 255, 255, 90);
                border-right: 1px solid rgba(255, 255, 255, 90);
                border-bottom: 1px solid rgba(255, 255, 255, 30);
                border-radius: 40px;
            }
            QPushButton {
                background-color: transparent; 
                border: none;
                color: rgba(255, 255, 255, 220); 
            }
            QPushButton:hover {
                color: rgba(255, 255, 255, 255);
            }
            QPushButton#PlayBtn {
                font-size: 48px;
            }
            QPushButton#MuteBtn {
                font-size: 14px;
                font-weight: 800;
                letter-spacing: 2px;
            }
            QWidget#VolumeContainer {
                background-color: transparent;
                border: none;
            }
            QSlider {
                background: transparent;
            }
            QSlider::groove:horizontal {
                border-radius: 3px;
                height: 6px;
                background: rgba(0, 0, 0, 80); 
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid rgba(0, 0, 0, 50);
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: rgba(255, 255, 255, 255);
            }
            QSlider::sub-page:horizontal {
                background: white; 
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background: transparent;
            }
        """)
        self.setFixedHeight(80) 
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(40, 0, 40, 0)

        self.volume_group = QWidget()
        self.volume_group.setObjectName("VolumeContainer")
        self.volume_group.setFixedWidth(130) 
        vol_layout = QHBoxLayout(self.volume_group)
        vol_layout.setContentsMargins(0, 0, 0, 0)
        vol_layout.setSpacing(10)
        
        self.mute_btn = QPushButton("VOL") 
        self.mute_btn.setObjectName("MuteBtn")
        self.mute_btn.setFixedSize(40, 40)
        self.mute_btn.setCursor(Qt.PointingHandCursor)
        self.mute_btn.clicked.connect(self.toggle_mute_ui)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(100)
        self.vol_slider.setCursor(Qt.PointingHandCursor)
        self.vol_slider.valueChanged.connect(self.volume_changed.emit)

        vol_layout.addWidget(self.mute_btn)
        vol_layout.addWidget(self.vol_slider)

        self.left_spacer = QWidget()
        self.left_spacer.setFixedWidth(130) 
        # 强制显式声明左侧占位符透明
        self.left_spacer.setStyleSheet("background-color: transparent; border: none;")

        self.play_btn = QPushButton("⏸")
        self.play_btn.setObjectName("PlayBtn")
        self.play_btn.setFixedSize(60, 60)
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.clicked.connect(self.toggle_play_ui)

        self.layout.addWidget(self.left_spacer)
        self.layout.addStretch()
        self.layout.addWidget(self.play_btn)
        self.layout.addStretch()
        self.layout.addWidget(self.volume_group)

    def toggle_play_ui(self):
        self.is_playing = not self.is_playing
        self.play_btn.setText("⏸" if self.is_playing else "▶") 
        self.play_state_changed.emit(self.is_playing)

    def toggle_mute_ui(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.mute_btn.setText("MUT")
            self.mute_btn.setStyleSheet("color: rgba(255, 80, 80, 255);")
        else:
            self.mute_btn.setText("VOL")
            self.mute_btn.setStyleSheet("color: rgba(255, 255, 255, 220);")
        self.mute_changed.emit(self.is_muted)