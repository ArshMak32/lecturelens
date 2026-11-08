# LectureLens model and testing boundary

## Speech model
Pretrained Whisper via SYSTRAN faster-whisper / CTranslate2, CPU int8. Supported English models: tiny.en, base.en, small.en. Defaults to tiny.en; models are downloaded separately. No speech model training is claimed.

## Downstream study features
TF-IDF lexical retrieval and centrality/diversity selection produce exact segment excerpts. Cloze generation blanks a source phrase and stores that phrase as the answer. These methods do not generate a conceptual explanation, validate factual truth or estimate exam relevance. Literal source grounding prevents fabricated quote spans but cannot correct an ASR error.

## Actual smoke test
Transcribed the 11-second JFK test clip from the OpenAI Whisper repository through the app's transcription function. Normalized word error rate was 0.0 for that one clip and reference, with two non-overlapping timestamped segments. This is a narrow successful smoke test, not a 100% transcription accuracy claim. Short clean speech is not representative of long noisy lectures, accents, equations or technical language. The audio is not included in the distribution; source and checksum are in reports/asr_smoke.json.

## Quality controls
Pydantic validates unique IDs, ordered non-overlapping finite intervals and nonblank text. Corrections are saved to session state and exported explicitly. ASR log-score flags are heuristic only. No diarization/speaker labels, translation, speaker identification or emotion inference is implemented. Review important material against the recording.

## Privacy and operational limits
Temporary audio files are deleted after inference. Session bytes and transcripts remain in application memory and exports remain wherever the user saves them. No hosted inference or analytics call is added; model files download from upstream sources. This is a local single-user tool without authentication, tenancy, production retention controls or measured long-recording throughput. Only process recordings you are authorized to use.
