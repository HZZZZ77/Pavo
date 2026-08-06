import ctypes
import logging
import sys

from PySide6.QtCore import QByteArray, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QPushButton, QWidget


logger = logging.getLogger("pavo.pip")
PIP_CORNER_RADIUS = 14.0


SVG_PREVIOUS = (
    '<svg viewBox="0 0 24 24" fill="white">'
    '<path d="M6 5h2v14H6zM19 6v12l-9-6z"/></svg>'
)
SVG_PLAY = (
    '<svg viewBox="0 0 24 24" fill="white">'
    '<path d="M8 5v14l11-7z"/></svg>'
)
SVG_PAUSE = (
    '<svg viewBox="0 0 24 24" fill="white">'
    '<path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>'
)
SVG_NEXT = (
    '<svg viewBox="0 0 24 24" fill="white">'
    '<path d="M16 5h2v14h-2zM5 6v12l9-6z"/></svg>'
)
SVG_RETURN = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="white" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M9 14l-4-4 4-4"/><path d="M5 10h9a5 5 0 0 1 5 5v2"/>'
    '</svg>'
)
SVG_CLOSE = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="white" '
    'stroke-width="2" stroke-linecap="round">'
    '<path d="M6 6l12 12M18 6L6 18"/></svg>'
)


class MacWindowCornerStyle:
    def __init__(self):
        self._objc = None

    def apply(self, window, enabled):
        if sys.platform != "darwin" or QApplication.platformName() != "cocoa":
            return False

        try:
            self._load_runtime()
            native_view = ctypes.c_void_p(int(window.winId()))
            native_window = self._send_object(native_view, "window")
            content_view = self._send_object(native_window, "contentView")
            self._send_bool(content_view, "setWantsLayer:", True)
            layer = self._send_object(content_view, "layer")

            self._send_double(
                layer,
                "setCornerRadius:",
                PIP_CORNER_RADIUS if enabled else 0.0,
            )
            self._send_double(layer, "setBorderWidth:", 0.0)
            self._send_bool(layer, "setMasksToBounds:", enabled)
            if self._responds_to(layer, "setAllowsEdgeAntialiasing:"):
                self._send_bool(layer, "setAllowsEdgeAntialiasing:", enabled)
            if enabled:
                self._set_continuous_corner_curve(layer)
                self._send_bool(native_window, "setOpaque:", False)
                self._send_bool(native_window, "setHasShadow:", True)
                clear_color = self._send_class_object("NSColor", "clearColor")
                self._send_object_argument(
                    native_window,
                    "setBackgroundColor:",
                    clear_color,
                )
            return True
        except Exception:
            logger.debug("Native PiP corner styling is unavailable", exc_info=True)
            return False

    def _load_runtime(self):
        if self._objc is not None:
            return
        self._objc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
        self._objc.sel_registerName.argtypes = [ctypes.c_char_p]
        self._objc.sel_registerName.restype = ctypes.c_void_p
        self._objc.objc_getClass.argtypes = [ctypes.c_char_p]
        self._objc.objc_getClass.restype = ctypes.c_void_p

    def _selector(self, name):
        return self._objc.sel_registerName(name.encode("ascii"))

    def _message(self, result_type, *argument_types):
        prototype = ctypes.CFUNCTYPE(
            result_type,
            ctypes.c_void_p,
            ctypes.c_void_p,
            *argument_types,
        )
        return prototype(("objc_msgSend", self._objc))

    def _send_object(self, receiver, selector):
        return self._message(ctypes.c_void_p)(
            receiver,
            self._selector(selector),
        )

    def _send_bool(self, receiver, selector, value):
        self._message(None, ctypes.c_bool)(
            receiver,
            self._selector(selector),
            value,
        )

    def _send_double(self, receiver, selector, value):
        self._message(None, ctypes.c_double)(
            receiver,
            self._selector(selector),
            value,
        )

    def _send_object_argument(self, receiver, selector, value):
        self._message(None, ctypes.c_void_p)(
            receiver,
            self._selector(selector),
            value,
        )

    def _send_class_object(self, class_name, selector):
        class_object = self._objc.objc_getClass(class_name.encode("ascii"))
        return self._send_object(class_object, selector)

    def _responds_to(self, receiver, selector_name):
        return self._message(ctypes.c_bool, ctypes.c_void_p)(
            receiver,
            self._selector("respondsToSelector:"),
            self._selector(selector_name),
        )

    def _set_continuous_corner_curve(self, layer):
        if not self._responds_to(layer, "setCornerCurve:"):
            return
        string_class = self._objc.objc_getClass(b"NSString")
        continuous = self._message(ctypes.c_void_p, ctypes.c_char_p)(
            string_class,
            self._selector("stringWithUTF8String:"),
            b"continuous",
        )
        self._send_object_argument(layer, "setCornerCurve:", continuous)


class PiPProgressIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ratio = 0.0
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    @property
    def progress_ratio(self):
        return self._ratio

    def set_progress(self, current, total):
        if total <= 0:
            ratio = 0.0
        else:
            ratio = max(0.0, min(1.0, current / total))
        if ratio != self._ratio:
            self._ratio = ratio
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        track_height = 1.0
        track = QRectF(
            0,
            (self.height() - track_height) / 2.0,
            self.width(),
            track_height,
        )
        painter.setBrush(QColor(255, 255, 255, 24))
        painter.drawRoundedRect(track, 0.5, 0.5)

        if self._ratio > 0:
            played = QRectF(
                track.left(),
                track.top(),
                track.width() * self._ratio,
                track_height,
            )
            gradient = QLinearGradient(played.topLeft(), played.topRight())
            gradient.setColorAt(0.0, QColor(10, 132, 255, 165))
            gradient.setColorAt(1.0, QColor(0, 122, 255, 175))
            painter.setBrush(gradient)
            painter.drawRoundedRect(played, 0.5, 0.5)


class PiPControlButton(QPushButton):
    def __init__(self, base_alpha=96, parent=None):
        super().__init__(parent)
        self._base_alpha = base_alpha
        self.setAttribute(Qt.WA_Hover, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        if not self.isEnabled():
            alpha = 42
        elif self.isDown():
            alpha = min(180, self._base_alpha + 32)
        elif self.underMouse():
            alpha = min(170, self._base_alpha + 18)
        else:
            alpha = self._base_alpha

        circle = QPainterPath()
        circle.addEllipse(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5))
        painter.fillPath(circle, QColor(18, 18, 20, alpha))

        icon_size = self.iconSize()
        icon_rect = QRect(
            (self.width() - icon_size.width()) // 2,
            (self.height() - icon_size.height()) // 2,
            icon_size.width(),
            icon_size.height(),
        )
        painter.setOpacity(1.0 if self.isEnabled() else 0.42)
        mode = QIcon.Normal if self.isEnabled() else QIcon.Disabled
        self.icon().paint(painter, icon_rect, Qt.AlignCenter, mode, QIcon.Off)


