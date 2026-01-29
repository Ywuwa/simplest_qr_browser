import webbrowser # high-level interface to display web-based documents
import re         # lib for regular expressions
from kivy.app import App
from kivy.uix.camera import Camera
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from pyzbar.pyzbar import decode
from PIL import Image, ImageEnhance
from kivy.utils import platform
from kivy.graphics import Rotate, PushMatrix, PopMatrix
from kivy.metrics import dp

class QRScannerApp(App):
  def build(self):
    # 1. Запрос разрешений (обязательно для Android > 10)
    if platform == 'android':
        from android.permissions import request_permissions, Permission
        request_permissions([Permission.CAMERA, Permission.INTERNET])

    self.layout = BoxLayout(orientation='vertical')

    # 2. Камера
    self.camera = Camera(index=0, resolution=(640, 480), 
                         play=True, allow_stretch=True, keep_ratio=True)
    
    # 3. Исправление ориентации (Canvas)
    with self.camera.canvas.before:
      PushMatrix()
      self.rot = Rotate(angle=90, origin=self.camera.center)
    with self.camera.canvas.after:
      PopMatrix()
    self.camera.bind(center=lambda inv, val: setattr(self.rot, 'origin', val))

    # 4. Кнопка ссылки
    self.link_btn = Button(
        text="", size_hint_y=None, height=0, 
        background_color=(0.1, 0.7, 0.1, 1), font_size='16sp'
    )
    self.link_btn.bind(on_press=self.open_link)

    # 5. Кнопка смены камеры
    self.switch_btn = Button(text="Сменить камеру", 
                             size_hint_y=None, height=dp(50))
    self.switch_btn.bind(on_press=self.switch_cam)

    self.layout.add_widget(self.camera)
    self.layout.add_widget(self.link_btn)
    self.layout.add_widget(self.switch_btn)
    
    self.url_pattern = re.compile(r'https?://[^\s]+')
    self.last_url = None
    
    Clock.schedule_interval(self.update, 1.0 / 8.0)
    return self.layout

  def switch_cam(self, instance):
    # Чтобы избежать артефактов, останавливаем камеру перед сменой индекса
    self.camera.play = False
    self.camera.index = 1 if self.camera.index == 0 else 0
    # Меняем угол: если на одной 90, на другой часто нужно -90 (или 270)
    self.rot.angle = -90 if self.camera.index == 1 else 90
    Clock.schedule_once(lambda dt: setattr(self.camera, 'play', True), 0.2)
    
  def open_link(self, instance):
    if self.current_url:
      webbrowser.open(self.current_url)
      self.hide_button()
      
  def hide_button(self, *args):
    self.link_btn.height = 0
    self.link_btn.text = ""
    self.current_url = None

  def update(self, dt):
    if not self.camera.texture: return

    try:
      texture = self.camera.texture
      # 1. Сначала создаем PIL-объект
      pil_img = Image.frombytes(
        mode='RGBA', size=texture.size, data=texture.pixels).convert('L')
      
      # 2. Улучшаем контраст ИЗОБРАЖЕНИЯ
      enhancer = ImageEnhance.Contrast(pil_img)
      pil_img = enhancer.enhance(2.0)
      
      # 3. Ищем коды
      decoded_res = None
      for angle in [0, 90]:
        res = decode(pil_img.rotate(angle, expand=True))
        if res:
          decoded_res = res
          break
        
      if decoded_res:
        # Берем данные из первого найденного кода в списке
        url = decoded_res[0].data.decode('utf-8').strip()
        if self.url_pattern.match(url):
          self.current_url = url
          self.link_btn.text = f"ОТКРЫТЬ: {url[:30]}..."
          self.link_btn.height = dp(70)
          
          Clock.unschedule(self.hide_button)
          Clock.schedule_once(self.hide_button, 3)
    except Exception as e:
      print(f"Update error: {e}")

if __name__ == '__main__':
    QRScannerApp().run()