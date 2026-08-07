import os
import sys
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QSlider

from components.pip_overlay import PiPControlButton, PiPOverlay


class PiPOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.overlay = PiPOverlay(hide_delay_ms=30)
        self.overlay.resize(480, 270)
        self.overlay.activate()
        self.app.processEvents()

    def tearDown(self):
        self.overlay.close()
        self.overlay.deleteLater()
        self.app.processEvents()

    def test_exposes_only_minimal_controls_and_read_only_progress(self):
        button_names = {
            button.objectName()
            for button in self.overlay.findChildren(QPushButton)
        }
        self.assertEqual(
            button_names,
            {
                "pipReturnButton",
                "pipCloseButton",
                "pipPreviousButton",
                "pipPlayButton",
                "pipNextButton",
            },
        )
        self.assertEqual(self.overlay.findChildren(QSlider), [])
        for button in self.overlay.findChildren(QPushButton):
            self.assertIsInstance(button, PiPControlButton)
            self.assertEqual(button.styleSheet(), "")
        self.assertTrue(
            self.overlay.progress_indicator.testAttribute(
                Qt.WA_TransparentForMouseEvents
            )
        )
        self.assertEqual(self.overlay.progress_indicator.height(), 2)
        self.assertEqual(self.overlay.progress_indicator.x(), 18)
        self.assertEqual(
            self.overlay.width()
            - self.overlay.progress_indicator.geometry().right()
            - 1,
            18,
        )

    def test_buttons_forward_requests_without_playback_logic(self):
        requests = []
        self.overlay.previous_requested.connect(lambda: requests.append("previous"))
        self.overlay.play_pause_requested.connect(lambda: requests.append("play"))
        self.overlay.next_requested.connect(lambda: requests.append("next"))
        self.overlay.return_requested.connect(lambda: requests.append("return"))
        self.overlay.close_requested.connect(lambda: requests.append("close"))

        self.overlay.previous_btn.click()
        self.overlay.play_btn.click()
        self.overlay.next_btn.click()
        self.overlay.return_btn.click()
        self.overlay.close_btn.click()

        self.assertEqual(
            requests,
            ["previous", "play", "next", "return", "close"],
        )

    def test_navigation_state_tracks_playlist_boundaries(self):
        self.overlay.set_navigation_enabled(False, True)
        self.assertFalse(self.overlay.previous_btn.isEnabled())
        self.assertTrue(self.overlay.next_btn.isEnabled())

        self.overlay.set_navigation_enabled(True, False)
        self.assertTrue(self.overlay.previous_btn.isEnabled())
        self.assertFalse(self.overlay.next_btn.isEnabled())

    def test_playing_auto_hides_controls_and_activity_restores_them(self):
        self.overlay.set_playing(True)
        QTest.qWait(60)
        self.assertTrue(self.overlay.is_playing)
        self.assertFalse(self.overlay.controls_visible)

        self.overlay.notify_activity()
        self.assertTrue(self.overlay.controls_visible)

    def test_paused_state_keeps_controls_visible(self):
        self.overlay.set_playing(False)
        self.overlay.hide_controls()
        QTest.qWait(60)

        self.assertFalse(self.overlay.is_playing)
        self.assertTrue(self.overlay.controls_visible)

    def test_progress_is_clamped_and_reset_without_media(self):
        self.overlay.set_progress(25, 100)
        self.assertEqual(
            self.overlay.progress_indicator.progress_ratio,
            0.25,
        )

        self.overlay.set_progress(125, 100)
        self.assertEqual(
            self.overlay.progress_indicator.progress_ratio,
            1.0,
        )

        self.overlay.set_progress(10, 0)
        self.assertEqual(
            self.overlay.progress_indicator.progress_ratio,
            0.0,
        )

    def test_window_edges_are_available_for_native_resize(self):
        top_left = self.overlay._resize_edges(QPoint(0, 0))
        center = self.overlay._resize_edges(QPoint(240, 135))

        self.assertTrue(top_left & Qt.LeftEdge)
        self.assertTrue(top_left & Qt.TopEdge)
        self.assertFalse(center)


if __name__ == "__main__":
    unittest.main()
