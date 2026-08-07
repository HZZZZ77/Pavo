import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import QApplication, QWidget

import main as pavo_main


class FakeEngine(QObject):
    thumbnail_ready = Signal(str, int, int, bytes)
    file_ended = Signal()
    file_loaded = Signal()
    error_occurred = Signal(str)
    play_state_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.current_media_path = None
        self.thumbnail_generation_id = 0
        self.init_error = None
        self.player = SimpleNamespace(
            pause=False,
            dwidth=1920,
            dheight=1080,
        )

    def play(self, media_path):
        self.current_media_path = media_path
        self.player.pause = False
        self.play_state_changed.emit(True)
        return True

    def stop(self):
        self.current_media_path = None
        self.player.pause = True
        self.play_state_changed.emit(False)

    def set_playing(self, is_playing):
        self.player.pause = not is_playing
        self.play_state_changed.emit(is_playing)

    def get_progress(self):
        return (25, 100) if self.current_media_path else (0, 0)

    def set_volume(self, value):
        pass

    def set_mute(self, value):
        pass

    def seek_to_percent(self, value):
        pass

    def add_external_subtitle(self, path):
        pass


class FakeVideoWidget(QWidget):
    clicked = Signal()
    double_clicked = Signal()
    files_dropped = Signal(list)

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine


class TestPavoPlayer(pavo_main.PavoPlayer):
    def load_data(self):
        self.refresh_playlist_ui()

    def save_data(self):
        pass


class PiPMainIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        engine_patch = patch.object(pavo_main, "PavoEngine", FakeEngine)
        video_patch = patch.object(pavo_main, "PavoVideoWidget", FakeVideoWidget)
        self.addCleanup(engine_patch.stop)
        self.addCleanup(video_patch.stop)
        engine_patch.start()
        video_patch.start()

        self.window = TestPavoPlayer()
        self.window.playlist = ["/tmp/first.mp4", "/tmp/second.mp4"]
        self.window.current_idx = 0
        self.window.refresh_playlist_ui()
        self.window.engine.play(self.window.playlist[0])
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.app.removeEventFilter(self.window)
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_enter_and_return_restore_main_window_ui(self):
        self.window.enter_pip()
        self.app.processEvents()

        self.assertTrue(self.window._is_pip)
        self.assertTrue(self.window.windowFlags() & Qt.WindowStaysOnTopHint)
        self.assertTrue(self.window.pip_overlay.isVisible())
        self.assertTrue(self.window.hud.isHidden())
        self.assertTrue(self.window.menuBar().isHidden())
        self.assertEqual(self.window.size().width(), 480)
        self.assertEqual(self.window.size().height(), 270)
        self.assertEqual(self.window.main_layout.spacing(), 0)
        margins = self.window.main_layout.contentsMargins()
        self.assertEqual(
            (margins.left(), margins.top(), margins.right(), margins.bottom()),
            (0, 0, 0, 0),
        )
        self.assertEqual(
            self.window.video_canvas.geometry(),
            self.window.central_widget.rect(),
        )
        self.assertEqual(
            self.window.pip_overlay.geometry(),
            self.window.central_widget.rect(),
        )
        self.assertEqual(
            self.window.pip_overlay.progress_indicator.progress_ratio,
            0.25,
        )

        self.window.pip_overlay.return_btn.click()
        self.app.processEvents()

        self.assertFalse(self.window._is_pip)
        self.assertTrue(self.window.pip_overlay.isHidden())
        self.assertTrue(self.window.hud.isVisible())
        self.assertTrue(self.window.menuBar().isVisible())

    def test_pip_controls_reuse_playlist_and_playback_paths(self):
        self.window.enter_pip()
        self.window.pip_overlay.next_btn.click()

        self.assertEqual(self.window.current_idx, 1)
        self.assertEqual(
            self.window.engine.current_media_path,
            "/tmp/second.mp4",
        )
        self.assertFalse(self.window.pip_overlay.next_btn.isEnabled())

        self.window.pip_overlay.play_btn.click()
        self.assertFalse(self.window.hud.is_playing)
        self.assertFalse(self.window.pip_overlay.is_playing)
        self.assertTrue(self.window.pip_overlay.controls_visible)

        self.window.pip_overlay.previous_btn.click()
        self.assertEqual(self.window.current_idx, 0)
        self.assertEqual(
            self.window.engine.current_media_path,
            "/tmp/first.mp4",
        )

    def test_clear_playlist_exits_pip_to_empty_state(self):
        self.window.enter_pip()
        self.window.clear_playlist()
        self.app.processEvents()

        self.assertFalse(self.window._is_pip)
        self.assertEqual(self.window.playlist, [])
        self.assertEqual(self.window.current_idx, -1)
        self.assertIsNone(self.window.engine.current_media_path)
        self.assertTrue(self.window.empty_state.isVisible())
        self.assertEqual(
            self.window.pip_overlay.progress_indicator.progress_ratio,
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
