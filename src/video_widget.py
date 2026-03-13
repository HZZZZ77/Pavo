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

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.render_ctx = None
        self._get_proc_addr_c = None 
        
        self.setStyleSheet("background-color: #000000;")
        
        # ==========================================
        # 👑 引入极其严苛的“状态机”计数器
        # ==========================================
        self._click_count = 0
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._handle_click_timeout)

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

    # ==========================================
    # 👑 绝对互斥的状态机逻辑
    # ==========================================
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._click_count += 1
            
            if self._click_count == 1:
                # 记录第一下点击，启动倒计时
                delay = QApplication.doubleClickInterval()
                self._click_timer.start(delay if delay > 0 else 300)
                
            elif self._click_count == 2:
                # 在倒计时内迎来了第二下点击！
                self._click_timer.stop()
                self._click_count = 0  # 状态彻底清零！这是关键！
                self.double_clicked.emit()
                
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        # 强制将 Qt 原生的双击事件映射为我们的“按下事件”，交给状态机统一收编防错！
        self.mousePressEvent(event)

    def _handle_click_timeout(self):
        # 【终极防抖锁】：就算定时器意外触发，只要发现状态被清零了，就绝对不执行暂停！
        if self._click_count == 1:
            self.clicked.emit()
        
        # 无论如何，重置状态，迎接下一轮交互
        self._click_count = 0

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            event.ignore()
        else:
            super().keyPressEvent(event)