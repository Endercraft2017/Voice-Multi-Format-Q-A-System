import sounddevice as sd
import numpy as np
import time
import wave
from pydub import AudioSegment
import threading
from faster_whisper import WhisperModel

# Whisper setup
model = WhisperModel("small.en", device="cpu", compute_type="int8")

SAMPLE_RATE = 16000
BLOCK_DURATION = 5  # seconds of silence to stop recording
OUTPUT_FOLDER = "recordings"

def record_block():
    print("🎙️ Start speaking... (stop = 5s silence)")

    audio_data = []
    last_sound_time = time.time()

    def callback(indata, frames, time_info, status):
        nonlocal last_sound_time, audio_data
        volume_norm = np.linalg.norm(indata) * 10
        if volume_norm > 0.01:  # threshold for "sound detected"
            last_sound_time = time.time()
        audio_data.append(indata.copy())

    with sd.InputStream(callback=callback, channels=1, samplerate=SAMPLE_RATE):
        while True:
            if time.time() - last_sound_time > BLOCK_DURATION:
                break
            time.sleep(0.1)

    audio_np = np.concatenate(audio_data, axis=0)
    return audio_np


def save_wav(audio_np, filename):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((audio_np * 32767).astype(np.int16).tobytes())


def save_mp3(wav_path, mp3_path):
    audio = AudioSegment.from_wav(wav_path)
    audio.export(mp3_path, format="mp3")


def transcribe_and_save(audio_np, index):
    wav_file = f"{OUTPUT_FOLDER}/recording_{index}.wav"
    mp3_file = f"{OUTPUT_FOLDER}/recording_{index}.mp3"

    # Save WAV + MP3
    save_wav(audio_np, wav_file)
    save_mp3(wav_file, mp3_file)

    print(f"💾 Saved block {index} -> {mp3_file}")

    # Run Whisper transcription
    segments, _ = model.transcribe(wav_file)
    transcript = " ".join([seg.text for seg in segments])
    print(f"📝 Transcription {index}: {transcript}")


if __name__ == "__main__":
    import os
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    block_index = 1
    while True:
        audio_block = record_block()

        # Start transcription in background
        threading.Thread(target=transcribe_and_save, args=(audio_block, block_index)).start()

        block_index += 1
