from mutagen.mp3 import MP3
from mutagen.wave import WAVE


def get_audio_duration(file_path: str) -> float:
    """Get the duration of an audio file in seconds."""
    try:
        if file_path.lower().endswith('.mp3'):
            audio = MP3(file_path)
        elif file_path.lower().endswith('.wav'):
            audio = WAVE(file_path)
        else:
            raise ValueError("Unsupported audio format")
        return audio.info.length
    except Exception as e:
        raise ValueError(f"Error processing audio file: {str(e)}")