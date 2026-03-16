import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QGraphicsDropShadowEffect, QLabel
from PySide6.QtCore import Qt, Signal, QPoint, QByteArray, QSize
from PySide6.QtGui import QColor, QPixmap, QPainter, QIcon

try:
    from PySide6.QtSvg import QSvgRenderer
    HAS_SVG = True
except ImportError:
    HAS_SVG = False

SVG_PLAY = '<svg viewBox="0 0 24 24" fill="white"><path d="M8 5v14l11-7z"/></svg>'
SVG_PAUSE = '<svg viewBox="0 0 24 24" fill="white"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>'
SVG_REWIND = '<svg viewBox="0 0 24 24" fill="white"><path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"/></svg>'
SVG_FORWARD = '<svg viewBox="0 0 24 24" fill="white"><path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6L13 6z"/></svg>'
SVG_VOL = '<svg viewBox="0 0 24 24" fill="white"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>'
SVG_MUTE = '<svg viewBox="0 0 24 24" fill="#ff5555"><path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/></svg>'
SVG_FULLSCREEN = '<svg viewBox="0 0 24 24" fill="white"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>'
SVG_SETTINGS = '<svg viewBox="0 0 24 24" fill="white"><path d="M6 10c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm12 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm-6 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/></svg>'
SVG_CC = '<svg viewBox="0 0 24 24" fill="white"><path d="M19 4H5c-1.11 0-2 .9-2 2v12c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-8 7H9.5v-.5h-2v3h2V13H11v1c0 .55-.45 1-1 1H7c-.55 0-1-.45-1-1v-4c0-.55.45-1 1-1h3c.55 0 1 .45 1 1v1zm7 0h-1.5v-.5h-2v3h2V13H18v1c0 .55-.45 1-1 1h-3c-.55 0-1-.45-1-1v-4c0-.55.45-1 1-1h3c.55 0 1 .45 1 1v1z"/></svg>'
SVG_PIP = '<svg viewBox="0 0 24 24" fill="white"><path d="M19 7h-8v6h8V7zm2-4H3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16.01H3V4.98h18v14.03z"/></svg>'

# ==========================================
# 👑 具有极客感知的悬停进度条
# ==========================================
class HoverSlider(QSlider):
    hover_moved = Signal(float, int) 
    hover_entered = Signal()
    hover_left = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.total_time = 0

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        # 实时换算：把鼠标的 X 坐标转化为视频的具体秒数发射出去！
        if self.total_time > 0:
            val = event.position().x() / self.width()
            val = max(0.0, min(1.0, val))
            time_sec = val * self.total_time
            self.hover_moved.emit(time_sec, int(event.position().x()))

    def enterEvent(self, event):
        super().enterEvent(event)
        self.hover_entered.emit()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.hover_left.emit()

