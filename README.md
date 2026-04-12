# Wakeword Speech Transcriber

A real-time offline speech recognition system based on Vosk with wake-word detection.

When a trigger word is detected, the system captures surrounding speech context (before and after the event) and saves it as a structured transcription log.

---

## Features
- Real-time audio stream processing
- Wake-word / trigger-word detection
- Pre-trigger and post-trigger audio buffering
- Offline speech recognition (no internet required)
- Automatic structured transcription logging
---

## Tech Stack
- Python 3.10+
- Vosk (offline speech recognition)
- sounddevice (audio stream input)
- JSON parsing for recognition results

---

## Project Structure

```
.
│
├── main.py
│
├── STL/
│   └── *.stl (parts for 3D-printing)
│
├── VoskModel/
│   ├── small-en/
│   └── small-ru/
│
├── Results/
│   └── transcriptions.txt
│
└── README.md
```
---

## Configuration

Inside "main.py":
```
SizeOfModel = 0  # 0 = Russian model, 1 = English model  
TRIGGER_WORD = "Стоп"  # or other word
RECORD_DURATION = 10  # seconds after trigger  
BUFFER_DURATION = 10  # seconds before trigger  
```
---

## Installation

```bash
pip install vosk sounddevice
```

---

## Usage

1. Run the program:
```
main.py
```
2. Speak into microphone
3. Say trigger word (example: "Стоп")
4. Program will:
   - save previous speech (buffer)
   - record triggered speech
   - save following speech
   - write everything to file

---

## Output

Results are saved in:
```
Results/transcriptions.txt
```
Format:
```
[YYYY-MM-DD HH:MM:SS] recognized speech text
```
---

## How it works
- Microphone audio is streamed in real time
- Vosk converts speech to text (final + partial results)
- Program continuously checks for trigger word
- When detected:
  - recording mode starts
  - previous buffer is added
  - speech is recorded for fixed time
  - result is saved to file
- Exit possible via terminal command: 
```
q
```

---

## Author

Bogdan Lomp  
GitHub: [Wakeword-speech-transcriber](https://github.com/nskbogdanl/Wakeword-speech-transcriber)

---

## Notes
- Fully offline after model download
- Accuracy depends on microphone, environment noise and size of the model
