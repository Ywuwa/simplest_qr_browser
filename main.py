# currently working code
import webbrowser, re
from kivy.app import App
from kivy.uix.camera import Camera
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from pyzbar.pyzbar import decode
from PIL import Image, ImageEnhance, ImageOps
from kivy.utils import platform
from kivy.graphics import Rotate, PushMatrix, PopMatrix
from kivy.metrics import dp

class QRScannerApp(App):
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
        
        # 2. Исправление ориентации
        with self.camera.canvas.before:
            PushMatrix()
            self.rot = Rotate(angle=-90, origin=self.camera.center)
        with self.camera.canvas.after:
            PopMatrix()
        self.camera.bind(center=lambda inv, val: setattr(self.rot, 'origin', val))
        
        # 3. Кнопка ссылки (высота 0 — скрыта)
        self.link_btn = Button(text="", size_hint_y=None, height=0, 
                               background_color=(0.1, 0.7, 0.1, 1))
        self.link_btn.bind(on_press=self.open_link)

        # 4. Кнопка смены камеры
        self.switch_btn = Button(text="Сменить камеру", 
                                 size_hint_y=None, height=dp(50))
        self.switch_btn.bind(on_press=self.switch_cam)

        self.layout.add_widget(self.camera)
        self.layout.add_widget(self.link_btn)
        self.layout.add_widget(self.switch_btn)

        self.url_pattern = re.compile(r'https?://[^\s]+')

        Clock.schedule_interval(self.update, 1.0 / 5.0)
        return self.layout
    
    def switch_cam(self, instance):
        self.camera.play = False
        self.camera.index = 1 if self.camera.index == 0 else 0
        self.rot.angle = 90 if self.camera.index == 1 else -90
        Clock.schedule_once(lambda dt: setattr(self.camera, 'play', True), 0.5)

    def open_link(self, instance):
        if self.current_url:
            webbrowser.open(self.current_url)
            self.hide_btn()

    def hide_btn(self, *dt):
        self.link_btn.height = 0
        self.link_btn.text = ""
        self.current_url = None

    def update(self, dt):
        if not self.camera.texture: return

        texture = self.camera.texture
        pil_img = Image.frombytes(mode='RGBA', 
                                  size=texture.size, 
                                  data=texture.pixels).convert('L')

        # 2. Динамическое выравнивание освещения (спасает от бликов)
        pil_img = ImageOps.autocontrast(pil_img)
        # --- ЦИФРОВОЙ ЗУМ ДЛЯ МЕЛКИХ КОДОВ ---
        # Вырезаем центральный квадрат 300x300 и увеличиваем его до 600x600
        w, h = pil_img.size
        sz = 400
        left, top = (w - sz)/2, (h - sz)/2
        pil_img = pil_img.crop((
          left, top, left + sz, top + sz)).resize((800, 800), Image.Resampling.BILINEAR)
        # Контраст
        pil_img = ImageEnhance.Contrast(pil_img).enhance(2.0)
        # Резкость
        pil_img = ImageEnhance.Sharpness(pil_img).enhance(2.0)
        # Строгое разделение в Ч/Б
        pil_img = pil_img.point(lambda x: 0 if x < 128 else 255, '1').convert('L')
        res = None
        # Проверка двух углов
        for angle in [0, 90]:
            found = decode(pil_img.rotate(angle, expand=True))
            if found:
                res = found
                break

        # Инверсия (если не получается увидеть код)
        if not res:
            for angle in [0, 90]:
              inv_img = ImageOps.invert(pil_img.rotate(angle, expand=True))
              found = decode(inv_img)
              if found:
                  res = found
                  break

        if res:
            url = res[0].data.decode('utf-8').strip()
            if self.url_pattern.match(url):
                self.current_url = url
                self.link_btn.text = f"ОТКРЫТЬ: {url[:25]}..."
                self.link_btn.height = dp(50)        
                Clock.unschedule(self.hide_button)
                Clock.schedule_once(self.hide_button, 4)

if __name__ == '__main__':
    QRScannerApp().run()