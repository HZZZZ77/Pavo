import os
import sys
import bootstrap
bootstrap.setup_pavo_env()

from PySide6.QtWidgets import (QApplication, QMainWindow, QGridLayout, QWidget, 
                             QGraphicsOpacityEffect, QMenu, QLabel, QVBoxLayout,
                             QGraphicsDropShadowEffect)
# 👑 新增：引入 QPainter 和 QPainterPath 用于精美绘制圆角图片，QColor 用于绘制高级阴影
from PySide6.QtGui import QSurfaceFormat, QAction, QKeyEvent, QPixmap, QPainter, QPainterPath, QColor
from PySide6.QtCore import Qt, QTimer, QEvent, QPropertyAnimation, QEasingCurve, QPoint, QUrl

from engine import PavoEngine
from video_widget import PavoVideoWidget
from components.hud_panel import HUDPanel

class PavoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pavo") 
        self.resize(1000, 600)
        self.setStyleSheet("background-color: black;")
        self.setAcceptDrops(True)

        self.engine = PavoEngine()
        self.engine.thumbnail_ready.connect(self._on_thumbnail_ready)
        
        self.hud_timer = QTimer(self)
        self.hud_timer.setInterval(2000)
        self.hud_timer.timeout.connect(self.hide_hud)
        
        self._is_pip = False
        self._normal_geometry = None

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

        self.hud = HUDPanel(self.central_widget)
        self.hud.raise_()

        # ==========================================
        # 👑 焕然一新的高颜值悬浮缩略图弹窗
        # ==========================================
        self.thumb_popup = QWidget(self.central_widget)
        self.thumb_popup.setFixedSize(176, 128) # 略微放大，容纳更精美的排版
        
        # 1. 增加极具质感的柔和外发光阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.thumb_popup.setGraphicsEffect(shadow)

        # 2. 调优 macOS 风格的深邃半透明背景色
        self.thumb_popup.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 32, 240);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 12px;
            }
            QLabel { background-color: transparent; border: none; }
        """)
        popup_layout = QVBoxLayout(self.thumb_popup)
        popup_layout.setContentsMargins(8, 8, 8, 4) # 顶部和两侧留白多一点，底部稍紧凑
        popup_layout.setSpacing(4)

        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(158, 89) # 精确的 16:9 比例
        self.thumb_label.setStyleSheet("background-color: rgba(0, 0, 0, 100); border-radius: 6px;")
        self.thumb_label.setAlignment(Qt.AlignCenter)

        self.thumb_time_label = QLabel("00:00")
        self.thumb_time_label.setAlignment(Qt.AlignCenter)
        # 3. 换用干净的无衬线字体和加粗数字，更具现代感
        self.thumb_time_label.setStyleSheet("""
            color: rgba(255, 255, 255, 230); 
            font-size: 13px; 
            font-weight: 600; 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        """)

        popup_layout.addWidget(self.thumb_label)
        popup_layout.addWidget(self.thumb_time_label)
        self.thumb_popup.hide()

        # 200ms 防抖计时器
        self.thumb_timer = QTimer(self)
        self.thumb_timer.setSingleShot(True)
        self.thumb_timer.setInterval(200) 
        self.thumb_timer.timeout.connect(self._request_thumbnail)
        self._current_hover_time = 0

        self.top_osd = QLabel(self.central_widget)
        self.top_osd.setAlignment(Qt.AlignCenter)
        self.top_osd.setText("✨ 请将视频文件拖拽至此播放")
        self.top_osd.setStyleSheet("""
            QLabel {
                background-color: rgba(40, 40, 40, 180);
                color: rgba(255, 255, 255, 230);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 12px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
        """)
        self.top_osd.adjustSize()
        self.top_osd.raise_()

        self.opacity_effect = QGraphicsOpacityEffect(self.hud)
        self.opacity_effect.setOpacity(1.0)
        self.hud.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(250)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.finished.connect(self._on_fade_finished)

        self.osd_opacity_effect = QGraphicsOpacityEffect(self.top_osd)
        self.osd_opacity_effect.setOpacity(1.0)
        self.top_osd.setGraphicsEffect(self.osd_opacity_effect)
        self.osd_fade_anim = QPropertyAnimation(self.osd_opacity_effect, b"opacity")
        self.osd_fade_anim.setDuration(250)
        self.osd_fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.osd_fade_anim.setEndValue(1.0)

        # 连线
        self.hud.play_state_changed.connect(self.engine.set_playing)
        self.hud.volume_changed.connect(self.engine.set_volume)
        self.hud.mute_changed.connect(self.engine.set_mute)
        self.hud.seek_requested.connect(self.engine.seek_to_percent)
        self.hud.skip_requested.connect(self.on_skip)
        self.hud.fullscreen_requested.connect(self.toggle_fullscreen)
        
        self.hud.progress_slider.hover_entered.connect(self.thumb_popup.show)
        self.hud.progress_slider.hover_left.connect(self.thumb_popup.hide)
        self.hud.progress_slider.hover_moved.connect(self._on_hover_moved)
        
        if hasattr(self.hud, 'settings_btn'):
            self.hud.settings_btn.clicked.connect(self.show_settings_menu)
        if hasattr(self.hud, 'subtitle_btn'):
            self.hud.subtitle_requested.connect(self.show_subtitle_menu)
        if hasattr(self.hud, 'pip_btn'):
            self.hud.pip_requested.connect(self.toggle_pip)

        if hasattr(self.hud, 'user_activity'):
            self.hud.user_activity.connect(self.wake_hud)

        if hasattr(self.video_canvas, 'clicked'):
            self.video_canvas.clicked.connect(self.hud.toggle_play_ui)
        if hasattr(self.video_canvas, 'double_clicked'):
            self.video_canvas.double_clicked.connect(self.toggle_fullscreen)
        if hasattr(self.video_canvas, 'file_dropped'):
            self.video_canvas.file_dropped.connect(self.handle_dropped_file)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sync_progress)
        self.timer.start(500)

    # ==========================================
    # 缩略图逻辑驱动区
    # ==========================================
    def _on_hover_moved(self, time_sec, local_x):
        self._current_hover_time = time_sec
        
        s = int(time_sec)
        time_str = f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}" if s >= 3600 else f"{(s%3600)//60:02d}:{s%60:02d}"
        self.thumb_time_label.setText(time_str)

        slider = self.hud.progress_slider
        slider_global = slider.mapToGlobal(QPoint(local_x, 0))
        local_pos = self.central_widget.mapFromGlobal(slider_global)
        
        px = local_pos.x() - self.thumb_popup.width() // 2
        px = max(10, min(px, self.width() - self.thumb_popup.width() - 10))
        # 抬高一点，给阴影留出空间
        py = self.hud.y() - self.thumb_popup.height() - 20
        
        self.thumb_popup.move(px, py)
        self.thumb_timer.start()

    def _request_thumbnail(self):
        self.engine.get_thumbnail(self._current_hover_time)

    def _on_thumbnail_ready(self, time_key, img_bytes):
        if abs(time_key - int(self._current_hover_time)) <= 2:
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes)
            
            # 👑 4. 魔法：给视频原图“动手术”，切割出圆角
            target_size = self.thumb_label.size()
            scaled_pixmap = pixmap.scaled(target_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            
            # 创建一个透明的空画板
            rounded_pixmap = QPixmap(target_size)
            rounded_pixmap.fill(Qt.transparent)
            
            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 定义一个带圆角的切割路径 (6像素内圆角)
            path = QPainterPath()
            path.addRoundedRect(0, 0, target_size.width(), target_size.height(), 6, 6)
            painter.setClipPath(path)
            
            # 把图片画入切割路径中，自动去掉直角边
            x_offset = (target_size.width() - scaled_pixmap.width()) // 2
            y_offset = (target_size.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
            painter.end()
            
            self.thumb_label.setPixmap(rounded_pixmap)

    def toggle_pip(self):
        if not self._is_pip:
            self._normal_geometry = self.geometry()
            self._is_pip = True
            
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.showNormal() 
            self.resize(480, 270) 
            self.show()
            
            if hasattr(self.hud, 'set_pip_mode'):
                self.hud.set_pip_mode(True)
            
            self.top_osd.setText("🚀 已进入画中画模式")
            self.top_osd.adjustSize()
            self.resizeEvent(None)
            self.wake_hud()
        else:
            self._is_pip = False
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            if self._normal_geometry:
                self.setGeometry(self._normal_geometry)
            self.show()
            
            if hasattr(self.hud, 'set_pip_mode'):
                self.hud.set_pip_mode(False)
                
            if hasattr(self.hud, '_user_dragged'):
                self.hud._user_dragged = False
                
            self.top_osd.setText("🔙 已恢复正常模式")
            self.top_osd.adjustSize()
            self.resizeEvent(None)
            self.wake_hud()

    def handle_dropped_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.srt', '.ass', '.vtt', '.ssa']:
            self.engine.add_external_subtitle(file_path)
            self.top_osd.setText(f"💬 字幕已加载：{os.path.basename(file_path)}")
            self.top_osd.adjustSize()
            self.resizeEvent(None)
            self.wake_hud()
        else:
            self.load_local_video(file_path)

    def load_local_video(self, file_path):
        filename = os.path.basename(file_path)
        self.top_osd.setText(f"🎬 正在播放：{filename}")
        self.top_osd.adjustSize()
        self.resizeEvent(None) 
        self.wake_hud()
        self.engine.play(file_path)
        if hasattr(self.hud, 'is_playing'):
            self.hud.is_playing = True
            self.hud.play_btn.setIcon(self.hud.icons['pause'])

    def on_skip(self, seconds):
        curr, total = self.engine.get_progress()
        if total <= 0: return
        new_time = max(0, min(total, curr + seconds))
        self.engine.seek_to_percent(new_time / total)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
        self.resizeEvent(None)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
        elif event.key() == Qt.Key_Space:
            self.hud.toggle_play_ui()
        super().keyPressEvent(event)

    def show_subtitle_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(45, 45, 45, 240);
                color: white;
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 30px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #007AFF;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 30);
                margin: 4px 10px;
            }
        """)
        
        sub_tracks = self.engine.get_subtitle_tracks()
        
        action_disable = QAction("🚫 关闭字幕", self)
        action_disable.setCheckable(True)
        has_selected_sub = any(t['selected'] for t in sub_tracks)
        if not has_selected_sub: action_disable.setChecked(True)
        action_disable.triggered.connect(lambda: self.engine.set_subtitle_track('no'))
        menu.addAction(action_disable)
        menu.addSeparator()

        for t in sub_tracks:
            action = QAction(t['name'], self)
            action.setCheckable(True)
            if t['selected']: action.setChecked(True)
            action.triggered.connect(lambda checked, val=t['id']: self.engine.set_subtitle_track(val))
            menu.addAction(action)

        btn_pos = self.hud.subtitle_btn.mapToGlobal(QPoint(0, 0))
        menu.exec(btn_pos - QPoint(0, menu.sizeHint().height() + 10))

    def show_settings_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(45, 45, 45, 240);
                color: white;
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 30px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #007AFF;
            }
        """)

        speed_menu = menu.addMenu("⏩ 倍速播放")
        speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        current_speed = getattr(self.engine, 'playback_speed', 1.0)
        for s in speeds:
            action = QAction(f"{s}x", self)
            action.setCheckable(True)
            if s == current_speed: action.setChecked(True)
            action.triggered.connect(lambda checked, val=s: self.change_speed(val))
            speed_menu.addAction(action)

        aspect_menu = menu.addMenu("📺 画面比例")
        aspects = ["Auto", "16:9", "4:3", "21:9", "9:16", "1:1"]
        current_aspect = getattr(self.engine, 'current_aspect', 'Auto')
        for r in aspects:
            action = QAction(r, self)
            action.setCheckable(True)
            if r == current_aspect: action.setChecked(True)
            action.triggered.connect(lambda checked, val=r: self.change_aspect_ratio(val))
            aspect_menu.addAction(action)

        audio_tracks = self.engine.get_audio_tracks()
        if audio_tracks:
            audio_menu = menu.addMenu("🎧 切换音轨")
            for t in audio_tracks:
                action = QAction(t['name'], self)
                action.setCheckable(True)
                if t['selected']: action.setChecked(True)
                action.triggered.connect(lambda checked, val=t['id']: self.engine.set_audio_track(val))
                audio_menu.addAction(action)

        btn_pos = self.hud.settings_btn.mapToGlobal(QPoint(0, 0))
        menu.exec(btn_pos - QPoint(0, menu.sizeHint().height() + 10))

    def change_speed(self, speed):
        if hasattr(self.engine, 'set_speed'):
            self.engine.set_speed(speed)
            self.engine.playback_speed = speed 

    def change_aspect_ratio(self, ratio):
        if hasattr(self.engine, 'set_aspect_ratio'):
            self.engine.set_aspect_ratio(ratio)
            ratio_text = "默认" if ratio == "Auto" else ratio
            self.top_osd.setText(f"📺 画面比例已切换为：{ratio_text}")
            self.top_osd.adjustSize()
            self.resizeEvent(None)
            self.wake_hud()

    def resizeEvent(self, event):
        if event: super().resizeEvent(event)
        if hasattr(self, 'top_osd'):
            osd_w = self.top_osd.width()
            osd_x = (self.width() - osd_w) // 2
            self.top_osd.move(osd_x, 30)
        if hasattr(self, 'hud'):
            hud_w = min(600, self.width() - 40)
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
            self.top_osd.show()
            self.fade_anim.stop()
            self.fade_anim.setStartValue(self.opacity_effect.opacity())
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()
            self.osd_fade_anim.stop()
            self.osd_fade_anim.setStartValue(self.osd_opacity_effect.opacity())
            self.osd_fade_anim.setEndValue(1.0)
            self.osd_fade_anim.start()
        if getattr(self.hud, 'is_playing', True):
            self.hud_timer.start()

    def hide_hud(self):
        if not self.hud.isHidden() and getattr(self.hud, 'is_playing', True) and self.fade_anim.endValue() != 0.0:
            self.fade_anim.stop()
            self.fade_anim.setStartValue(self.opacity_effect.opacity())
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()
            self.osd_fade_anim.stop()
            self.osd_fade_anim.setStartValue(self.osd_opacity_effect.opacity())
            self.osd_fade_anim.setEndValue(0.0)
            self.osd_fade_anim.start()

    def _on_fade_finished(self):
        if self.fade_anim.endValue() == 0.0:
            self.hud.hide()
            self.top_osd.hide()

if __name__ == "__main__":
    fmt = QSurfaceFormat()
    fmt.setVersion(4, 1)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    window = PavoPlayer()
    window.show()
    sys.exit(app.exec())