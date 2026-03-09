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
        # 【护盾】：必须把转换后的 C 函数指针挂载到 self 上
        # 否则它刚传给 mpv 就会被 Python 当成垃圾回收掉，导致闪退！
        self._get_proc_addr_c = None 
        
        self.setStyleSheet("background-color: #000000;")

    def initializeGL(self):
        print("👉 [Qt] initializeGL 被触发！开始搭建 OpenGL 画板...")
        try:
            if not self.engine.player:
                print("❌ 引擎未就绪，取消画板初始化")
                return

            # 【修复 1】：C 语言底层的回调强制要求 2 个参数 (上下文指针, 函数名)
            def get_proc_address(ctx_ptr, name):
                ctx = QOpenGLContext.currentContext()
                name_str = name.decode('utf-8') if isinstance(name, bytes) else name
                addr = ctx.getProcAddress(name_str)
                return int(addr) if addr else 0

            # 【修复 2】：给 Python 函数穿上 C 语言的伪装衣 (强制指针转换)
            # 兼容 python-mpv 不同版本的底层写法
            if hasattr(mpv, 'MpvGlGetProcAddressFn'):
                self._get_proc_addr_c = mpv.MpvGlGetProcAddressFn(get_proc_address)
            elif hasattr(mpv, 'OpenGlCbGetProcAddrFn'):
                self._get_proc_addr_c = mpv.OpenGlCbGetProcAddrFn(get_proc_address)
            else:
                # 终极保底：手搓一个符合 C 标准的 void* fn(void*, char*) 指针
                CFuncType = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p)
                self._get_proc_addr_c = CFuncType(get_proc_address)

            print("🔗 开始绑定 mpv 渲染上下文...")
            
            # 这次传进去的，是纯正的 C 函数指针！
            self.render_ctx = mpv.MpvRenderContext(
                self.engine.player,
                'opengl',
                opengl_init_params={'get_proc_address': self._get_proc_addr_c}
            )
            self.render_ctx.update_cb = self.on_mpv_update
            
            print("🎨 OpenGL 画板初始化及 mpv 绑定绝对成功！")
            
            print("⏳ 画板已就绪，立即向引擎下达播放指令！")
            test_url = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
            self.engine.play(test_url)

        except Exception as e:
            print(f"❌ initializeGL 遭遇致命错误: {e}")
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
            print(f"❌ paintGL 遭遇错误: {e}")

    def on_mpv_update(self):
        QMetaObject.invokeMethod(self, "update", Qt.QueuedConnection)