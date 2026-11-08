# LectureLens attribution

Speech engine: SYSTRAN faster-whisper, https://github.com/SYSTRAN/faster-whisper . Pretrained Whisper model family: OpenAI Whisper, https://github.com/openai/whisper . CTranslate2 model distribution for tiny.en: https://huggingface.co/Systran/faster-whisper-tiny.en . Review upstream model/software licenses before redistribution. No model weights are included here.

Actual audio smoke test: https://raw.githubusercontent.com/openai/whisper/main/tests/jfk.flac . It contains an excerpt from John F. Kennedy's inaugural address. The audio is downloaded only for local verification, not distributed in this package. Source, SHA-256, reference, output and testing scope are in reports/asr_smoke.json. It is not a lecture benchmark.

The machine-learning transcript demo and illustrative timestamps in data/demo_transcript.json were authored for this project. They are not actual ASR output and contain no private recording. The UI labels this distinction. Code unit tests use this authored fixture for deterministic transcript/search/export checks.
