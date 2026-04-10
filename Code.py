import queue
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from datetime import datetime
import threading
from collections import deque
from pathlib import Path
import time

# ======================
# CONFIG
# ======================
SizeOfModel = 0  # 0 - russian, 1 - english
TRIGGER_WORD = "Стоп"
RECORD_DURATION = 10
BUFFER_DURATION = 10

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "VoskModel" / ("small-en" if SizeOfModel == 1 else "small-ru")
OUTPUT_FILE = BASE_DIR / "Results" / "transcriptions.txt"

print("Model path:", MODEL_PATH)

# ======================
# INIT VOSK
# ======================
model = Model(str(MODEL_PATH))
rec = KaldiRecognizer(model, 16000)
rec.SetWords(True)

# ======================
# GLOBAL STATE
# ======================
q = queue.Queue()

recording_mode = False
recording_buffer = []
recording_start_time = None
last_partial = ""

stop_flag = threading.Event()

pre_trigger_buffer = deque(maxlen=200)  # ~10 sec depending on chunk size
last_trigger_time = None
TRIGGER_COOLDOWN = 5  # seconds

# ======================
# AUDIO CALLBACK
# ======================
def callback(indata, frames, time_info, status):
    if status:
        print(status)
    q.put(bytes(indata))

# ======================
# FILE SAVE
# ======================
def save_to_file(timestamp, text):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {text}\n")

    print(f"\n✓ Saved: {text}\n")

# ======================
# EXIT THREAD
# ======================
def check_for_exit():
    while not stop_flag.is_set():
        cmd = input()
        if cmd.lower() in ["exit", "quit", "q"]:
            stop_flag.set()
            break

threading.Thread(target=check_for_exit, daemon=True).start()

# ======================
# MAIN LOOP
# ======================
print(f"Listening for trigger: '{TRIGGER_WORD}'\n")

try:
    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=callback
    ):

        while not stop_flag.is_set():

            # ======================
            # GET AUDIO DATA
            # ======================
            try:
                data = q.get(timeout=0.1)
            except queue.Empty:
                data = None

            if data:
                is_final = rec.AcceptWaveform(data)

                # ======================
                # FINAL RESULT
                # ======================
                if is_final:
                    res = json.loads(rec.Result())
                    text = res.get("text", "").strip()

                    if text:
                        now = datetime.now()

                        if not recording_mode:
                            pre_trigger_buffer.append((now, text))

                            # trigger check
                            if TRIGGER_WORD.lower() in text.lower():
                                if last_trigger_time is None or (now - last_trigger_time).total_seconds() > TRIGGER_COOLDOWN:

                                    recording_mode = True
                                    recording_start_time = now
                                    last_trigger_time = now

                                    # collect pre-buffer
                                    buffered_text = [
                                        t for ts, t in pre_trigger_buffer
                                        if (now - ts).total_seconds() <= BUFFER_DURATION
                                    ]

                                    recording_buffer = buffered_text

                                    print("\n🔴 TRIGGERED")
                                    print("Before:", " ".join(buffered_text))

                        else:
                            recording_buffer.append(text)
                            print(" ", text)

                # ======================
                # PARTIAL RESULT
                # ======================
                else:
                    res = json.loads(rec.PartialResult())
                    partial = res.get("partial", "").strip()

                    if not recording_mode:
                        if partial and TRIGGER_WORD.lower() in partial.lower():
                            now = datetime.now()

                            if last_trigger_time is None or (now - last_trigger_time).total_seconds() > TRIGGER_COOLDOWN:

                                recording_mode = True
                                recording_start_time = now
                                last_trigger_time = now

                                buffered_text = [
                                    t for ts, t in pre_trigger_buffer
                                    if (now - ts).total_seconds() <= BUFFER_DURATION
                                ]

                                buffered_text.append(partial)
                                recording_buffer = buffered_text

                                print("\n🔴 TRIGGERED (partial)")
                                print("Before:", " ".join(buffered_text))

                    elif partial and partial != last_partial:
                        print("..." + partial, end="\r")
                        last_partial = partial

            # ======================
            # STOP RECORDING
            # ======================
            if recording_mode and recording_start_time:
                elapsed = (datetime.now() - recording_start_time).total_seconds()

                if elapsed >= RECORD_DURATION:
                    full_text = " ".join(recording_buffer).strip()

                    if full_text:
                        timestamp = recording_start_time.strftime("%Y-%m-%d %H:%M:%S")
                        save_to_file(timestamp, full_text)

                    # reset
                    recording_mode = False
                    recording_buffer = []
                    recording_start_time = None
                    last_partial = ""

                    print(f"\n🎤 Listening again for '{TRIGGER_WORD}'\n")

except KeyboardInterrupt:
    print("\nStopped by user")

finally:
    if recording_mode and recording_buffer:
        full_text = " ".join(recording_buffer).strip()
        if full_text:
            timestamp = recording_start_time.strftime("%Y-%m-%d %H:%M:%S")
            save_to_file(timestamp, full_text)

    print("Program ended.")