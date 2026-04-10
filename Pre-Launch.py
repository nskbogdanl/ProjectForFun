import queue
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from datetime import datetime
import threading
from collections import deque

# Configuration
SizeOfModel = 0  # 0 - russian model, 1 - english model
ModelPath = r'D:\Programms\Code\ProjectForFun\VoskModel\\' + ("small-en" if SizeOfModel == 1 else "small-ru")
TRIGGER_WORD = "Стоп/Stop"  # Trigger word
RECORD_DURATION = 10  # Time after trigger word (seconds)
BUFFER_DURATION = 10  # Time before trigger word (seconds)
OUTPUT_FILE = "D:\\Programms\\Code\\ProjectForFun\\Results\\transcriptions.txt"


# Initialize model
model = Model(ModelPath)
rec = KaldiRecognizer(model, 16000)
rec.SetWords(True)

q = queue.Queue()
recording_mode = False
recording_buffer = []
recording_start_time = None
stop_flag = threading.Event()
last_partial = ""

# Circular buffer to store the last 10 seconds
pre_trigger_buffer = deque(maxlen=100)  # 100 chunks of 0.1 seconds

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

def save_to_file(timestamp, text):
    """Save transcription to file with timestamp"""
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {text}\n")
    print(f"✓ Saved to {OUTPUT_FILE}: {text}")

def check_for_exit():
    """Background thread to listen for exit command"""
    while not stop_flag.is_set():
        user_input = input()
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("\nExiting...")
            stop_flag.set()
            break

print(f" Listening for: '{TRIGGER_WORD}'")
print("Type 'exit', 'quit', or 'q' and press Enter to stop\n")

# Exit listener thread
exit_thread = threading.Thread(target=check_for_exit, daemon=True)
exit_thread.start()

try:
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        while not stop_flag.is_set():
            try:
                data = q.get(timeout=0.1)
            except queue.Empty:
                # Check recording timeout even when no audio data
                if recording_mode:
                    elapsed = (datetime.now() - recording_start_time).total_seconds()
                    if elapsed >= RECORD_DURATION:
                        # Save recording
                        full_text = ' '.join(recording_buffer).strip()
                        if full_text:
                            timestamp = recording_start_time.strftime("%Y-%m-%d %H:%M:%S")
                            save_to_file(timestamp, full_text)
                        
                        recording_mode = False
                        recording_buffer = []
                        recording_start_time = None
                        last_partial = ""
                        print(f"\n🎤 Listening for trigger word: '{TRIGGER_WORD}'\n")
                continue
            
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                text = res.get('text', '').strip()
                
                if not recording_mode:
                    # Add text to pre-trigger buffer with timestamp
                    if text:
                        pre_trigger_buffer.append((datetime.now(), text))
                    
                    # Check for trigger word
                    if TRIGGER_WORD.lower() in text.lower():
                        recording_mode = True
                        
                        current_time = datetime.now()
                        buffered_text = []
                        
                        for timestamp, buffered in pre_trigger_buffer:
                            time_diff = (current_time - timestamp).total_seconds()
                            if time_diff <= BUFFER_DURATION:
                                buffered_text.append(buffered)
                        
                        recording_buffer = buffered_text
                        recording_start_time = current_time
                        
                        print(f"\n🔴 TRIGGERED! Saving {BUFFER_DURATION}s before + {RECORD_DURATION}s after...")
                        print(f"  Before trigger: {' '.join(buffered_text)}")
                else:
                    # Save recognized text
                    if text:
                        recording_buffer.append(text)
                        print(f"  {text}")
                    last_partial = ""
            
            else:
                # Partial results
                res = json.loads(rec.PartialResult())
                partial = res.get('partial', '').strip()
                
                if not recording_mode:
                    # Monitor partial results for trigger word
                    if partial and TRIGGER_WORD.lower() in partial.lower():
                        recording_mode = True
                        
                        current_time = datetime.now()
                        buffered_text = []
                        
                        for timestamp, buffered in pre_trigger_buffer:
                            time_diff = (current_time - timestamp).total_seconds()
                            if time_diff <= BUFFER_DURATION:
                                buffered_text.append(buffered)
                        
                        buffered_text.append(partial)
                        recording_buffer = buffered_text
                        recording_start_time = current_time
                        
                        print(f"\n🔴 TRIGGERED! Saving {BUFFER_DURATION}s before + {RECORD_DURATION}s after...")
                        print(f"  Before trigger: {' '.join(buffered_text)}")
                        last_partial = partial
                elif partial and partial != last_partial:
                    # Show partial results during recording
                    print(f"  ...{partial}", end='\r')
                    last_partial = partial
            
            # Check recording timeout
            if recording_mode:
                elapsed = (datetime.now() - recording_start_time).total_seconds()
                if elapsed >= RECORD_DURATION:
                    # Add last partial result if needed
                    if last_partial and last_partial not in ' '.join(recording_buffer):
                        recording_buffer.append(last_partial)
                    
                    # Save everything
                    full_text = ' '.join(recording_buffer).strip()
                    if full_text:
                        timestamp = recording_start_time.strftime("%Y-%m-%d %H:%M:%S")
                        save_to_file(timestamp, full_text)
                    
                    recording_mode = False
                    recording_buffer = []
                    recording_start_time = None
                    last_partial = ""
                    print(f"\n🎤 Listening for trigger word: '{TRIGGER_WORD}'\n")

except KeyboardInterrupt:
    print("\n\nStopped by Ctrl+C")
finally:
    # Save any ongoing recording
    if recording_mode and recording_buffer:
        if last_partial and last_partial not in ' '.join(recording_buffer):
            recording_buffer.append(last_partial)
        full_text = ' '.join(recording_buffer).strip()
        if full_text:
            timestamp = recording_start_time.strftime("%Y-%m-%d %H:%M:%S")
            save_to_file(timestamp, full_text)
    print("Program ended.")