class HUDPanel(QWidget):
    play_state_changed = Signal(bool)
    volume_changed = Signal(int)
    mute_changed = Signal(bool)
    seek_requested = Signal(float)
    skip_requested = Signal(int)
    fullscreen_requested = Signal()
    subtitle_requested = Signal() 
    pip_requested = Signal()      
    user_activity = Signal() 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.is_playing = True 
        self.is_muted = False      
        self.last_seek_time = 0  
        self._drag_pos = None 
        self._user_dragged = False 
        self.icons = {}
        self._preload_icons()
        self.init_ui()

    def _create_svg_icon(self, svg_string, size=64):
        if not HAS_SVG: return QIcon()
        renderer = QSvgRenderer(QByteArray(svg_string.encode('utf-8')))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)

    def _preload_icons(self):
        self.icons['play'] = self._create_svg_icon(SVG_PLAY)
        self.icons['pause'] = self._create_svg_icon(SVG_PAUSE)
        self.icons['rewind'] = self._create_svg_icon(SVG_REWIND)
        self.icons['forward'] = self._create_svg_icon(SVG_FORWARD)
        self.icons['vol'] = self._create_svg_icon(SVG_VOL)
        self.icons['mute'] = self._create_svg_icon(SVG_MUTE)
        self.icons['fullscreen'] = self._create_svg_icon(SVG_FULLSCREEN)
        self.icons['settings'] = self._create_svg_icon(SVG_SETTINGS)
        self.icons['cc'] = self._create_svg_icon(SVG_CC)   
        self.icons['pip'] = self._create_svg_icon(SVG_PIP) 

    def init_ui(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40) 
        shadow.setColor(QColor(0, 0, 0, 90)) 
        shadow.setOffset(0, 8) 
        self.setGraphicsEffect(shadow)

        self.setStyleSheet("""
            QWidget { background-color: transparent; }
            HUDPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 rgba(255, 255, 255, 30),
                                            stop:0.5 rgba(200, 200, 200, 15),
                                            stop:1 rgba(150, 150, 150, 25));
                border-top: 1px solid rgba(255, 255, 255, 160);
                border-left: 1px solid rgba(255, 255, 255, 90);
                border-right: 1px solid rgba(255, 255, 255, 90);
                border-bottom: 1px solid rgba(255, 255, 255, 30);
                border-radius: 20px;
            }
            QPushButton { background-color: transparent; border: none; border-radius: 8px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 30); }
            QLabel {
                color: rgba(255, 255, 255, 210); font-size: 13px; font-weight: 500; 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, sans-serif; 
                font-variant-numeric: tabular-nums;
            }
            QSlider { background: transparent; }
            QSlider#ProgressBar::groove:horizontal { border: none; height: 3px; border-radius: 2px; background: rgba(255, 255, 255, 40); }
            QSlider#ProgressBar::sub-page:horizontal { background: rgba(255, 255, 255, 200); border-radius: 2px; }
            QSlider#ProgressBar::add-page:horizontal { background: transparent; }
            QSlider#ProgressBar::handle:horizontal { width: 3px; height: 12px; margin: -4px 0px; background: white; border-radius: 1px; }
            QSlider#ProgressBar:hover::groove:horizontal { height: 5px; border-radius: 3px;}
            QSlider#ProgressBar:hover::handle:horizontal { height: 14px; margin: -4px 0px;}
            QSlider#VolumeBar::groove:horizontal { border: none; height: 4px; border-radius: 2px; background: rgba(255, 255, 255, 40); }
            QSlider#VolumeBar::sub-page:horizontal { background: #007AFF; border-radius: 2px; }
            QSlider#VolumeBar::add-page:horizontal { background: transparent; }
            QSlider#VolumeBar::handle:horizontal { width: 12px; height: 12px; margin: -4px 0px; border-radius: 6px; background: white; }
        """)
        
        self.setFixedHeight(100) 
        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(25, 15, 25, 15)
        main_v_layout.setSpacing(8)

        btns_row = QHBoxLayout()
        btns_row.setContentsMargins(0, 0, 0, 0)
        
        self.vol_group = QWidget()
        self.vol_group.setFixedWidth(160)
        vol_layout = QHBoxLayout(self.vol_group)
        vol_layout.setContentsMargins(0, 0, 0, 0)
        
        self.mute_btn = QPushButton()
        self.mute_btn.setIcon(self.icons['vol'])
        self.mute_btn.setIconSize(QSize(20, 20))
        self.mute_btn.setFixedSize(30, 30)
        
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setObjectName("VolumeBar")
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(100)
        self.vol_slider.setFixedHeight(16) 
        self.vol_slider.valueChanged.connect(self.volume_changed.emit)
        
        vol_layout.addWidget(self.mute_btn)
        vol_layout.addWidget(self.vol_slider)
        
        self.center_btns = QWidget()
        center_layout = QHBoxLayout(self.center_btns)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(15) 
        
        self.rewind_btn = QPushButton()
        self.rewind_btn.setIcon(self.icons['rewind'])
        self.rewind_btn.setIconSize(QSize(24, 24))
        self.rewind_btn.setFixedSize(36, 36)
        
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.icons['pause']) 
        self.play_btn.setIconSize(QSize(32, 32))
        self.play_btn.setFixedSize(44, 44) 
        
        self.forward_btn = QPushButton()
        self.forward_btn.setIcon(self.icons['forward'])
        self.forward_btn.setIconSize(QSize(24, 24))
        self.forward_btn.setFixedSize(36, 36)
        
        center_layout.addWidget(self.rewind_btn)
        center_layout.addWidget(self.play_btn)
        center_layout.addWidget(self.forward_btn)
        
        self.right_utils = QWidget()
        self.right_utils.setFixedWidth(160) 
        util_layout = QHBoxLayout(self.right_utils)
        util_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        util_layout.setContentsMargins(0, 0, 0, 0)
        util_layout.setSpacing(10)
        
        self.subtitle_btn = QPushButton()
        self.subtitle_btn.setIcon(self.icons['cc'])
        self.subtitle_btn.setIconSize(QSize(20, 20))
        self.subtitle_btn.setFixedSize(30, 30)
        
        self.pip_btn = QPushButton()
        self.pip_btn.setIcon(self.icons['pip'])
        self.pip_btn.setIconSize(QSize(20, 20))
        self.pip_btn.setFixedSize(30, 30)

        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(self.icons['settings'])
        self.settings_btn.setIconSize(QSize(20, 20))
        self.settings_btn.setFixedSize(30, 30)
        
        self.fullscreen_btn = QPushButton()
        self.fullscreen_btn.setIcon(self.icons['fullscreen'])
        self.fullscreen_btn.setIconSize(QSize(20, 20))
        self.fullscreen_btn.setFixedSize(30, 30)
        
        util_layout.addWidget(self.subtitle_btn)
        util_layout.addWidget(self.pip_btn)
        util_layout.addWidget(self.settings_btn)
        util_layout.addWidget(self.fullscreen_btn)

        btns_row.addWidget(self.vol_group)
        btns_row.addStretch()
        btns_row.addWidget(self.center_btns)
        btns_row.addStretch()
        btns_row.addWidget(self.right_utils)
        
        time_row = QHBoxLayout()
        time_row.setContentsMargins(0, 0, 0, 0)
        time_row.setSpacing(10)
        
        self.curr_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")
        self.curr_time_label.setFixedWidth(42)
        self.curr_time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.total_time_label.setFixedWidth(42)
        self.total_time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 👑 替换为我们写的高级 HoverSlider
        self.progress_slider = HoverSlider(Qt.Horizontal)
        self.progress_slider.setObjectName("ProgressBar")
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setFixedHeight(16)
        self.progress_slider.sliderMoved.connect(self.on_slider_moved)
        self.progress_slider.sliderReleased.connect(self.on_seek)
        
        time_row.addWidget(self.curr_time_label)
        time_row.addWidget(self.progress_slider)
        time_row.addWidget(self.total_time_label)
        
        main_v_layout.addLayout(btns_row)
        main_v_layout.addLayout(time_row)

        self.rewind_btn.clicked.connect(lambda: self.skip_requested.emit(-10))
        self.forward_btn.clicked.connect(lambda: self.skip_requested.emit(10))
        self.play_btn.clicked.connect(self.toggle_play_ui)
        self.mute_btn.clicked.connect(self.toggle_mute_ui)
        self.fullscreen_btn.clicked.connect(self.fullscreen_requested.emit)
        
        self.subtitle_btn.clicked.connect(self.subtitle_requested.emit)
        self.pip_btn.clicked.connect(self.pip_requested.emit)

    def toggle_play_ui(self):
        self.is_playing = not self.is_playing
        self.play_btn.setIcon(self.icons['pause'] if self.is_playing else self.icons['play'])
        self.play_state_changed.emit(self.is_playing)

    def toggle_mute_ui(self):
        self.is_muted = not self.is_muted
        self.mute_btn.setIcon(self.icons['mute'] if self.is_muted else self.icons['vol'])
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
            # 传递总时长给 HoverSlider 用于计算
            self.progress_slider.total_time = total
            self.curr_time_label.setText(self.format_time(current))
            self.total_time_label.setText(self.format_time(total))
            if not self.progress_slider.isSliderDown():
                self.progress_slider.setValue(int((current / total) * 1000))

    def enterEvent(self, event):
        self.user_activity.emit() 
        super().enterEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._user_dragged = True 
            self.user_activity.emit()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.user_activity.emit() 
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            new_pos = self.pos() + delta
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

    def set_pip_mode(self, is_pip):
        self.vol_slider.setVisible(not is_pip)
        self.subtitle_btn.setVisible(not is_pip)
        self.settings_btn.setVisible(not is_pip)
        self.fullscreen_btn.setVisible(not is_pip)
        
        if is_pip:
            self.vol_group.setFixedWidth(40)
            self.right_utils.setFixedWidth(40)
            self.setFixedHeight(85)
        else:
            self.vol_group.setFixedWidth(160)
            self.right_utils.setFixedWidth(160)
            self.setFixedHeight(100)