class PiPOverlay(QWidget):
    previous_requested = Signal()
    play_pause_requested = Signal()
    next_requested = Signal()
    return_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent=None, hide_delay_ms=1800):
        super().__init__(parent)
        self.setObjectName("pipOverlay")
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.NoFocus)
        self._is_playing = False
        self._controls_visible = True
        self._native_corner_style = MacWindowCornerStyle()

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(hide_delay_ms)
        self._hide_timer.timeout.connect(self.hide_controls)

        self.icons = {
            "previous": self._create_svg_icon(SVG_PREVIOUS),
            "play": self._create_svg_icon(SVG_PLAY),
            "pause": self._create_svg_icon(SVG_PAUSE),
            "next": self._create_svg_icon(SVG_NEXT),
            "return": self._create_svg_icon(SVG_RETURN),
            "close": self._create_svg_icon(SVG_CLOSE),
        }

        self.return_btn = self._create_button(
            "pipReturnButton", self.icons["return"], QSize(20, 20), 34,
            "Return to Main Window",
        )
        self.close_btn = self._create_button(
            "pipCloseButton", self.icons["close"], QSize(18, 18), 34,
            "Close Picture in Picture",
        )
        self.previous_btn = self._create_button(
            "pipPreviousButton", self.icons["previous"], QSize(25, 25), 48,
            "Previous",
        )
        self.play_btn = self._create_button(
            "pipPlayButton", self.icons["play"], QSize(32, 32), 58,
            "Play / Pause",
        )
        self.next_btn = self._create_button(
            "pipNextButton", self.icons["next"], QSize(25, 25), 48,
            "Next",
        )

        self.progress_indicator = PiPProgressIndicator(self)

        self.return_btn.clicked.connect(self.return_requested.emit)
        self.close_btn.clicked.connect(self.close_requested.emit)
        self.previous_btn.clicked.connect(self.previous_requested.emit)
        self.play_btn.clicked.connect(self.play_pause_requested.emit)
        self.next_btn.clicked.connect(self.next_requested.emit)

        self.hide()

    @staticmethod
    def _create_svg_icon(svg_string, size=64):
        renderer = QSvgRenderer(QByteArray(svg_string.encode("utf-8")))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)

    def _create_button(self, object_name, icon, icon_size, button_size, tooltip):
        base_alpha = 116 if object_name == "pipPlayButton" else 92
        button = PiPControlButton(base_alpha, self)
        button.setObjectName(object_name)
        button.setIcon(icon)
        button.setIconSize(icon_size)
        button.setFixedSize(button_size, button_size)
        button.setToolTip(tooltip)
        button.setCursor(Qt.PointingHandCursor)
        button.setFocusPolicy(Qt.NoFocus)
        return button

    @property
    def controls_visible(self):
        return self._controls_visible

    @property
    def is_playing(self):
        return self._is_playing

    def activate(self):
        self.show()
        self.raise_()
        self._native_corner_style.apply(self.window(), True)
        self.show_controls()

    def deactivate(self):
        self._hide_timer.stop()
        self._native_corner_style.apply(self.window(), False)
        self.hide()

    def set_playing(self, is_playing):
        self._is_playing = bool(is_playing)
        self.play_btn.setIcon(
            self.icons["pause"] if self._is_playing else self.icons["play"]
        )
        if self._is_playing:
            self._schedule_hide()
        else:
            self._hide_timer.stop()
            self.show_controls()

    def set_navigation_enabled(self, previous_enabled, next_enabled):
        self.previous_btn.setEnabled(bool(previous_enabled))
        self.next_btn.setEnabled(bool(next_enabled))

    def set_progress(self, current, total):
        self.progress_indicator.set_progress(current, total)

    def notify_activity(self):
        if not self.isVisible():
            return
        self.show_controls()

    def pointer_left(self):
        if self._is_playing:
            self._hide_timer.start(min(350, self._hide_timer.interval()))

    def show_controls(self):
        for button in self._control_buttons():
            button.show()
            button.raise_()
        self._controls_visible = True
        if self._is_playing:
            self._schedule_hide()

    def hide_controls(self):
        if not self._is_playing:
            return
        for button in self._control_buttons():
            button.hide()
        self._controls_visible = False

    def _schedule_hide(self):
        self._hide_timer.start()

    def _control_buttons(self):
        return (
            self.return_btn,
            self.close_btn,
            self.previous_btn,
            self.play_btn,
            self.next_btn,
        )

    def resizeEvent(self, event):
        margin = 12
        self.return_btn.move(margin, margin)
        self.close_btn.move(self.width() - self.close_btn.width() - margin, margin)

        spacing = 12
        controls_width = (
            self.previous_btn.width()
            + self.play_btn.width()
            + self.next_btn.width()
            + (spacing * 2)
        )
        x = (self.width() - controls_width) // 2
        center_y = (self.height() - self.play_btn.height()) // 2
        self.previous_btn.move(
            x,
            center_y + (self.play_btn.height() - self.previous_btn.height()) // 2,
        )
        self.play_btn.move(x + self.previous_btn.width() + spacing, center_y)
        self.next_btn.move(
            x + self.previous_btn.width() + self.play_btn.width() + (spacing * 2),
            center_y + (self.play_btn.height() - self.next_btn.height()) // 2,
        )
        self.progress_indicator.setGeometry(
            18,
            self.height() - 6,
            max(0, self.width() - 36),
            2,
        )
        super().resizeEvent(event)

    def enterEvent(self, event):
        self.notify_activity()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.pointer_left()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        self.notify_activity()
        self._update_resize_cursor(event.position().toPoint())
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            window = self.window()
            window_handle = window.windowHandle()
            edges = self._resize_edges(event.position().toPoint())
            if window_handle and edges and window_handle.startSystemResize(edges):
                event.accept()
                return
            if window_handle and window_handle.startSystemMove():
                event.accept()
                return
        super().mousePressEvent(event)

    def _resize_edges(self, pos):
        margin = 8
        edges = Qt.Edges()
        if pos.x() <= margin:
            edges |= Qt.LeftEdge
        elif pos.x() >= self.width() - margin:
            edges |= Qt.RightEdge
        if pos.y() <= margin:
            edges |= Qt.TopEdge
        elif pos.y() >= self.height() - margin:
            edges |= Qt.BottomEdge
        return edges

    def _update_resize_cursor(self, pos):
        edges = self._resize_edges(pos)
        if edges in (Qt.LeftEdge | Qt.TopEdge, Qt.RightEdge | Qt.BottomEdge):
            self.setCursor(Qt.SizeFDiagCursor)
        elif edges in (Qt.RightEdge | Qt.TopEdge, Qt.LeftEdge | Qt.BottomEdge):
            self.setCursor(Qt.SizeBDiagCursor)
        elif edges & (Qt.LeftEdge | Qt.RightEdge):
            self.setCursor(Qt.SizeHorCursor)
        elif edges & (Qt.TopEdge | Qt.BottomEdge):
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.unsetCursor()
