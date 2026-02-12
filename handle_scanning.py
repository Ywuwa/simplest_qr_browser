from kivy.clock import Clock
from pyzbar.pyzbar import decode, ZBarSymbol
from PIL import Image, ImageEnhance, ImageOps
from kivy.metrics import dp

class ScanningHandler:
    def link_btn_to_default(self, *dt):
        """
        Приводит кнопку ссылки в исходное состояние
  
        """
        self.link_btn.background_color = (0.6, 0.6, 0.8, 1)
        self.link_btn.height = dp(30)
        self.link_btn.text = ""
        self.current_url = None
        
    def hide_btn(self, *dt):
        self.link_btn_to_default()
        self.is_scanning = True    
    
    def scan_frame_task(self, frame_data, frame_size):
        """
        Сканирует изображение на предмет наличия QR-кодов (ссылок)
  
        Parameters
        ----------
        frame_data (bytes): Байтовая строка пикселей (self.camera.texture.pixels)
        frame_size (list): Список [width, height]
    
        """
        found_valid_url = False
        try:
            self.frame_number = (self.frame_number + 1) % 10
            pil_img = Image.frombytes('RGBA', frame_size, frame_data)
    
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
    
              if res:
                  url = res[0].data.decode('utf-8', errors='replace').strip()
                  
                  if self.url_pattern.match(url):
                      found_valid_url = True 
                      self.current_url = url
                      Clock.schedule_once(lambda dt: self._show_url_ui(url))
                  else:
                      found_valid_url = True
                      Clock.schedule_once(lambda dt: self._show_url_guess_ui(url))
    
        except Exception:
            Clock.schedule_once(
              lambda dt: setattr(self.notific_btn, 'text', "сложна..."), 1.5)
            pass
        finally:
          # Разблокируем, только если НЕ нашли ссылку
          if not found_valid_url:
              self.is_scanning = True
              
    def _show_url_ui(self, url):
        """Выполняется строго в основном потоке"""
        self.link_btn.text = f"ОТКРЫТЬ: {url[:25]}..."
        self.link_btn.height = dp(60)
        self.link_btn.background_color = (0, 0.9, 0.9, 1)
        # Сбрасываем старые таймеры и ставим новый
        Clock.unschedule(self.hide_btn)
        Clock.schedule_once(self.hide_btn, 4)
      
    def _show_url_guess_ui(self, url):
        self.link_btn.text = "что-то похожее на..." + url
        Clock.unschedule(self.hide_btn)
        Clock.schedule_once(self.hide_btn, 1)