from kivy.clock import Clock

class CameraHandler:
    def switch_cam(self, instance):
        """
        Переключает камеру с фронтальной на веб и обратно (если это возможно)

        """
        old_index = self.camera.index
        new_index = 1 if old_index == 0 else 0
        
        try:
            self.camera.play = False
            self.camera.index = new_index
            # Важно: self.rot должен существовать в основном классе
            self.rot.angle = 90 if new_index == 1 else -90
            Clock.schedule_once(self._try_restart_camera, 0.1)
        except Exception:
            self._handle_switch_error(old_index)

    def _try_restart_camera(self, dt):
        try:
            self.camera.play = True
        except Exception:
            self._handle_switch_error(0)

    def _handle_switch_error(self, fallback_index):
        self.camera.index = fallback_index
        self.camera.play = True
        self.switch_btn.text = "не смею смотреть на вас..."
        Clock.schedule_once(
            lambda dt: setattr(self.switch_btn, 'text', "Сменить камеру"), 1.5)