from faster_whisper import WhisperModel

model_size = "small.en"

model = WhisperModel(model_size, device="cpu", compute_type="int8")

segments, _ = model.transcribe("Audio_input/test.mp3", beam_size=5)

for segment in segments:
    print(segment.text)