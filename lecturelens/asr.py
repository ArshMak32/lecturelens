"""CPU Whisper inference. No hosted transcription service."""

from functools import lru_cache
from pathlib import Path
import tempfile
import os
from lecturelens.core import Transcript, Segment


@lru_cache(maxsize=2)
def model(size="tiny.en"):
    if size not in {"tiny.en", "base.en", "small.en"}:
        raise ValueError("Unsupported model size")
    from faster_whisper import WhisperModel

    return WhisperModel(
        size,
        device="cpu",
        compute_type="int8",
        cpu_threads=2,
        download_root=os.environ.get("LECTURELENS_MODEL_CACHE"),
    )


def transcribe(data, suffix=".wav", size="tiny.en", title="Lecture recording"):
    if not 0 < len(data) <= 100 * 1024 * 1024:
        raise ValueError("Audio must be 1 byte to 100 MB")
    if suffix.lower() not in {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".mp4"}:
        raise ValueError("Unsupported audio format")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / ("recording" + suffix.lower())
        path.write_bytes(data)
        from faster_whisper.audio import decode_audio

        audio = decode_audio(str(path), sampling_rate=16000)
        if len(audio) > 16000 * 90 * 60:
            raise ValueError("Limit: 90 minutes of audio")
        if len(audio) < 8000:
            raise ValueError("Recording is too short")
        generated, info = model(size).transcribe(
            audio,
            language="en",
            beam_size=5,
            vad_filter=True,
            word_timestamps=True,
            condition_on_previous_text=False,
        )
        result = []
        for s in generated:
            text = s.text.strip()
            if text and s.end > s.start:
                result.append(
                    Segment(
                        id=f"s{len(result) + 1:04}",
                        start=max(0, s.start),
                        end=s.end,
                        text=text,
                        avg_logprob=s.avg_logprob,
                    )
                )
        if not result:
            raise ValueError("No speech detected; try clearer audio")
        return Transcript(
            title=title,
            source="whisper_" + size,
            language=info.language,
            segments=result,
        )
