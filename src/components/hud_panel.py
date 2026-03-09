import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QGraphicsDropShadowEffect, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

class HUDPanel(QWidget):
    play_state_changed = Signal(bool)
    volume_changed = Signal(int)
    mute_changed = Signal(bool)
    seek_requested = Signal(float)
    skip_requested = Signal(int)
    fullscreen_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.is_playing = True 
        self.is_muted = False      
        self.last_seek_time = 0  
        self.init_ui()

    def init_ui(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40) 
        shadow.setColor(QColor(0, 0, 0, 180)) 
        shadow.setOffset(0, 15) 
        self.setGraphicsEffect(shadow)

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
                border-radius: 30px;
            }
            QPushButton {
                background-color: transparent; 
                border: none;
                color: rgba(255, 255, 255, 210);
                font-family: "SF Pro Rounded", "Arial Rounded MT Bold", -apple-system, sans-serif;
            }
            QPushButton:hover {
                color: rgba(255, 255, 255, 255);
            }
            /* 👑 核心修复 1：视觉层次 CSS 强制接管 */
            QPushButton#PlayBtn {
                font-size: 36px; /* 核心按键，大幅放大 */
            }
            QPushButton#SkipBtn {
                font-size: 18px; /* 辅助按键，保持小巧，作为配重 */
                letter-spacing: -1px; /* 微调间距，形成紧凑的图标 */
            }
            QPushButton#MuteBtn {
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 2px;
            }
            QPushButton#UtilBtn {
                font-size: 20px;
                font-weight: 600;
            }
            QLabel {
                color: rgba(255, 255, 255, 210);
                font-size: 13px;
                font-weight: 600;
                font-family: "Courier New", monospace; 
                background: transparent;
            }
            QWidget#TransparentContainer {
                background-color: transparent;
                border: none;
            }
            QSlider {
                background: transparent;
            }
            QSlider::groove:horizontal {
                border-radius: 2px;
                height: 4px;
                background: rgba(0, 0, 0, 80); 
            }
            QSlider::sub-page:horizontal {
                background: white; 
                border-radius: 2px;
            }
            QSlider::add-page:horizontal {
                background: transparent;
            }
            QSlider::handle:horizontal {
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
                background: white;
                border: none;
            }
            QSlider::handle:horizontal:hover {
                background: rgba(255, 255, 255, 255);
                width: 16px;
                height: 16px;
                margin: -6px -2px;
                border-radius: 8px;
            }
        """)
        self.setFixedHeight(105) 
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(35, 15, 35, 15)
        self.main_layout.setSpacing(8)

        self.time_layout = QHBoxLayout()
        self.time_layout.setContentsMargins(0, 0, 0, 0)
        self.time_layout.setSpacing(15)

        self.curr_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setObjectName("ProgressBar")
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setCursor(Qt.PointingHandCursor)
        self.progress_slider.sliderMoved.connect(self.on_slider_moved)
        self.progress_slider.sliderReleased.connect(self.on_seek)
        
        self.time_layout.addWidget(self.curr_time_label)
        self.time_layout.addWidget(self.progress_slider)
        self.time_layout.addWidget(self.total_time_label)

        self.main_layout.addLayout(self.time_layout)

        self.controls_layout = QHBoxLayout()
        self.controls_layout.setContentsMargins(0, 0, 0, 0)

        self.left_group = QWidget()
        self.left_group.setObjectName("TransparentContainer")
        self.left_group.setFixedWidth(160) 
        left_layout = QHBoxLayout(self.left_group)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        self.mute_btn = QPushButton("VOL") 
        self.mute_btn.setObjectName("MuteBtn")
        self.mute_btn.setFixedSize(40, 30)
        self.mute_btn.setCursor(Qt.PointingHandCursor)
        self.mute_btn.clicked.connect(self.toggle_mute_ui)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setObjectName("VolumeBar")
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(100)
        self.vol_slider.setCursor(Qt.PointingHandCursor)
        self.vol_slider.valueChanged.connect(self.volume_changed.emit)

        left_layout.addWidget(self.mute_btn)
        left_layout.addWidget(self.vol_slider)

        self.center_group = QWidget()
        self.center_group.setObjectName("TransparentContainer")
        center_layout = QHBoxLayout(self.center_group)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(15)

        self.rewind_btn = QPushButton("◄◄") 
        self.rewind_btn.setObjectName("SkipBtn")
        # 放大物理占位，确保大字符不被裁切
        self.rewind_btn.setFixedSize(60, 60)
        self.rewind_btn.setCursor(Qt.PointingHandCursor)
        self.rewind_btn.clicked.connect(lambda: self.skip_requested.emit(-10))

        # 👑 核心修复 2：暂停图案替换为实心双竖杠 ▮▮
        self.play_btn = QPushButton("▮▮")
        self.play_btn.setObjectName("PlayBtn")
        self.play_btn.setFixedSize(60, 60)
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.clicked.connect(self.toggle_play_ui)

        self.forward_btn = QPushButton("►►") 
        self.forward_btn.setObjectName("SkipBtn")
        self.forward_btn.setFixedSize(60, 60)
        self.forward_btn.setCursor(Qt.PointingHandCursor)
        self.forward_btn.clicked.connect(lambda: self.skip_requested.emit(10))

        center_layout.addWidget(self.rewind_btn)
        center_layout.addWidget(self.play_btn)
        center_layout.addWidget(self.forward_btn)

        self.right_group = QWidget()
        self.right_group.setObjectName("TransparentContainer")
        self.right_group.setFixedWidth(160)
        right_layout = QHBoxLayout(self.right_group)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)
        right_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.settings_btn = QPushButton("•••")
        self.settings_btn.setObjectName("UtilBtn")
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setCursor(Qt.PointingHandCursor)

        self.fullscreen_btn = QPushButton("⛶")
        self.fullscreen_btn.setObjectName("UtilBtn")
        self.fullscreen_btn.setFixedSize(30, 30)
        self.fullscreen_btn.setCursor(Qt.PointingHandCursor)
        self.fullscreen_btn.clicked.connect(self.fullscreen_requested.emit)

        right_layout.addWidget(self.settings_btn)
        right_layout.addWidget(self.fullscreen_btn)

        self.controls_layout.addWidget(self.left_group)
        self.controls_layout.addStretch()
        self.controls_layout.addWidget(self.center_group)
        self.controls_layout.addStretch()
        self.controls_layout.addWidget(self.right_group)

        self.main_layout.addLayout(self.controls_layout)

    def toggle_play_ui(self):
        self.is_playing = not self.is_playing
        # 👑 核心修复 3：播放/暂停时的字符对应替换
        self.play_btn.setText("▮▮" if self.is_playing else "►") 
        self.play_state_changed.emit(self.is_playing)

    def toggle_mute_ui(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.mute_btn.setText("MUT")
            self.mute_btn.setStyleSheet("color: rgba(255, 80, 80, 255);")
        else:
            self.mute_btn.setText("VOL")
            self.mute_btn.setStyleSheet("color: rgba(255, 255, 255, 210);")
        self.mute_changed.emit(self.is_muted)

    def on_slider_moved(self, value):
        current_time = time.time()
        if current_time - self.last_seek_time > 0.15:
            percent = value / 1000.0
            self.seek_requested.emit(percent)
            self.last_seek_time = current_time

    def on_seek(self):
        percent = self.progress_slider.value() / 1000.0
        self.seek_requested.emit(percent)
        self.last_seek_time = time.time()

    def format_time(self, seconds):
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def update_progress(self, current, total):
        if total > 0:
            self.curr_time_label.setText(self.format_time(current))
            self.total_time_label.setText(self.format_time(total))
            if not self.progress_slider.isSliderDown():
                val = int((current / total) * 1000)
                self.progress_slider.setValue(val)