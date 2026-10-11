# Demo video pipeline

Produces `docs/video/floodready-demo.mp4` (published at https://youtu.be/FJ9Uc15GI_A).

1. `seg2.py <ffmpeg>`: narration clips with ElevenLabs TTS (key read from the repo-root `.env`, never printed). Opening lines are in the script; app lines are in `app_segs.json`.
2. `rec.py`: Playwright records `slides.html` (animated, sourced stats) and the running app at `/?demo=1`, timed to each clip.
3. ffmpeg mixes the clips onto the recording at the logged marks (`adelay` + `amix`), with the voice sped up 1.15×.

Needs the backend on :8000 and the frontend on :5173.
