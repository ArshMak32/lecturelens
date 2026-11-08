# Run LectureLens

Move `lecturelens` to Desktop. Stop any current app with Control+C, then:
```bash
cd ~/Desktop/lecturelens
bash run.sh
```
Open http://localhost:8507 . Python 3.11/3.12 recommended. No API key needed.

The first screen contains an authored example transcript. Try transcript search, study notes and practice cards immediately. To use actual speech AI, upload your own permitted English recording and click Transcribe recording in the sidebar. First use downloads a Whisper model. Keep tiny.en initially; larger models take more time.

After transcription, check the recording, correct important terms and save corrections before exporting. The notes and fill-in-the-blank answers come from the transcript and inherit its errors.

Screenshots:
1. Your permitted recording's transcript/search results with timestamps.
2. Notes and cards with source references.
3. Correction view showing human review.

If using the included demo for screenshots, retain the Authored transcript demo label. Do not present it as recognized speech or claim a general transcription accuracy score.

Manual start:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.port 8507
```
