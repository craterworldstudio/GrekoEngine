import subprocess
import tempfile
import librosa
import numpy as np
import sys
import os

FRAME_LENGTH = 2048
HOP_LENGTH = 512
ENERGY_THRESHOLD = 0.01


def decode_adts_to_wav(adts_path):
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_wav.close()

    cmd = [
        "ffmpeg",
        "-y",
        "-i", adts_path,
        "-ac", "1",          # mono
        "-ar", "16000",      # 16kHz
        temp_wav.name
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return temp_wav.name


def detect_vowel(y, sr):
    spectrum = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), 1/sr)
    peak_freq = freqs[np.argmax(spectrum)]

    if 200 <= peak_freq < 400:
        return "A"
    elif 400 <= peak_freq < 600:
        return "E"
    elif 600 <= peak_freq < 800:
        return "I"
    elif 800 <= peak_freq < 1000:
        return "O"
    else:
        return "U"


def extract_gpseq(audio_path):
    y, sr = librosa.load(audio_path, sr=None)

    energies = librosa.feature.rms(
        y=y,
        frame_length=FRAME_LENGTH,
        hop_length=HOP_LENGTH
    )[0]

    times = librosa.frames_to_time(
        np.arange(len(energies)),
        sr=sr,
        hop_length=HOP_LENGTH
    )

    events = []
    current_label = None
    start_time = 0

    for i, energy in enumerate(energies):
        if energy < ENERGY_THRESHOLD:
            label = "REST"
        else:
            frame_start = int(i * HOP_LENGTH)
            frame_end = frame_start + FRAME_LENGTH
            segment = y[frame_start:frame_end]
            label = detect_vowel(segment, sr)

        if current_label is None:
            current_label = label
            start_time = times[i]
        elif label != current_label:
            duration = times[i] - start_time
            events.append((current_label, duration))
            current_label = label
            start_time = times[i]

    if current_label is not None:
        duration = times[-1] - start_time
        events.append((current_label, duration))

    return events


def write_gpseq(events, filename="test.gpseq"):
    with open(f".\\GEN_PHENOME_SEQ\\{filename}", "w") as f:
        f.write("# GPSEQ v1\n")
        for label, duration in events:
            f.write(f"{label} {duration:.2f};\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python gpseq_from_adts.py input.aac")
        return

    adts_path = sys.argv[1]

    print("Decoding ADTS → WAV...")
    wav_path = decode_adts_to_wav(adts_path)

    print("Extracting GPSEQ...")
    events = extract_gpseq(wav_path)

    write_gpseq(events)

    os.remove(wav_path)

    print("Done → output.gpseq")


if __name__ == "__main__":
    main()

