# Voice Separation Web Application

A web application that separates vocals from music tracks using AI-powered audio processing.
test from sim dev

## Features

- Upload audio files (MP3, WAV)
- Separate vocals from music
- Download separated audio tracks
- Real-time processing status
- Modern and responsive UI

## Technology Stack

- Backend: Python 3.9
- Web Framework: Flask 3.1.1
- Audio Processing: Spleeter 2.4.0, demucs v4 (https://github.com/facebookresearch/demucs.git  commit e976d93)

- Frontend: HTML5, CSS3, JavaScript
- Audio Processing Libraries: librosa, soundfile
- Deep Learning: PyTorch, torchaudio

## Setup Instructions

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Project Structure

```
voice_separation_app/
├── app.py              # Main Flask application
├── requirements.txt    # Project dependencies
├── static/            # Static files (CSS, JS, uploads)
│   ├── css/
│   ├── js/
│   └── uploads/
├── templates/         # HTML templates
└── utils/            # Utility functions
    └── audio_processor.py
```

## API Endpoints

- `GET /`: Home page
- `POST /upload`: Upload audio file
- `POST /process`: Process audio file
- `GET /download/<filename>`: Download processed file

## Model Details

The application uses Spleeter, a pre-trained deep learning model for audio source separation. It can separate:
- Vocals
- Accompaniment (music)

## License

MIT License 