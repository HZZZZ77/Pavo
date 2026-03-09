from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QOpenGLContext
from PySide6.QtCore import Qt, QMetaObject
import mpv
import ctypes
import traceback

class PavoVideoWidget(QOpenGLWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.render_ctx = None
        self._get_proc_addr_c = None 
        
        self.setStyleSheet("background-color: #000000;")

    def initializeGL(self):
        print("[VideoWidget] initializeGL triggered. Setting up OpenGL context...")
        try:
            if not self.engine.player:
                print("[VideoWidget] Error: Engine not ready. Aborting OpenGL initialization.")
                return

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

            print("[VideoWidget] Binding mpv render context...")
            
            self.render_ctx = mpv.MpvRenderContext(
                self.engine.player,
                'opengl',
                opengl_init_params={'get_proc_address': self._get_proc_addr_c}
            )
            self.render_ctx.update_cb = self.on_mpv_update
            
            print("[VideoWidget] OpenGL context and mpv binding successfully established.")
            
            test_url = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
            self.engine.play(test_url)

        except Exception as e:
            print(f"[VideoWidget] Fatal error during initializeGL: {e}")
            traceback.print_exc()

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
        except Exception as e:
            print(f"[VideoWidget] Error during paintGL: {e}")

    def on_mpv_update(self):
        QMetaObject.invokeMethod(self, "update", Qt.QueuedConnection)