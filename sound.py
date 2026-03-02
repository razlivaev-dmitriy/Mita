from pycaw.pycaw import AudioUtilities

class Sound():
    def __init__(self):
        self.volume = AudioUtilities.GetSpeakers().EndpointVolume
        self.current_volume = self.volume.GetMasterVolumeLevelScalar()
        self.is_muted = self.volume.GetMute()

    def mute(self):
        if not self.is_muted:
            self.is_muted = True
            self.volume.SetMute(1, None)
    
    def demute(self):
        if self.is_muted:
            self.is_muted = False
            self.volume.SetMute(0, None)

    def volume_up(self, value):
        self.volume.SetMasterVolumeLevelScalar(self.current_volume + value/100, None)
        self.current_volume = value/100

    def volume_down(self, value):
        self.volume.SetMasterVolumeLevelScalar(self.current_volume - value/100, None)
        self.current_volume = value/100

    def volume_set(self, value):
        self.volume.SetMasterVolumeLevelScalar(value/100, None)
        self.current_volume = value/100

    def volume_min(self):
        self.volume.SetMasterVolumeLevelScalar(0, None)

    def volume_max(self):
        self.volume.SetMasterVolumeLevelScalar(1, None)
