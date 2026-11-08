"""Timestamped transcript validation, local search, extractive notes and cloze cards."""

from hashlib import sha256
import re, csv, io
import numpy as np
from pydantic import BaseModel, Field, model_validator
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Segment(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    text: str = Field(min_length=1, max_length=10000)
    reviewed: bool = False
    avg_logprob: float | None = None

    @model_validator(mode="after")
    def duration(self):
        if (
            not np.isfinite(self.start)
            or not np.isfinite(self.end)
            or self.end <= self.start
        ):
            raise ValueError("Segment interval must be finite and positive")
        if not self.text.strip():
            raise ValueError("Segment text cannot be blank")
        return self


class Transcript(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    source: str = "uploaded"
    language: str = "en"
    segments: list[Segment] = Field(min_length=1, max_length=5000)

    @model_validator(mode="after")
    def ordered(self):
        if len({s.id for s in self.segments}) != len(self.segments):
            raise ValueError("Segment IDs must be unique")
        if any(
            b.start < a.end - 0.01 for a, b in zip(self.segments, self.segments[1:])
        ):
            raise ValueError("Segments must be ordered and non-overlapping")
        return self

    @property
    def digest(self):
        return sha256(self.model_dump_json().encode()).hexdigest()


def stamp(seconds, separator="."):
    ms = round(seconds * 1000)
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02}{separator}{ms:03}"


def subtitles(transcript, vtt=False):
    lines = ["WEBVTT", ""] if vtt else []
    for i, s in enumerate(transcript.segments, 1):
        lines.extend(
            [
                str(i),
                f"{stamp(s.start, '.' if vtt else ',')} --> {stamp(s.end, '.' if vtt else ',')}",
                s.text,
                "",
            ]
        )
    return "\n".join(lines)


def from_srt(text, title="Imported subtitles"):
    if text.lstrip().startswith("WEBVTT"):
        text = text.lstrip()[6:]
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip())
    segments = []
    pattern = re.compile(r"(?:(\d+):)?(\d{2}):(\d{2})[.,](\d{3})")

    def seconds(x):
        m = pattern.search(x)
        if not m:
            raise ValueError("Invalid subtitle timestamp")
        h, mi, se, ms = m.groups()
        return int(h or 0) * 3600 + int(mi) * 60 + int(se) + int(ms) / 1000

    for block in blocks:
        lines = block.splitlines()
        idx = next((i for i, x in enumerate(lines) if "-->" in x), None)
        if idx is None:
            continue
        a, b = lines[idx].split("-->", 1)
        body = " ".join(lines[idx + 1 :]).strip()
        if body:
            segments.append(
                Segment(
                    id=f"s{len(segments) + 1:04}",
                    start=seconds(a),
                    end=seconds(b),
                    text=body,
                )
            )
    return Transcript(title=title, source="imported_subtitles", segments=segments)


def index(transcript):
    texts = [s.text for s in transcript.segments]
    v = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    try:
        x = v.fit_transform(texts)
    except ValueError:
        v = TfidfVectorizer(analyzer="char", ngram_range=(2, 3))
        x = v.fit_transform(texts)
    return v, x


def search(transcript, query, k=5):
    if not query.strip():
        return []
    v, x = index(transcript)
    scores = (x @ v.transform([query]).T).toarray().ravel()
    order = np.argsort(-scores, kind="stable")[:k]
    return [
        {
            "segment_id": transcript.segments[i].id,
            "start": transcript.segments[i].start,
            "end": transcript.segments[i].end,
            "quote": transcript.segments[i].text,
            "score": float(scores[i]),
        }
        for i in order
        if scores[i] > 0
    ]


def notes(transcript, count=6):
    v, x = index(transcript)
    central = cosine_similarity(x, np.asarray(x.mean(axis=0))).ravel()
    similarity = (x @ x.T).toarray()
    selected = []
    for _ in range(min(count, len(transcript.segments))):
        values = [
            0.7 * central[i] - 0.3 * max([similarity[i, j] for j in selected] or [0])
            if i not in selected
            else -999
            for i in range(len(central))
        ]
        selected.append(int(np.argmax(values)))
    return [
        {
            "segment_id": transcript.segments[i].id,
            "start": transcript.segments[i].start,
            "end": transcript.segments[i].end,
            "quote": transcript.segments[i].text,
            "reviewed": transcript.segments[i].reviewed,
        }
        for i in sorted(selected)
    ]


def cards(transcript, count=10):
    v, x = index(transcript)
    terms = v.get_feature_names_out()
    out = []
    if v.analyzer == "char":
        return []
    for i, s in enumerate(transcript.segments):
        row = x[i].toarray().ravel()
        for j in np.argsort(-row):
            term = terms[j]
            if row[j] <= 0:
                break
            if len(term) < 5 or len(term.split()) > 2:
                continue
            match = re.search(r"\b" + re.escape(term) + r"\b", s.text, re.I)
            if match:
                answer = match.group()
                prompt = re.sub(
                    r"\b" + re.escape(term) + r"\b", "_____", s.text, flags=re.I
                )
                out.append(
                    {
                        "question": prompt,
                        "answer": answer,
                        "segment_id": s.id,
                        "start": s.start,
                        "end": s.end,
                        "source_quote": s.text,
                    }
                )
                break
        if len(out) >= count:
            break
    return out


def study_markdown(transcript, count=6):
    lines = [
        "# " + transcript.title,
        "",
        "Extractive study notes. Check transcription against the recording.",
        "",
    ]
    for n in notes(transcript, count):
        lines.append(
            f"- [{stamp(n['start'])}–{stamp(n['end'])}] {n['quote']} (source: {n['segment_id']})"
        )
    return "\n".join(lines) + "\n"


def card_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(
        buf,
        fieldnames=["question", "answer", "segment_id", "start", "end", "source_quote"],
    )
    w.writeheader()
    for r in rows:
        safe = {
            k: (
                "'" + v
                if isinstance(v, str) and v[:1] in {"=", "+", "-", "@", "\t", "\r"}
                else v
            )
            for k, v in r.items()
        }
        w.writerow(safe)
    return buf.getvalue()


def word_error_rate(reference, hypothesis):
    def words(t):
        return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", t.lower())

    a, b = words(reference), words(hypothesis)
    if not a:
        raise ValueError("Reference must contain words")
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        row = [i]
        for j, y in enumerate(b, 1):
            row.append(min(row[-1] + 1, previous[j] + 1, previous[j - 1] + (x != y)))
        previous = row
    return previous[-1] / len(a)
