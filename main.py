# currently working code
import webbrowser, re
from kivy.app import App
from kivy.uix.camera import Camera
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.utils import platform
from kivy.graphics import Rotate, PushMatrix, PopMatrix
from kivy.metrics import dp
if platform == 'android':
    from jnius import autoclass
import threading

from handle_camera import CameraHandler
from handle_scanning import ScanningHandler

class QRScannerApp(App, CameraHandler, ScanningHandler):
    def build(self):
        # Переменная для хранения текущего URL
        self.current_url = None

        # Запрос разрешений для Android
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.CAMERA])
        #-----------------------------------------------------------------------
        
        #-----------------------------------------------------------------------
        self.layout = BoxLayout(orientation='vertical')

        # 1. Камера  640x480 — самая стабильная для этого кода
        self.camera = Camera(index=0, resolution=(640, 480), 
                             play=True, allow_stretch=True, keep_ratio=True)
        
        # 2. Исправление ориентации изображения с камеры
        with self.camera.canvas.before:
            PushMatrix()
            self.rot = Rotate(angle=-90, origin=self.camera.center)
        with self.camera.canvas.after:
            PopMatrix()
        self.camera.bind(center=lambda inv, val: setattr(self.rot, 'origin', val))
        
        # 3. Кнопка ссылки
        self.link_btn = Button(text="", size_hint_y=None, height=dp(30), 
                               background_color=(0.6, 0.6, 0.8, 1))
        self.link_btn.bind(on_press=self.open_link)

        # 4. Кнопка бубнёжки
        self.notific_btn = Button(text="", 
                                  size_hint_y=None, height=dp(30),
                                  background_color=(0.0, 0.7, 0.1, 1))
        
        self.layout.add_widget(self.camera)
        self.layout.add_widget(self.link_btn)
        self.layout.add_widget(self.notific_btn)
        #-----------------------------------------------------------------------
        
        #-----------------------------------------------------------------------
        btns_layout = BoxLayout(orientation='horizontal', 
                                size_hint_y=None, height=dp(60))

        # 5. Кнопка смены камеры
        self.switch_btn = Button(text="Сменить камеру", 
                                 size_hint_x=0.75)#, height=dp(60))
        self.switch_btn.bind(on_press=self.switch_cam)
        
        # 5. Кнопка фонарика
        self.flash_btn = Button(text="==#", 
                                 size_hint_x=0.25)#, height=dp(60))
        self.flash_btn.bind(on_press=self.flash_button_pressed)
        
        btns_layout.add_widget(self.switch_btn)
        btns_layout.add_widget(self.flash_btn)
        
        self.layout.add_widget(btns_layout)
        #-----------------------------------------------------------------------

        self.url_pattern = re.compile(r'https?://[^\s]+')
        self.complain_message = "" # сообщение о последней выполненной операции
        self.is_scanning = True    # флаг блокировки сканера
        self.frame_number = 0      # счётчик кадров
        self.flash_enabled = False  # статус фонарика

        Clock.schedule_interval(self.update, 1.0 / 5.0)
        return self.layout
      
    def on_pause(self):
        # Обязательно останавливаем камеру при сворачивании
        self.camera.play = False
        Clock.unschedule(self.update)
        # Выключаем фонарик
        if self.flash_enabled:
          self.flash_button_pressed(self.flash_btn)
        # Возвращаем True, чтобы приложение не закрылось, а уснуло
        return True
  
    def on_resume(self):
        # При возврате в приложение даем системе 0.5 сек 
        # на восстановление графического контекста и включаем камеру
        Clock.schedule_once(self._restart_camera, 0.5)
  
    def _restart_camera(self, dt):
        self.camera.play = True
        Clock.schedule_interval(self.update, 1.0 / 5.0)
        
    def set_flashlight(self, state: bool):
        """Включает или выключает фонарик через Android Camera2 API.      
        Args:
            state (bool): True для включения, False для выключения.
        """
        if platform != 'android':
            print("Фонарик доступен только на Android")
            return

        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            activity = PythonActivity.mActivity
            camera_manager = activity.getSystemService(Context.CAMERA_SERVICE)
            
            # '0' — обычно ID основной задней камеры с фонариком
            camera_id = camera_manager.getCameraIdList()[0]
            camera_manager.setTorchMode(camera_id, state)
        except Exception as e:
            print(f"Ошибка управления фонариком: {e}")
            
    def flash_button_pressed(self, instance):
        self.flash_enabled = not self.flash_enabled
        instance.text = "==# [ВКЛ]" if self.flash_enabled else "==#"
        try:
            # Пытаемся вызвать нативный метод Kivy-камеры для Android
            if self.flash_enabled:
                self.camera._camera.set_flash_mode('torch')
            else:
                self.camera._camera.set_flash_mode('off')
        except Exception as e:
            print(f"Способ Б не сработал: {e}")
            # Если не вышло, вызываем ваш метод через jnius (Способ 4)
            self.set_flashlight(self.flash_enabled)
      
    def open_link(self, instance):
        if self.current_url:
            webbrowser.open(self.current_url)
            # 1. Прячем кнопку СРАЗУ, но НЕ включаем scanning здесь
            self.link_btn_to_default()
            
            if self.camera:
                self.camera.play = False
                # 2. Включаем камеру через 0.2 сек
                Clock.schedule_once(self._resume_camera, 0.2)

    def _resume_camera(self, *dt):
        self.camera.play = True
        # 3. А сканирование разрешаем еще через 0.5 сек, 
        # когда текстура ТОЧНО прогрузится
        Clock.schedule_once(self._enable_scan, 0.5)

    def _enable_scan(self, *dt):
        self.is_scanning = True

    def update(self, *dt):
        """
        Сканирует изображение, если есть что сканировать и сканер активен
        Сканирование происходит в отдельном потоке
  
        """
        if not self.camera.texture or not self.is_scanning: return
        
        Clock.schedule_once(
            lambda dt: setattr(
              self.link_btn, 'text', "рассматриваюююуууу..."), 0)
        frame_data = self.camera.texture.pixels 
        frame_size = self.camera.texture.size
        # Блокируем создание новых потоков сразу
        self.is_scanning = False
        
        # Запускаем один поток для одного анализа
        thread = threading.Thread(
            target=self.scan_frame_task, 
            args=(frame_data, frame_size)
        )
        # daemon=True гарантирует, что поток умрет при закрытии приложения
        thread.daemon = True 
        thread.start()

if __name__ == '__main__':
    QRScannerApp().run()