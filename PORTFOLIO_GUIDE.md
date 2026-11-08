# Presenting lecturelens

## Title
LectureLens — Local Speech-to-Study Assistant

## Description
Developed a local application that transcribes English recordings with Whisper and connects transcript search, extractive notes and fill-in-the-blank practice cards to source timestamps. Added editable human review and JSON/SRT/WebVTT/Markdown/CSV exports. Exercised actual speech inference on a short public clip and tested transcript, grounding and export behavior.

Use the description after running and understanding the app. Do not claim training the pretrained model, company deployment, measured cost/time savings, or benchmark accuracy that was not measured. These are working prototypes with explicit limitations. The implementation was created with AI assistance; state your own contribution accurately and use actual project dates.

## GitHub
Create an empty repository named `lecturelens`. In this folder:
```bash
git init
git add .
git status
```
Review staged files. Exclude `.venv`, caches, private recordings/photos, credentials and local exports. Keep source attribution, source metadata, tests and reports. Then:
```bash
git commit -m "Build evaluated local AI workflow"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/lecturelens.git
git push -u origin main
```
Replace YOUR_USERNAME and authenticate with GitHub's supported flow. Do not force-push over existing work. Choose a code license before inviting reuse, keeping upstream model/data terms separate.

## Interview preparation
Explain the user problem, actual model, preprocessing, evaluation boundary, false positives/recognition errors, human review and one improvement you personally made. Show source-linked evidence and a failure rather than claiming perfect automation. Add screenshots only after capturing the actual app.
