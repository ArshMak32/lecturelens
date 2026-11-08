from pathlib import Path
import json
import pandas as pd
import streamlit as st
from lecturelens.core import (
    Transcript,
    from_srt,
    search,
    notes,
    cards,
    study_markdown,
    subtitles,
    card_csv,
    stamp,
)
from lecturelens.asr import transcribe

ROOT = Path(__file__).resolve().parent
st.set_page_config(
    page_title="LectureLens | Listen, Find, Review", page_icon="🎧", layout="wide"
)
st.markdown(
    '<style>.block-container{max-width:1350px;padding-top:2rem}h1,h2,h3{letter-spacing:-.03em}div[data-testid="stMetric"]{border:1px solid #344264;border-radius:12px;padding:14px}</style>',
    unsafe_allow_html=True,
)
st.caption("LECTURELENS / LOCAL SPEECH AI + SOURCE-LINKED STUDY")
st.title("Find the moment. Learn the concept.")
st.write(
    "Turn a recording into a reviewable transcript, timestamped notes and source-linked practice cards."
)
if "transcript" not in st.session_state:
    st.session_state["transcript"] = json.loads(
        (ROOT / "data/demo_transcript.json").read_text()
    )
with st.sidebar:
    st.subheader("Bring your lecture")
    st.caption(
        "Use recordings you have permission to process. Files stay in this local app; do not deploy it publicly with private recordings."
    )
    audio = st.file_uploader(
        "Audio recording", type=["wav", "mp3", "m4a", "flac", "ogg", "mp4"]
    )
    size = st.selectbox("Local speech model", ["tiny.en", "base.en", "small.en"])
    st.caption(
        "First use downloads the selected Whisper model. Larger models are slower. English audio only in this version."
    )
    if st.button("Transcribe recording", type="primary"):
        if audio is None:
            st.error("Choose an audio file first")
        else:
            try:
                with st.spinner(
                    "Transcribing locally. Long recordings may take several minutes…"
                ):
                    t = transcribe(
                        audio.getvalue(),
                        Path(audio.name).suffix,
                        size,
                        Path(audio.name).stem,
                    )
                    st.session_state["transcript"] = t.model_dump(mode="json")
                    st.session_state["audio_bytes"] = audio.getvalue()
                    st.session_state["audio_mime"] = audio.type
                    st.success(
                        "Transcription ready. Review uncertain spans before studying."
                    )
            except Exception as exc:
                st.error(
                    "Transcription failed: "
                    + type(exc).__name__
                    + ". Check the file, model download and installed dependency versions."
                )
    upload = st.file_uploader(
        "Or import JSON/SRT/VTT transcript", type=["json", "srt", "vtt"]
    )
    if st.button("Import transcript"):
        try:
            if upload is None:
                raise ValueError("Choose a transcript")
            if upload.size > 5 * 1024 * 1024:
                raise ValueError("Transcript limit: 5 MB")
            text = upload.getvalue().decode("utf-8-sig")
            t = (
                Transcript.model_validate_json(text)
                if upload.name.endswith(".json")
                else from_srt(text, Path(upload.name).stem)
            )
            st.session_state["transcript"] = t.model_dump(mode="json")
            st.session_state.pop("audio_bytes", None)
            st.rerun()
        except Exception as exc:
            st.error("Transcript rejected: " + str(exc))
    if st.button("Load authored demo"):
        st.session_state["transcript"] = json.loads(
            (ROOT / "data/demo_transcript.json").read_text()
        )
        st.session_state.pop("audio_bytes", None)
        st.rerun()
t = Transcript.model_validate(st.session_state["transcript"])
if t.source == "authored_demo":
    st.info(
        "Authored transcript demo with illustrative timestamps. This is not output from a real lecture recording. Upload audio to exercise speech recognition."
    )
st.subheader(t.title)
a, b, c = st.columns(3)
a.metric("Transcript segments", len(t.segments))
b.metric("Timeline end", stamp(t.segments[-1].end))
c.metric("Human-reviewed spans", sum(s.reviewed for s in t.segments))
if "audio_bytes" in st.session_state:
    st.audio(st.session_state["audio_bytes"])
