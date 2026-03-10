import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QGraphicsDropShadowEffect, QLabel
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor

class HUDPanel(QWidget):
    play_state_changed = Signal(bool)
    volume_changed = Signal(int)
    mute_changed = Signal(bool)
    seek_requested = Signal(float)
    skip_requested = Signal(int)
    fullscreen_requested = Signal()
    # 👑 存活信号
    user_activity = Signal() 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.is_playing = True 
        self.is_muted = False      
        self.last_seek_time = 0  
        self._drag_pos = None 
        self._user_dragged = False # 记录用户是否手动拖拽过
        self.init_ui()

    def init_ui(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40) 
        shadow.setColor(QColor(0, 0, 0, 180)) 
        shadow.setOffset(0, 15) 
        self.setGraphicsEffect(shadow)

        self.setStyleSheet("""
            /* 👑 核心手术 1：清洗所有子组件，强制全部变透明，斩断黑色的继承 */
            QWidget {
                background-color: transparent;
            }
            
            /* 👑 核心手术 2：给大底板重新刷上绝美的冰晶毛玻璃 */
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
                background-color: transparent; border: none;
                color: rgba(255, 255, 255, 210);
                font-family: -apple-system, "SF Pro Rounded", sans-serif;
                font-weight: 900;
            }
            QPushButton:hover {
                color: rgba(255, 255, 255, 255);
                background-color: rgba(255, 255, 255, 20);
                border-radius: 20px;
            }
            QPushButton#PlayBtn { font-size: 32px; }
            QPushButton#SkipBtn { font-size: 20px; }
            QPushButton#MuteBtn { font-size: 13px; letter-spacing: 1px; }
            QPushButton#UtilBtn { font-size: 20px; }
            
            QLabel {
                background-color: transparent;
                color: rgba(255, 255, 255, 210); font-size: 13px;
                font-weight: 600; font-family: "Courier New", monospace; 
            }
            
            QSlider::groove:horizontal { border-radius: 2px; height: 4px; background: rgba(0, 0, 0, 80); }
            QSlider::sub-page:horizontal { background: white; border-radius: 2px; }
            QSlider::handle:horizontal { width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; background: white; }
            QSlider::handle:horizontal:hover { width: 14px; height: 14px; margin: -5px -1px; border-radius: 7px; }
        """)
        self.setFixedHeight(105) 
        
        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(30, 15, 30, 15)
        main_v_layout.setSpacing(5)

        time_row = QHBoxLayout()
        self.curr_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setObjectName("ProgressBar")
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderMoved.connect(self.on_slider_moved)
        self.progress_slider.sliderReleased.connect(self.on_seek)
        
        time_row.addWidget(self.curr_time_label)
        time_row.addWidget(self.progress_slider)
        time_row.addWidget(self.total_time_label)
        main_v_layout.addLayout(time_row)

        btns_row = QHBoxLayout()
        self.vol_group = QWidget()
        self.vol_group.setFixedWidth(150)
        vol_layout = QHBoxLayout(self.vol_group)
        vol_layout.setContentsMargins(0, 0, 0, 0)
        self.mute_btn = QPushButton("VOL")
        self.mute_btn.setObjectName("MuteBtn")
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(100)
        self.vol_slider.valueChanged.connect(self.volume_changed.emit)
        vol_layout.addWidget(self.mute_btn)
        vol_layout.addWidget(self.vol_slider)
        
        self.center_btns = QWidget()
        center_layout = QHBoxLayout(self.center_btns)
        center_layout.setSpacing(10)
        self.rewind_btn = QPushButton("◀◀")
        self.rewind_btn.setObjectName("SkipBtn")
        self.rewind_btn.setFixedSize(45, 45)
        self.play_btn = QPushButton("▶")
        self.play_btn.setObjectName("PlayBtn")
        self.play_btn.setFixedSize(55, 55) 
        self.forward_btn = QPushButton("▶▶")
        self.forward_btn.setObjectName("SkipBtn")
        self.forward_btn.setFixedSize(45, 45)
        center_layout.addWidget(self.rewind_btn)
        center_layout.addWidget(self.play_btn)
        center_layout.addWidget(self.forward_btn)
        
        self.right_utils = QWidget()
        self.right_utils.setFixedWidth(150)
        util_layout = QHBoxLayout(self.right_utils)
        util_layout.setAlignment(Qt.AlignRight)
        self.settings_btn = QPushButton("•••")
        self.settings_btn.setObjectName("UtilBtn")
        self.fullscreen_btn = QPushButton("⛶")
        self.fullscreen_btn.setObjectName("UtilBtn")
        util_layout.addWidget(self.settings_btn)
        util_layout.addWidget(self.fullscreen_btn)

        btns_row.addWidget(self.vol_group)
        btns_row.addStretch()
        btns_row.addWidget(self.center_btns)
        btns_row.addStretch()
        btns_row.addWidget(self.right_utils)
        main_v_layout.addLayout(btns_row)

        self.rewind_btn.clicked.connect(lambda: self.skip_requested.emit(-10))
        self.forward_btn.clicked.connect(lambda: self.skip_requested.emit(10))
        self.play_btn.clicked.connect(self.toggle_play_ui)
        self.mute_btn.clicked.connect(self.toggle_mute_ui)
        self.fullscreen_btn.clicked.connect(self.fullscreen_requested.emit)

    def toggle_play_ui(self):
        self.is_playing = not self.is_playing
        self.play_btn.setText("▶" if not self.is_playing else "❙❙") 
        self.play_state_changed.emit(self.is_playing)

    def toggle_mute_ui(self):
        self.is_muted = not self.is_muted
        self.mute_btn.setText("MUT" if self.is_muted else "VOL")
        self.mute_btn.setStyleSheet("color: #ff5555;" if self.is_muted else "")
        self.mute_changed.emit(self.is_muted)

    def on_slider_moved(self, value):
        self.user_activity.emit() 
        curr = time.time()
        if curr - self.last_seek_time > 0.15:
            self.seek_requested.emit(value / 1000.0)
            self.last_seek_time = curr

    def on_seek(self):
        self.seek_requested.emit(self.progress_slider.value() / 1000.0)

    def format_time(self, s):
        s = int(s)
        return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}" if s >= 3600 else f"{(s%3600)//60:02d}:{s%60:02d}"

    def update_progress(self, current, total):
        if total > 0:
            self.curr_time_label.setText(self.format_time(current))
            self.total_time_label.setText(self.format_time(total))
            if not self.progress_slider.isSliderDown():
                self.progress_slider.setValue(int((current / total) * 1000))

    # ==========================================
    # 👑 物理拖拽引擎
    # ==========================================
    def enterEvent(self, event):
        self.user_activity.emit() 
        super().enterEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._user_dragged = True # 标记已经被拖动，不再自动居中
            self.user_activity.emit()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.user_activity.emit() 
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            new_pos = self.pos() + delta
            # 防止面板被拖出主窗口
            if self.parentWidget():
                parent_rect = self.parentWidget().rect()
                new_x = max(0, min(new_pos.x(), parent_rect.width() - self.width()))
                new_y = max(0, min(new_pos.y(), parent_rect.height() - self.height()))
                new_pos = QPoint(new_x, new_y)
            self.move(new_pos)
            self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)