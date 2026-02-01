# currently working code
import webbrowser, re
from kivy.app import App
from kivy.uix.camera import Camera
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from pyzbar.pyzbar import decode, ZBarSymbol
from PIL import Image, ImageEnhance, ImageOps
from kivy.utils import platform
from kivy.graphics import Rotate, PushMatrix, PopMatrix
from kivy.metrics import dp
from handle_camera import CameraHandler

class QRScannerApp(App, CameraHandler):
    def build(self):
        # Переменная для хранения текущего URL
        self.current_url = None

        # Запрос разрешений для Android
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.CAMERA])

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

        # 4. Кнопка смены камеры
        self.switch_btn = Button(text="Сменить камеру", 
                                 size_hint_y=None, height=dp(60))
        self.switch_btn.bind(on_press=self.switch_cam)

        # 5. Кнопка бубнёжки
        self.notific_btn = Button(text="", 
                                  size_hint_y=None, height=dp(30),
                                  background_color=(0.0, 0.7, 0.1, 1))

        self.layout.add_widget(self.camera)
        self.layout.add_widget(self.link_btn)
        self.layout.add_widget(self.notific_btn)
        self.layout.add_widget(self.switch_btn)

        self.url_pattern = re.compile(r'https?://[^\s]+')
        self.complain_message = "" # сообщение о последней выполненной операции
        self.is_scanning = True    # флаг блокировки сканера
        self.frame_number = 0      # счётчик кадров

        Clock.schedule_interval(self.update, 1.0 / 5.0)
        return self.layout
    
    def open_link(self, instance):
        if self.current_url:
            webbrowser.open(self.current_url)
            # 1. Прячем кнопку СРАЗУ, но НЕ включаем scanning здесь
            self.link_btn.height = dp(30)
            self.link_btn.text = ""
            self.current_url = None
            
            if self.camera:
                self.camera.play = False
                # 2. Включаем камеру через 0.2 сек
                Clock.schedule_once(self._resume_camera, 0.2)

    def _resume_camera(self, dt):
        self.camera.play = True
        # 3. А сканирование разрешаем еще через 0.5 сек, 
        # когда текстура ТОЧНО прогрузится
        Clock.schedule_once(self._enable_scan, 0.5)

    def _enable_scan(self, dt):
        self.is_scanning = True

    def hide_btn(self, *dt):
        self.link_btn.height = dp(30)
        self.link_btn.text = ""
        self.current_url = None
        self.is_scanning = True

    def update(self, dt):
        if not self.camera.texture or not self.is_scanning: return

        try:
            self.frame_number = (self.frame_number + 1) % 10
            pil_img = Image.frombytes('RGBA', 
                                      self.camera.texture.size, 
                                      self.camera.texture.pixels)

            pil_img = pil_img.convert('RGB').convert('L')
            # ИСПРАВЛЯЕМ ОРИЕНТАЦИЮ KIVY (чаще всего это -1 по вертикали)
            pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM) 
            # 2. Динамическое выравнивание освещения
            pil_img = ImageOps.autocontrast(pil_img, cutoff=2)
            # Контраст
            pil_img = ImageEnhance.Contrast(pil_img).enhance(2.0)
            # Резкость
            pil_img = ImageEnhance.Sharpness(pil_img).enhance(1.5)

            res = None
            # анализ изображения каждые два кадра
            if self.frame_number % 2 == 0:
              self.complain_message = "..."

              # 1. Проход по обычному изображению
              for angle in [0, 90]:
                pil_img_rot = pil_img if angle==0 else pil_img.rotate(angle, expand=True)
                found = decode(pil_img_rot, symbols=[ZBarSymbol.QRCODE])
                if found:
                    res = found
                    break
              # 2. Отзеркаливание по горизонтали, если код не найден
              if not res:
                for angle in [0, 90]:
                  pil_img = pil_img.transpose(Image.FLIP_LEFT_RIGHT) 
                  pil_img_rot = pil_img if angle==0 else pil_img.rotate(angle, expand=True)
                  found = decode(pil_img_rot, symbols=[ZBarSymbol.QRCODE])
                  if found:
                      res = found
                      break
              # 3. Отзеркаливание по горизонтали, если код до сих пор не найден
              if not res:
                for angle in [0, 90]:
                  pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM) 
                  pil_img_rot = pil_img if angle==0 else pil_img.rotate(angle, expand=True)
                  found = decode(pil_img_rot, symbols=[ZBarSymbol.QRCODE])
                  if found:
                      res = found
                      break

              self.link_btn.text = "рассматриваюююуууу..."
              if res:
                  self.link_btn.text = "что-то похожее..."
                  url = res[0].data.decode('utf-8', errors='replace').strip()
                  self.link_btn.text = "что-то похожее на..." + url
                  if self.url_pattern.match(url):
                      self.is_scanning = False  
                      self.current_url = url
                      self.link_btn.text = f"ОТКРЫТЬ: {url[:25]}..."
                      self.link_btn.height = dp(60)   
                      Clock.unschedule(self.hide_btn)
                      Clock.schedule_once(self.hide_btn, 4)

        except Exception:
            self.notific_btn.text = self.complain_message
            Clock.schedule_once(
              lambda dt: setattr(self.notific_btn, 'text', "сложна..."), 1.5)
            pass

if __name__ == '__main__':
    QRScannerApp().run()