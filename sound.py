import keyboard

class Sound():
    def __init__(self, current_volume, is_muted):
        self.current_volume = current_volume
        self.is_muted = is_muted

    def mute(self):
        if not self.is_muted:
            self.is_muted = True
            keyboard.send("volume mute")
    
    def demute(self):
        if self.is_muted:
            self.is_muted = False
            keyboard.send("volume mute")

    @staticmethod
    def volume_up(value):
        for i in range(value//2):
            keyboard.send("volume up")

    @staticmethod
    def volume_down(value):
        for i in range(value//2):
            keyboard.send("volume down")

    def volume_set(self, value):
        if value > 100:
            value = 100
        elif int(value) < 0:
            value = 0
        if self.current_volume == None:
            self.volume_down(100)
            self.volume_up(value)
            self.current_volume = (value // 2) * 2
        elif self.current_volume > value:
            self.volume_down(self.current_volume - value)
            self.current_volume -= (value // 2) * 2
        else:
            self.volume_up(value - self.current_volume)
            self.current_volume += (value // 2) * 2

    # @staticmethod
    # def volume_min(self):
    #     self.volume_set(0)

    # @staticmethod
    # def volume_max(self):
    #     self.volume_set(100)