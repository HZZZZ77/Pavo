from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QOpenGLContext
from PySide6.QtCore import Qt, QMetaObject, Signal, QTimer
from PySide6.QtWidgets import QApplication
import mpv
import ctypes
import traceback

class PavoVideoWidget(QOpenGLWidget):
    clicked = Signal()
    double_clicked = Signal()
    # 👑 升级：可以一次性发射一堆文件的路径！
    files_dropped = Signal(list) 

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.render_ctx = None
        self._get_proc_addr_c = None 
        
        self.setStyleSheet("background-color: #000000;")
        self.setAcceptDrops(True)
        
        self._click_count = 0
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._handle_click_timeout)

    def initializeGL(self):
        try:
            if not self.engine.player: return

            def get_proc_address(ctx_ptr, name):
                ctx = QOpenGLContext.currentContext()
                name_str = name.decode('utf-8') if isinstance(name, bytes) else name
                addr = ctx.getProcAddress(name_str)
                return int(addr) if addr else 0

            if hasattr(mpv, 'MpvGlGetProcAddressFn'):
                self._get_proc_addr_c = mpv.MpvGlGetProcAddressFn(get_proc_address)
            elif hasattr(mpv, 'OpenGlCbGetProcAddrFn'):
                self._get_proc_addr_c = mpv.OpenGlCbGetProcAddrFn(get_proc_address)
            else:
                CFuncType = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p)
                self._get_proc_addr_c = CFuncType(get_proc_address)

            self.render_ctx = mpv.MpvRenderContext(
                self.engine.player,
                'opengl',
                opengl_init_params={'get_proc_address': self._get_proc_addr_c}
            )
            self.render_ctx.update_cb = self.on_mpv_update
            
        except Exception as e:
            print(f"[VideoWidget] Fatal error during initializeGL: {e}")

    def paintGL(self):
        try:
            if self.render_ctx:
                self.render_ctx.update()
                ratio = self.devicePixelRatio()
                self.render_ctx.render(
                    flip_y=True, 
                    opengl_fbo={
                        'w': int(self.width() * ratio),
                        'h': int(self.height() * ratio),
                        'fbo': self.defaultFramebufferObject()
                    }
                )
        except Exception: pass

    def on_mpv_update(self):
        QMetaObject.invokeMethod(self, "update", Qt.QueuedConnection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        # 👑 核心升级：遍历用户拖进来的所有文件
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            urls = event.mimeData().urls()
            paths = [url.toLocalFile() for url in urls if url.toLocalFile()]
            if paths:
                self.files_dropped.emit(paths)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta != 0:
            step = 5 if delta > 0 else -5
            try:
                main_window = self.window()
                if hasattr(main_window, 'hud') and hasattr(main_window.hud, 'vol_slider'):
                    current_vol = main_window.hud.vol_slider.value()
                    new_vol = max(0, min(100, current_vol + step))
                    main_window.hud.vol_slider.setValue(new_vol)
                    if hasattr(main_window, 'wake_hud'):
                        main_window.wake_hud()
            except: pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._click_count += 1
            if self._click_count == 1:
                delay = QApplication.doubleClickInterval()
                self._click_timer.start(delay if delay > 0 else 300)
            elif self._click_count == 2:
                self._click_timer.stop()
                self._click_count = 0 
                self.double_clicked.emit()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.mousePressEvent(event)

    def _handle_click_timeout(self):
        if self._click_count == 1:
            self.clicked.emit()
        self._click_count = 0

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            event.ignore()
        else:
            super().keyPressEvent(event)