import unittest
from pathlib import Path
from lecturelens.core import (
    Transcript,
    Segment,
    from_srt,
    subtitles,
    search,
    notes,
    cards,
    word_error_rate,
    card_csv,
)

ROOT = Path(__file__).resolve().parents[1]


class TranscriptTests(unittest.TestCase):
    def setUp(self):
        self.t = Transcript.model_validate_json(
            (ROOT / "data/demo_transcript.json").read_text()
        )

    def test_timestamp_roundtrip(self):
        parsed = from_srt(subtitles(self.t))
        self.assertEqual(len(parsed.segments), len(self.t.segments))
        self.assertAlmostEqual(parsed.segments[0].start, self.t.segments[0].start)

    def test_vtt_roundtrip(self):
        self.assertEqual(
            len(from_srt(subtitles(self.t, True)).segments), len(self.t.segments)
        )

    def test_search_returns_source(self):
        results = search(self.t, "recall")
        self.assertTrue(results)
        self.assertTrue(any("Recall is" in x["quote"] for x in results))

    def test_notes_are_exact_sources(self):
        source = {s.id: s.text for s in self.t.segments}
        self.assertTrue(
            all(n["quote"] == source[n["segment_id"]] for n in notes(self.t))
        )

    def test_cards_are_grounded_spans(self):
        rows = cards(self.t)
        self.assertTrue(rows)
        self.assertTrue(
            all(
                c["answer"] in c["source_quote"] and "_____" in c["question"]
                for c in rows
            )
        )

    def test_overlapping_rejected(self):
        with self.assertRaises(ValueError):
            Transcript(
                title="x",
                segments=[
                    Segment(id="a", start=0, end=4, text="one"),
                    Segment(id="b", start=3, end=5, text="two"),
                ],
            )

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            Transcript(
                title="x",
                segments=[
                    Segment(id="a", start=0, end=1, text="one"),
                    Segment(id="a", start=1, end=2, text="two"),
                ],
            )

    def test_invalid_interval_rejected(self):
        with self.assertRaises(ValueError):
            Segment(id="a", start=2, end=1, text="bad")

    def test_wer(self):
        self.assertEqual(word_error_rate("hello world", "Hello world!"), 0)
        self.assertEqual(word_error_rate("hello world", "hello there"), 0.5)

    def test_csv_formula_escaped(self):
        row = {
            "question": "=evil",
            "answer": "safe",
            "segment_id": "x",
            "start": 0,
            "end": 1,
            "source_quote": "safe",
        }
        self.assertIn("'=evil", card_csv([row]))
