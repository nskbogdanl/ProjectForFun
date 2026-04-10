# ProjectForFun

A real-time offline speech recognition system with trigger-word detection.  
When a trigger word is detected, the program saves surrounding speech context to a file.

---

## Features
- Real-time microphone speech recognition
- Trigger-word detection in live audio stream
- Pre-buffer + post-buffer context saving
- Automatic transcription saving to file
- Fully offline (Vosk-based)
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
├── Code.py
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

Inside "Code.py":
```
SizeOfModel = 0  # 0 = Russian model, 1 = English model  
TRIGGER_WORD = "Стоп"  
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
Code.py
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
GitHub: [ProjectForFun](https://github.com/nskbogdanl/ProjectForFun)

---

## Notes
- Fully offline after model download
- Accuracy depends on microphone, environment noise and size of the model
