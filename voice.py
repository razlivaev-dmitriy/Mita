import torch
import sounddevice as sd
import numpy as np
import pyrubberband as pyrb

device = torch.device('cpu') if not torch.cuda.is_available() else torch.device('cuda')

class Voice():
    def __init__(self):
        self.model = torch.package.PackageImporter(f"models/v5_ru.pt").load_pickle("tts_models", "model")
        self.model.to(device)
        self.sample_rate = 48000
        self.speaker = 'xenia'
        self.speed = 0.95
        self.pitch = 0.7
        self.volume = 1
    
    def say(self, text):
        audio = self.model.apply_tts(
            ssml_text=text,
            speaker=self.speaker,
            sample_rate=self.sample_rate,
            put_accent=True,
            put_yo=True
        )
        audio = np.array(audio, dtype=np.float32)
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio * (self.volume / max_val)
        if self.speed != 1.0:
            audio = pyrb.time_stretch(audio, self.sample_rate, self.speed)
        if self.pitch != 0:
            audio = pyrb.pitch_shift(audio, self.sample_rate, self.pitch)
        sd.play(audio, self.sample_rate)
        sd.wait()
        
    def ChangeSpeed(self, speed):
        self.speed = speed
    
    def ChangePitch(self, pitch):
        self.pitch = pitch
    
    def ChangeVolume(self, volume):
        self.volume = volume
        
    def ChangeSpeaker(self, speaker):
        self.speaker = speaker