import os
import sys
import json
import bootstrap
bootstrap.setup_pavo_env()

from PySide6.QtWidgets import (QApplication, QMainWindow, QGridLayout, QWidget, 
                             QGraphicsOpacityEffect, QMenu, QLabel, QVBoxLayout,
                             QGraphicsDropShadowEffect, QListWidget, QListWidgetItem,
                             QAbstractItemView)
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
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.setStyleSheet("""
            QMainWindow { background-color: black; }
            QToolTip {
                background-color: rgba(30, 30, 32, 220);
                color: rgba(255, 255, 255, 230);
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 8px;
                padding: 6px 10px;
                font-family: -apple-system, sans-serif;
                font-size: 12px;
            }
        """)
        self.setAcceptDrops(True)

        self.engine = PavoEngine()
        self.engine.thumbnail_ready.connect(self._on_thumbnail_ready)
        self.engine.file_ended.connect(self._on_file_ended)
        self.engine.file_loaded.connect(self._on_file_loaded)
        
        self.hud_timer = QTimer(self)
        self.hud_timer.setInterval(2000)
        self.hud_timer.timeout.connect(self.hide_hud)
        
        self._is_pip = False
        self._normal_geometry = None
        self._playlist_was_visible = False
        
        self.data_file = os.path.join(os.path.expanduser("~"), ".pavo_data.json")
        self.history = {}
        self.playlist = []
        self.current_idx = -1
        self.pending_seek = 0

        self.init_ui()
        self.load_data()

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

        self.thumb_popup = QWidget(self.central_widget)
        self.thumb_popup.setObjectName("thumbPopup")
        self.thumb_popup.setFixedSize(176, 128)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 6)
        self.thumb_popup.setGraphicsEffect(shadow)
        
        self.thumb_popup.setStyleSheet("""
            QWidget#thumbPopup { 
                background-color: rgba(30, 30, 32, 200); 
                border: 1px solid rgba(255, 255, 255, 30); 
                border-radius: 12px; 
            }
        """)
        popup_layout = QVBoxLayout(self.thumb_popup)
        popup_layout.setContentsMargins(8, 8, 8, 4)
        popup_layout.setSpacing(4)
        
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(158, 89)
        self.thumb_label.setStyleSheet("background-color: rgba(10, 10, 10, 180); border-radius: 6px;")
        self.thumb_label.setAlignment(Qt.AlignCenter)
        
        self.thumb_time_label = QLabel("00:00")
        self.thumb_time_label.setAlignment(Qt.AlignCenter)
        self.thumb_time_label.setStyleSheet("color: white; font-size: 13px; font-weight: 600; background: transparent;")
        
        popup_layout.addWidget(self.thumb_label)
        popup_layout.addWidget(self.thumb_time_label)
        self.thumb_popup.hide()

        self.thumb_timer = QTimer(self)
        self.thumb_timer.setSingleShot(True)
        self.thumb_timer.setInterval(200) 
        self.thumb_timer.timeout.connect(self._request_thumbnail)
        self._current_hover_time = 0

        self.top_osd = QLabel(self.central_widget)
        self.top_osd.setAlignment(Qt.AlignCenter)
        self.top_osd.setText("✨ Drop video files here to play")
        self.top_osd.setStyleSheet("""
            QLabel { background-color: rgba(40, 40, 40, 180); color: rgba(255, 255, 255, 230); border: 1px solid rgba(255, 255, 255, 30); border-radius: 12px; padding: 8px 20px; font-size: 14px; font-weight: 500; }
        """)
        self.top_osd.adjustSize()
        self.top_osd.raise_()

        self.playlist_ui = QListWidget(self.central_widget)
        self.playlist_ui.setFixedWidth(260)
        self.playlist_ui.setDragEnabled(True)
        self.playlist_ui.setAcceptDrops(True)
        self.playlist_ui.setDragDropMode(QAbstractItemView.InternalMove)
        self.playlist_ui.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.playlist_ui.setContextMenuPolicy(Qt.CustomContextMenu)
        self.playlist_ui.customContextMenuRequested.connect(self.show_playlist_context_menu)
        self.playlist_ui.model().rowsMoved.connect(self._sync_playlist_order)
        self.playlist_ui.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.playlist_ui.setTextElideMode(Qt.ElideRight)

        self.playlist_ui.setStyleSheet("""
            QListWidget {
                background-color: rgba(25, 25, 25, 210);
                color: rgba(255, 255, 255, 220);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 12px;
                padding: 6px;
                outline: none;
            }
            QListWidget::item { padding: 12px 10px; border-radius: 8px; margin-bottom: 2px; }
            QListWidget::item:selected { background-color: rgba(255, 255, 255, 30); color: white; font-weight: bold; }
            QListWidget::item:hover:!selected { background-color: rgba(255, 255, 255, 10); }
            QScrollBar:vertical { border: none; background: transparent; width: 6px; margin: 4px 0 4px 0; }
            QScrollBar::handle:vertical { background-color: rgba(255, 255, 255, 50); min-height: 30px; border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background-color: rgba(255, 255, 255, 120); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { border: none; background: none; }
            QScrollBar:horizontal { height: 0px; background: transparent; }
        """)
        self.playlist_ui.hide()
        self.playlist_ui.itemDoubleClicked.connect(self._on_playlist_item_clicked)

        self.playlist_ui.raise_()
        self.hud.raise_()
        self.thumb_popup.raise_()
        self.top_osd.raise_()

        self.opacity_effect = QGraphicsOpacityEffect(self.hud)
        self.opacity_effect.setOpacity(1.0)
        self.hud.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(300)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_anim.finished.connect(self._on_fade_finished)

        self.osd_opacity_effect = QGraphicsOpacityEffect(self.top_osd)
        self.top_osd.setGraphicsEffect(self.osd_opacity_effect)
        self.osd_fade_anim = QPropertyAnimation(self.osd_opacity_effect, b"opacity")
        self.osd_fade_anim.setDuration(300)

        self.pl_opacity = QGraphicsOpacityEffect(self.playlist_ui)
        self.playlist_ui.setGraphicsEffect(self.pl_opacity)
        self.pl_fade_anim = QPropertyAnimation(self.pl_opacity, b"opacity")
        self.pl_fade_anim.setDuration(300)
        self.pl_fade_anim.setEasingCurve(QEasingCurve.InOutQuad)

        self.hud.play_state_changed.connect(self.engine.set_playing)
        self.hud.volume_changed.connect(self.engine.set_volume)
        self.hud.mute_changed.connect(self.engine.set_mute)
        self.hud.seek_requested.connect(self.engine.seek_to_percent)
        self.hud.skip_requested.connect(self.on_skip)
        self.hud.fullscreen_requested.connect(self.toggle_fullscreen)
        self.hud.progress_slider.hover_entered.connect(self.thumb_popup.show)
        self.hud.progress_slider.hover_left.connect(self.thumb_popup.hide)
        self.hud.progress_slider.hover_moved.connect(self._on_hover_moved)
        
        if hasattr(self.hud, 'settings_btn'): self.hud.settings_btn.clicked.connect(self.show_settings_menu)
        if hasattr(self.hud, 'subtitle_btn'): 
            if hasattr(self.hud, 'subtitle_requested'): self.hud.subtitle_requested.connect(self.show_subtitle_menu)
            else: self.hud.subtitle_btn.clicked.connect(self.show_subtitle_menu)
        if hasattr(self.hud, 'pip_btn'): self.hud.pip_requested.connect(self.toggle_pip)
        if hasattr(self.hud, 'playlist_btn'): self.hud.playlist_requested.connect(self.toggle_playlist)
        if hasattr(self.hud, 'user_activity'): self.hud.user_activity.connect(self.wake_hud)

        if hasattr(self.video_canvas, 'clicked'): self.video_canvas.clicked.connect(self.hud.toggle_play_ui)
        if hasattr(self.video_canvas, 'double_clicked'): self.video_canvas.double_clicked.connect(self.toggle_fullscreen)
        self.video_canvas.files_dropped.connect(self.handle_dropped_files)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sync_progress)
        self.timer.start(500)

    def _create_styled_menu(self):
        menu = QMenu(self)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(30, 30, 32, 220);
                color: rgba(255, 255, 255, 230);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 12px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 30px 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                margin: 2px 4px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 30);
                color: white;
            }
            QMenu::item:disabled {
                color: rgba(255, 255, 255, 100);
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 20);
                margin: 4px 10px;
            }
            QMenu::indicator { width: 16px; height: 16px; }
        """)
        return menu

    def show_playlist_context_menu(self, pos):
        item = self.playlist_ui.itemAt(pos)
        menu = self._create_styled_menu()
        if item:
            play_act = QAction("▶️ Play Now", self)
            play_act.triggered.connect(lambda: self._on_playlist_item_clicked(item))
            menu.addAction(play_act)
            del_act = QAction("🗑️ Remove from Playlist", self)
            del_act.triggered.connect(self.delete_selected_items)
            menu.addAction(del_act)
        menu.exec(self.playlist_ui.mapToGlobal(pos))

    def delete_selected_items(self):
        items = self.playlist_ui.selectedItems()
        for item in items: self.playlist_ui.takeItem(self.playlist_ui.row(item))
        self._sync_playlist_order()

    def _sync_playlist_order(self, *args):
        new_list = [self.playlist_ui.item(i).toolTip() for i in range(self.playlist_ui.count())]
        self.playlist = new_list
        if self.engine.current_media_path in self.playlist:
            self.current_idx = self.playlist.index(self.engine.current_media_path)
        self.save_data()

    def toggle_playlist(self):
        if self.playlist_ui.isVisible() and self.pl_opacity.opacity() > 0:
            self._playlist_was_visible = False
            self.pl_fade_anim.setEndValue(0.0); self.pl_fade_anim.start()
            QTimer.singleShot(300, self.playlist_ui.hide) 
        else:
            self._playlist_was_visible = True
            self.playlist_ui.show()
            self.pl_fade_anim.setEndValue(1.0); self.pl_fade_anim.start()
            self.playlist_ui.setFocus()
            self.wake_hud()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = data.get("history", {})
                    self.playlist = data.get("playlist", [])
            except: pass
        self.refresh_playlist_ui()

    def save_data(self):
        data = { "playlist": self.playlist, "history": self.history }
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except: pass

    def closeEvent(self, event):
        self.save_data()
        super().closeEvent(event)

    def _on_file_loaded(self):
        if self.pending_seek > 0:
            current, total = self.engine.get_progress()
            if total > 0 and self.pending_seek < total - 5:
                self.engine.seek_to_percent(self.pending_seek / total)
                self.show_osd(f"🕒 Resumed from {self._format_time(self.pending_seek)}")
            self.pending_seek = 0

    def _on_file_ended(self):
        if 0 <= self.current_idx < len(self.playlist) - 1:
            self.current_idx += 1
            self.load_local_video(self.playlist[self.current_idx])

    def handle_dropped_files(self, file_paths):
        if not file_paths: return
        subs = [f for f in file_paths if os.path.splitext(f)[1].lower() in ['.srt', '.ass', '.vtt']]
        videos = [f for f in file_paths if f not in subs]
        
        if subs and not videos:
            self.engine.add_external_subtitle(subs[0])
            self.show_osd(f"💬 Subtitle loaded: {os.path.basename(subs[0])}")
            return

        self.playlist.extend(videos)
        self.playlist = list(dict.fromkeys(self.playlist))
        self.refresh_playlist_ui()
        
        self._playlist_was_visible = True
        self.playlist_ui.show()
        self.pl_fade_anim.setEndValue(1.0); self.pl_fade_anim.start()
        
        if self.current_idx == -1:
            self.current_idx = self.playlist.index(videos[0])
            self.load_local_video(self.playlist[self.current_idx])

    def refresh_playlist_ui(self):
        self.playlist_ui.clear()
        for path in self.playlist:
            item = QListWidgetItem(os.path.basename(path))
            item.setToolTip(path)
            self.playlist_ui.addItem(item)
        self.update_playlist_ui_selection()

    def update_playlist_ui_selection(self):
        if 0 <= self.current_idx < self.playlist_ui.count():
            self.playlist_ui.setCurrentRow(self.current_idx)

    def _on_playlist_item_clicked(self, item):
        idx = self.playlist_ui.row(item)
        self.current_idx = idx
        self.load_local_video(self.playlist[idx])
        self._playlist_was_visible = False
        self.pl_fade_anim.setEndValue(0.0); self.pl_fade_anim.start()
        QTimer.singleShot(300, self.playlist_ui.hide)

    def load_local_video(self, file_path):
        self.show_osd(f"🎬 Now playing: {os.path.basename(file_path)}")
        self.pending_seek = self.history.get(file_path, 0)
        self.engine.play(file_path)
        self.update_playlist_ui_selection()
        if hasattr(self.hud, 'is_playing'):
            self.hud.is_playing = True
            self.hud.play_btn.setIcon(self.hud.icons['pause'])

    def show_osd(self, text):
        self.top_osd.setText(text)
        self.top_osd.adjustSize()
        self.resizeEvent(None)
        self.wake_hud()

    def _format_time(self, s):
        s = int(s)
        return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}" if s >= 3600 else f"{(s%3600)//60:02d}:{s%60:02d}"

    def sync_progress(self):
        current, total = self.engine.get_progress()
        self.hud.update_progress(current, total)
        if total > 0 and self.engine.current_media_path:
            self.history[self.engine.current_media_path] = current

    def _on_hover_moved(self, time_sec, local_x):
        self._current_hover_time = time_sec
        self.thumb_time_label.setText(self._format_time(time_sec))
        slider = self.hud.progress_slider
        slider_global = slider.mapToGlobal(QPoint(local_x, 0))
        local_pos = self.central_widget.mapFromGlobal(slider_global)
        px = max(10, min(local_pos.x() - self.thumb_popup.width() // 2, self.width() - self.thumb_popup.width() - 10))
        self.thumb_popup.move(px, self.hud.y() - self.thumb_popup.height() - 20)
        self.thumb_timer.start()

    def _request_thumbnail(self):
        self.engine.get_thumbnail(self._current_hover_time)

    def _on_thumbnail_ready(self, time_key, img_bytes):
        if abs(time_key - int(self._current_hover_time)) <= 2:
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes)
            self.thumb_label.setPixmap(pixmap.scaled(self.thumb_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key_Space:
            self.hud.toggle_play_ui()
        elif key == Qt.Key_Right:
            self.on_skip(10)
            self.show_osd("⏩ Forward 10s")
        elif key == Qt.Key_Left:
            self.on_skip(-10)
            self.show_osd("⏪ Rewind 10s")
        elif key == Qt.Key_Up:
            new_vol = min(100, self.hud.volume_slider.value() + 5)
            self.hud.volume_slider.setValue(new_vol)
            self.show_osd(f"🔊 Volume: {new_vol}%")
        elif key == Qt.Key_Down:
            new_vol = max(0, self.hud.volume_slider.value() - 5)
            self.hud.volume_slider.setValue(new_vol)
            self.show_osd(f"🔉 Volume: {new_vol}%")
        elif key in [Qt.Key_Delete, Qt.Key_Backspace]:
            if self.playlist_ui.hasFocus():
                self.delete_selected_items()
        elif key == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
        super().keyPressEvent(event)

    def on_skip(self, seconds):
        curr, total = self.engine.get_progress()
        if total <= 0: return
        self.engine.seek_to_percent(max(0, min(total, curr + seconds)) / total)

    def toggle_fullscreen(self):
        if self.isFullScreen(): self.showNormal()
        else: self.showFullScreen()
        self.resizeEvent(None)

    def toggle_pip(self):
        if not self._is_pip:
            self._normal_geometry = self.geometry()
            self._is_pip = True
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.showNormal()
            self.resize(480, 270)
        else:
            self._is_pip = False
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            if self._normal_geometry: self.setGeometry(self._normal_geometry)
        self.show()

    def show_subtitle_menu(self):
        menu = self._create_styled_menu()
        subs = self.engine.get_subtitle_tracks()
        if not subs:
            act = QAction("🚫 No subtitles available", self)
            act.setEnabled(False)
            menu.addAction(act)
        else:
            for t in subs:
                act = QAction(t['name'], self)
                act.setCheckable(True)
                act.setChecked(t['selected'])
                act.triggered.connect(lambda checked, val=t['id']: self.engine.set_subtitle_track(val))
                menu.addAction(act)
                
        btn_pos = self.hud.subtitle_btn.mapToGlobal(QPoint(0, 0))
        menu.exec(btn_pos - QPoint(0, menu.sizeHint().height() + 10))

    def show_settings_menu(self):
        menu = self._create_styled_menu()
        
        speed_menu = menu.addMenu("⏩ Playback Speed")
        speed_menu.setAttribute(Qt.WA_TranslucentBackground)
        speed_menu.setStyleSheet(menu.styleSheet())
        for s in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0]:
            act = QAction(f"{s}x", self)
            act.setCheckable(True)
            act.setChecked(getattr(self.engine, 'playback_speed', 1.0) == s)
            act.triggered.connect(lambda checked, val=s: self.engine.set_speed(val))
            speed_menu.addAction(act)
            
        aspect_menu = menu.addMenu("📺 Aspect Ratio")
        aspect_menu.setAttribute(Qt.WA_TranslucentBackground)
        aspect_menu.setStyleSheet(menu.styleSheet())
        for ratio in ["Auto", "16:9", "16:10", "4:3", "21:9", "2.35:1", "1:1"]:
            act = QAction(ratio, self)
            act.setCheckable(True)
            act.setChecked(getattr(self.engine, 'current_aspect', 'Auto') == ratio)
            act.triggered.connect(lambda checked, r=ratio: self.engine.set_aspect_ratio(r))
            aspect_menu.addAction(act)
            
        audio_menu = menu.addMenu("🎵 Audio Track")
        audio_menu.setAttribute(Qt.WA_TranslucentBackground)
        audio_menu.setStyleSheet(menu.styleSheet())
        tracks = self.engine.get_audio_tracks()
        if not tracks:
            act = QAction("🚫 No audio tracks available", self)
            act.setEnabled(False)
            audio_menu.addAction(act)
        else:
            for t in tracks:
                act = QAction(t['name'], self)
                act.setCheckable(True)
                act.setChecked(t['selected'])
                act.triggered.connect(lambda checked, tid=t['id']: self.engine.set_audio_track(tid))
                audio_menu.addAction(act)
                
        btn_pos = self.hud.settings_btn.mapToGlobal(QPoint(0, 0))
        menu.exec(btn_pos - QPoint(0, menu.sizeHint().height() + 10))

    def resizeEvent(self, event):
        if hasattr(self, 'top_osd'):
            self.top_osd.move((self.width() - self.top_osd.width()) // 2, 30)
        if hasattr(self, 'playlist_ui'):
            self.playlist_ui.move(self.width() - self.playlist_ui.width() - 20, 20)
            self.playlist_ui.setFixedHeight(max(100, self.height() - 140))
        if hasattr(self, 'hud'):
            hud_w = min(640, self.width() - 40)
            self.hud.setFixedWidth(hud_w)
            if not getattr(self.hud, '_user_dragged', False):
                self.hud.move((self.width() - hud_w) // 2, self.height() - self.hud.height() - 40)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove: self.wake_hud()
        return super().eventFilter(obj, event)

    def leaveEvent(self, event):
        self.hud_timer.stop()
        self.hide_hud()
        super().leaveEvent(event)

    def wake_hud(self):
        if self.opacity_effect.opacity() < 1.0:
            self.hud.show(); self.top_osd.show()
            self.fade_anim.setEndValue(1.0); self.fade_anim.start()
            self.osd_fade_anim.setEndValue(1.0); self.osd_fade_anim.start()
            if getattr(self, '_playlist_was_visible', False):
                self.playlist_ui.show()
                self.pl_fade_anim.setEndValue(1.0); self.pl_fade_anim.start()
        if getattr(self.hud, 'is_playing', True): self.hud_timer.start()

    def hide_hud(self):
        if not self.hud.isHidden() and getattr(self.hud, 'is_playing', True):
            self.fade_anim.setEndValue(0.0); self.fade_anim.start()
            self.osd_fade_anim.setEndValue(0.0); self.osd_fade_anim.start()
            if self.playlist_ui.isVisible():
                self.pl_fade_anim.setEndValue(0.0); self.pl_fade_anim.start()

    def _on_fade_finished(self):
        if self.fade_anim.endValue() == 0.0: 
            self.hud.hide(); self.top_osd.hide()
            if self.playlist_ui.isVisible() and self.pl_opacity.opacity() == 0.0:
                self.playlist_ui.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PavoPlayer()
    window.show()
    sys.exit(app.exec())