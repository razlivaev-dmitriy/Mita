from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class Sound():
    def __init__(self, is_muted):
        self.volume = cast(AudioUtilities.GetSpeakers().Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None), POINTER(IAudioEndpointVolume))
        self.current_volume = self.volume.GetMasterVolumeLevelScalar(None)
        self.is_muted = is_muted

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