find, note_tab, quiz, edit, exports = st.tabs(
    ["Find a moment", "Study notes", "Practice cards", "Review transcript", "Export"]
)
with find:
    query = st.text_input("Search the transcript", "precision recall")
    results = search(t, query)
    if not results:
        st.info(
            "No matching transcript terms. Try wording from the lecture; search is lexical TF-IDF, not unrestricted question answering."
        )
    for r in results:
        with st.container(border=True):
            st.markdown("**" + stamp(r["start"]) + " → " + stamp(r["end"]) + "**")
            st.write(r["quote"])
            st.caption(
                "Source "
                + r["segment_id"]
                + " · lexical similarity "
                + f"{r['score']:.3f}"
            )
            if "audio_bytes" in st.session_state:
                st.audio(st.session_state["audio_bytes"], start_time=int(r["start"]))
with note_tab:
    count = st.slider(
        "Number of note excerpts", 1, min(20, len(t.segments)), min(6, len(t.segments))
    )
    st.caption(
        "Extractive centrality/diversity ranking selects exact transcript excerpts. It does not invent an explanation or verify the lecturer’s claims."
    )
    for n in notes(t, count):
        with st.container(border=True):
            st.write(n["quote"])
            st.caption(
                stamp(n["start"])
                + " · "
                + n["segment_id"]
                + " · "
                + ("reviewed" if n["reviewed"] else "not yet reviewed")
            )
    st.download_button(
        "Download timestamped notes",
        study_markdown(t, count),
        "study_notes.md",
        "text/markdown",
    )
with quiz:
    st.caption(
        "Fill-in-the-blank cards are generated from transcript phrases. Answers and source passages stay linked; they are not independently verified exam questions."
    )
    rows = cards(t)
    for i, card in enumerate(rows, 1):
        st.markdown("**" + str(i) + ". " + card["question"] + "**")
        with st.expander("Show answer and source"):
            st.write(card["answer"])
            st.write(card["source_quote"])
            st.caption(card["segment_id"] + " · " + stamp(card["start"]))
    if rows:
        st.download_button(
            "Export practice cards CSV",
            card_csv(rows),
            "practice_cards.csv",
            "text/csv",
        )
with edit:
    st.caption(
        "Check the recording, correct words, and mark reviewed. Timestamp edits must remain ordered and non-overlapping."
    )
    df = pd.DataFrame([s.model_dump() for s in t.segments])
    changed = st.data_editor(
        df,
        hide_index=True,
        disabled=["id", "avg_logprob"],
        num_rows="fixed",
        key="transcript_editor_" + t.digest,
    )
    if st.button("Save transcript corrections"):
        try:
            corrected = Transcript(
                title=t.title,
                source=t.source,
                language=t.language,
                segments=changed.to_dict(orient="records"),
            )
            st.session_state["transcript"] = corrected.model_dump(mode="json")
            st.rerun()
        except Exception as exc:
            st.error("Corrections rejected: " + str(exc))
    uncertain = [
        s
        for s in t.segments
        if not s.reviewed and s.avg_logprob is not None and s.avg_logprob < -0.65
    ]
    st.write(
        "Unreviewed spans below the heuristic ASR log-score cutoff:", len(uncertain)
    )
    st.caption(
        "ASR log scores are not word accuracy or a reliable error detector. All unreviewed spans may contain errors."
    )
with exports:
    st.download_button(
        "Transcript JSON",
        t.model_dump_json(indent=2),
        "transcript.json",
        "application/json",
    )
    st.download_button("Subtitles SRT", subtitles(t), "transcript.srt", "text/plain")
    st.download_button(
        "Captions WebVTT", subtitles(t, True), "transcript.vtt", "text/vtt"
    )
    st.download_button(
        "Study packet Markdown", study_markdown(t), "study_packet.md", "text/markdown"
    )
    st.caption(
        "Exports reflect your current corrections. Transcript text can contain personal information; review before sharing."
    )
st.divider()
st.caption(
    "Local research prototype. No speaker diarization, translation, OCR, generative explanation or guaranteed transcription accuracy. Audio is kept in session memory; temporary inference files are removed after processing."
)
