# ✨ Career Day — AI Career Visualiser

**Live:** https://cosmos-career-visualizer.vercel.app

> *"What do you want to be when you grow up?"*  
> Now you can actually **see it** — in seconds.

Career Day is a fun, interactive AI experience built for students. Speak your dream career into the mic, strike a pose for the webcam, and watch an AI transform your photo into a realistic image of your future self — as an astronaut, chef, surgeon, marine biologist, or anything in between.

---

## How It Works

```
You say "astronaut"
        ↓
Cosmo the wizard snaps your photo
        ↓
AI generates YOU in that career
        ↓
🎉 Confetti
```

1. **Cosmo** (an animated wizard avatar) greets you and asks what you want to be
2. You answer by voice — or type it in
3. A 3… 2… 1… countdown snaps your webcam photo
4. The AI generates a photorealistic image of **your face** in that career
5. Confetti, a reveal animation, and Cosmo's reaction

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla JS, HTML, Tailwind CSS |
| Avatar | Lottie animation |
| Voice input | Web Speech Recognition API (built into Chrome) |
| Voice output | Web Speech Synthesis API (built into Chrome) |
| AI image gen | [fal.ai](https://fal.ai) — `flux-pulid` (face-preserving) |
| Backend | Python + Flask |
| Hosting | Vercel (frontend) + Railway (backend) |

---

## Running Locally

**Prerequisites:** Python 3.9+, a [fal.ai](https://fal.ai) API key, a webcam

```bash
git clone https://github.com/joelcpy/career-visualizer.git
cd careerday

pip install -r requirements.txt

cp .env.example .env
# add your FAL_KEY to .env

python server.py
# open http://localhost:5001
```

---

## Deploying

Everything runs on **Vercel** — one platform, free forever.

1. Import your repo at [vercel.com](https://vercel.com) → **Add New Project**
2. Set Framework to **Other**
3. Add `FAL_KEY` as an Environment Variable
4. Click **Deploy**

The frontend is served as static files; `api/generate.py` runs as a serverless function at `/api/generate`.

---

## Features

- Voice recognition with graceful text fallback
- Fantasy careers remapped to real-world equivalents (say "wizard" → science professor)
- Content moderation to block inappropriate inputs
- Countdown timer, white flash, and snap animation
- Spell-casting sparkle effects while the AI generates
- Flip reveal + confetti when the result arrives
- Works on any device with a webcam and Chrome

---

## Built With

This project was built as a **vibe-coding demo** for Career Day — showing students that with a bit of creativity and modern AI tools, you can build something genuinely magical in an afternoon.

Feel free to fork it, remix it, and make it your own.

---

## Environment Variables

| Variable | Description |
|---|---|
| `FAL_KEY` | Your fal.ai API key — get one free at [fal.ai](https://fal.ai) |

Never commit your `.env` file. It's in `.gitignore` by default.
