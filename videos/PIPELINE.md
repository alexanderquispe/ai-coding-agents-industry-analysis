# Video Production Pipeline — From HTML Animations to Social-Media-Ready MP4

> **Project:** AI Coding Agents Industry Analysis
> **Author:** Alexander Quispe
> **Last updated:** April 2026
> **Purpose:** Complete reference document for replicating the video production pipeline used to generate 12 social-media videos from the project's data.

This document explains, end-to-end, how a folder of static HTML files was turned into polished, square-format MP4 videos with a synchronized soundtrack — using nothing but a browser, a Python script, and FFmpeg. No video editor, no After Effects, no paid SaaS.

---

## 1. Why this approach?

We had a research dataset (AI coding agent adoption across NAICS industries) and wanted videos for LinkedIn / Twitter / Instagram. The constraints:

- **No video-editing skill required.** Building animations in the browser uses skills we already had (HTML/CSS/JS).
- **Reproducible.** Re-running the pipeline regenerates the same video. No "click here, drag this layer" handcraft.
- **Data-driven.** Numbers come from the dataset; if data changes, the video updates automatically.
- **Free tooling.** Browser + Playwright + FFmpeg — all open source.
- **Square format (1080×1080).** Optimized for social feed display.

The core idea: **build the animation as a self-playing webpage, then have a headless browser screen-record itself.**

---

## 2. Architecture at a glance

```
┌────────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  HTML/CSS/JS animation │ ──▶ │  Playwright browser  │ ──▶ │  WebM video file    │
│  (the "scene")         │     │  records itself      │     │  (silent)           │
└────────────────────────┘     └──────────────────────┘     └──────────┬──────────┘
                                                                       │
                                                                       ▼
                                                            ┌─────────────────────┐
                                                            │ FFmpeg merges       │
                                                            │ video + soundtrack  │
                                                            └──────────┬──────────┘
                                                                       │
                                                                       ▼
                                                            ┌─────────────────────┐
                                                            │  Final MP4          │
                                                            │  (1080×1080, AAC)   │
                                                            └─────────────────────┘
```

Three components:

1. **A self-playing HTML file.** It contains all the data, all the styling, all the slide-transition logic. Open it in a browser and it plays itself like a slideshow.
2. **A Python recording script (`record_video.py`).** It uses Playwright to launch a headless Chromium, navigate to the HTML file, and capture a screen recording for a fixed duration.
3. **An FFmpeg merge step.** The recorded video has no audio, so FFmpeg muxes in a separate `.mp3` soundtrack and re-encodes to MP4 (H.264 + AAC, `yuv420p` for universal compatibility).

---

## 3. Folder structure

```
videos/
├── PIPELINE.md                          ← this document
├── index.html                           ← gallery landing page (preview all 12 videos)
├── record_video.py                      ← the recording orchestrator
├── soundtrack.mp3                       ← background music (single track for all videos)
├── ai-coding-agents-video.webm          ← raw silent recording (intermediate)
├── ai-coding-agents-video.mp4           ← final output (video + audio)
│
├── video-01-timeline-story.html         ← 12 self-playing animation files
├── video-02-agent-battle.html
├── video-03-industry-deepdive.html
├── video-04-breaking-news.html
├── video-05-infographic.html
├── video-06-minimalist-apple.html
├── video-06-minimalist-apple-enhanced.html
├── video-06-minimalist-apple-full.html  ← the one currently wired into record_video.py
├── video-07-movie-trailer.html
├── video-08-data-journalist.html
├── video-09-stats-reveal.html
└── video-10-complete-story.html
```

---

## 4. The 12 video templates

Each `video-XX-*.html` file is an **independent, self-contained slideshow**. They share data but use very different visual styles, so we can pick the one that fits the platform/audience.

| # | File | Style | Duration | Slides | Best For |
|---|------|-------|----------|--------|----------|
| 01 | `video-01-timeline-story.html` | Animated timeline of 15-month adoption | ~52 s | 10 | Showing growth journey |
| 02 | `video-02-agent-battle.html` | Head-to-head VS-style comparison of 4 agents | ~47 s | 10 | Comparing competitors |
| 03 | `video-03-industry-deepdive.html` | Top 5 industries, NAICS breakdowns, use cases | ~57 s | 10 | Sector-level insight |
| 04 | `video-04-breaking-news.html` | News broadcast: tickers, lower thirds, headlines | ~36 s | 7 | Attention-grabbing |
| 05 | `video-05-infographic.html` | Data-rich cards, charts, statistics | ~34 s | 6 | Information density |
| 06 | `video-06-minimalist-apple.html` | Apple keynote-style, clean typography | ~40 s | 8 | Premium feel |
| 06b | `video-06-minimalist-apple-enhanced.html` | Apple style + animated top-8 industry distributions | ~49 s | 11 | Polished data story |
| 06c | `video-06-minimalist-apple-full.html` | Apple style + **all 19** NAICS industries | ~49 s | 10 | Most data-rich |
| 07 | `video-07-movie-trailer.html` | Quick cuts, big text slams, cinematic letterbox | ~35 s | 11 | Hype / launch teaser |
| 08 | `video-08-data-journalist.html` | Bloomberg/FT style, light background, serif | ~33 s | 6 | Professional / B2B |
| 09 | `video-09-stats-reveal.html` | One impactful stat per slide, dramatic reveals | ~41 s | 10 | Quick consumption |
| 10 | `video-10-complete-story.html` | Combines agents + industries + growth + findings | ~40 s | 7 | Best for LinkedIn |

The default in `record_video.py` is **video 06c (`video-06-minimalist-apple-full.html`)** because it shows the full data while keeping the Apple-style polish.

---

## 5. Anatomy of a self-playing HTML video

Each animation HTML file follows a strict, reusable structure. Once you understand one, you can author the others quickly.

### 5.1 Page setup (fixed-size canvas)

```html
<body style="width: 1080px; height: 1080px; overflow: hidden;">
```

The page is locked at exactly **1080×1080 pixels** — square format for social media. `overflow: hidden` prevents scrollbars. Match Playwright's viewport to this exact size.

Font from Google Fonts (Inter) keeps typography consistent across all 12 videos.

### 5.2 Slide structure

The whole presentation is a series of `<div class="slide">` elements stacked on top of each other (`position: absolute`). Only one is visible at a time:

```html
<div class="slide slide-1 active" data-duration="4500"> ... </div>
<div class="slide slide-2"        data-duration="5000"> ... </div>
<div class="slide slide-3"        data-duration="4500" data-agent="claude"> ... </div>
...
```

Two important attributes:

- **`data-duration`** (milliseconds) — how long the slide stays on screen before transitioning to the next one. Stored as a data attribute so the JS scheduler can read it.
- **`data-agent`** (optional) — triggers a per-agent animation routine when the slide becomes active. Used for the data-driven distribution slides.

The `.slide.active` class is what drives visibility:

```css
.slide        { opacity: 0; transition: opacity 1.2s ease; }
.slide.active { opacity: 1; }
```

This means transitions are pure CSS opacity fades — no JS animation library required.

### 5.3 Slide-internal animations

Within each slide, individual elements animate themselves on appearance using CSS keyframes with staggered `animation-delay`:

```css
.hero-text { opacity: 0; animation: fadeIn 1.5s ease forwards 0.3s; }
.sub-text  { opacity: 0; animation: fadeIn 1.5s ease forwards 0.8s; }
@keyframes fadeIn  { to { opacity: 1; } }
@keyframes scaleIn { from { transform: scale(0.5); opacity: 0; } to { transform: scale(1); opacity: 1; } }
```

The result is a "Ken Burns / Apple keynote" feel: text fades in 0.3 s after the slide appears, sub-text 0.5 s after that, etc.

### 5.4 The slideshow scheduler

A small JS routine at the bottom of every file walks through the slides:

```javascript
const slides   = document.querySelectorAll('.slide');
const progress = document.querySelector('.progress');
let current = 0;
let total   = Array.from(slides).reduce((a, s) => a + parseInt(s.dataset.duration), 0);
let elapsed = 0;

function next() {
  elapsed += parseInt(slides[current].dataset.duration);
  progress.style.width = `${(elapsed / total) * 100}%`;
  current++;
  if (current < slides.length) {
    slides.forEach(s => s.classList.remove('active'));
    slides[current].classList.add('active');

    // If the slide opts into data animation, kick it off
    const agentType = slides[current].dataset.agent;
    if (agentType) animateAgent(agentType);

    setTimeout(next, parseInt(slides[current].dataset.duration));
  }
}
setTimeout(next, parseInt(slides[0].dataset.duration));
```

How it works:
1. Calculate total duration by summing every `data-duration`.
2. Schedule the first transition with `setTimeout` based on slide 1's duration.
3. Each transition: deactivate all, activate the next, optionally fire a data animation, schedule the following transition.
4. The progress bar at the bottom of the screen advances as a percentage of total elapsed time.

### 5.5 Data-driven slides

The interesting slides aren't static — they animate **real data from the project**. The full Apple template (`video-06-minimalist-apple-full.html`) embeds the per-month, per-industry counts inline as JS objects:

```javascript
const claudeData = {
  '11': [0,12,41,56,100,370,802,1404,1922,2764,3660,4826,6626],   // Agriculture
  '21': [0,0,1,2,6,32,63,98,139,230,331,460,637],                  // Mining
  '22': [0,5,10,21,43,157,357,553,788,1115,1531,2053,2914],        // Utilities
  // ... 16 more NAICS sectors ...
};
```

Each value is the cumulative repository count for that industry × that month. When a slide marked `data-agent="claude"` becomes active, an animator function steps through the 13 months one at a time:

```javascript
function animateAgent(agent) {
  const config = agentConfigs[agent];
  let monthIndex = 0;
  const interval = 260; // ms per month tick

  function updateMonth() {
    if (monthIndex >= months.length) return;
    document.getElementById(config.monthEl).textContent = months[monthIndex];

    // Recompute bar widths and percentages for every NAICS industry
    industries.forEach(ind => {
      const value    = config.data[ind.code][monthIndex];
      const total    = sumOver(industries);
      const maxValue = Math.max(...Object.values(config.data).map(d => d[monthIndex]));
      document.getElementById(`${agent}-bar-${ind.code}`).style.width = `${(value / maxValue) * 100}%`;
      // update value labels and percentages...
    });

    monthIndex++;
    if (monthIndex < months.length) setTimeout(updateMonth, interval);
  }
  setTimeout(updateMonth, 400); // 400 ms warm-up after slide enters
}
```

The visual effect is **horizontal bar charts that grow in real time** as the months tick from Jan 2025 → Jan 2026. Because everything is timed in milliseconds and deterministic, the recording always captures the same animation.

### 5.6 Audio (optional, mostly unused)

The HTML files include a hidden `<audio>` tag and try to play it on load:

```javascript
const bgMusic = document.getElementById('bgMusic');
bgMusic.volume = 0.7;
bgMusic.play().catch(() => {}); // silent fail in headless mode
```

In practice, headless browsers block autoplay audio, so this fails silently and the recording is silent. The soundtrack is added later via FFmpeg (Section 6.3) — much more reliable.

---

## 6. The recording pipeline (`record_video.py`)

The Python script is short and does three things in sequence:

```
[1] Open HTML in headless Chromium  →  [2] Wait & record  →  [3] FFmpeg mux audio
```

### 6.1 Setup and configuration

```python
from playwright.sync_api import sync_playwright
import time, subprocess, os

html_file    = r"...\video-06-minimalist-apple-full.html"
output_video = r"...\ai-coding-agents-video.webm"   # silent intermediate
final_video  = r"...\ai-coding-agents-video.mp4"    # final with audio
audio_file   = r"...\soundtrack.mp3"
ffmpeg_path  = r"C:\Users\Alexander\Downloads\ffmpeg\...\ffmpeg.exe"
```

To switch which video gets recorded, change the `html_file` path. Everything else stays the same.

### 6.2 Compute total duration

The script needs to know how long to keep recording. Since slide durations are baked into the HTML, we **manually sum them** in a comment (kept in sync with the HTML) and add a 2-second buffer:

```python
# Slides: 4500 + 5000 + 4500 + 5500 + 5500 + 5500 + 5500 + 4500 + 4000 + 4500 = 49000ms
total_duration_ms  = 49000 + 2000    # 2 s buffer for the final slide to finish fading
total_duration_sec = total_duration_ms / 1000
```

> **Maintenance note for your cofounder:** If you change a `data-duration` in the HTML, update this sum. Or — better — add a small script that parses the HTML and computes the total automatically.

### 6.3 Headless recording with Playwright

```python
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1080, "height": 1080},
        record_video_dir=".",
        record_video_size={"width": 1080, "height": 1080}
    )
    page = context.new_page()
    page.goto(f"file:///{html_file}")
    time.sleep(total_duration_sec)   # let the slideshow play to the end
    page.close()
    context.close()
    browser.close()

    # Playwright stores the video at a temp path — move it to where we want
    video_path = page.video.path()
    os.rename(video_path, output_video)
```

Key choices:

- **`headless=True`** — no visible window. Faster, runs on a server, no risk of you accidentally moving the mouse over it.
- **`viewport=1080×1080`** matches `record_video_size` exactly so there's no scaling artifact.
- **`time.sleep(total_duration_sec)`** is the simple, robust way to wait. We don't need to listen for an event — we know exactly how long the slideshow runs.
- The video is saved as `.webm` (VP8/VP9). It is **silent** — Playwright captures pixels, not page audio.

### 6.4 FFmpeg: video + audio → MP4

The webm has no sound, so we mux in the soundtrack and re-encode to a universally compatible MP4:

```python
cmd = [
    ffmpeg_path,
    "-y",                  # overwrite output without asking
    "-i", output_video,    # input #0: silent webm
    "-i", audio_file,      # input #1: mp3 soundtrack
    "-c:v", "libx264",     # H.264 video codec
    "-c:a", "aac",         # AAC audio codec
    "-shortest",           # cut to the shortest stream (audio is ~3 minutes, video is 51 s)
    "-pix_fmt", "yuv420p", # critical: required for compatibility with social media players
    final_video
]
subprocess.run(cmd, check=True)
```

Why each flag matters:
- **`-shortest`** — without this, the soundtrack would extend beyond the video, leaving the last frame frozen for minutes.
- **`-pix_fmt yuv420p`** — many social platforms reject `yuv444p`. This is the safe default.
- **`-c:v libx264`** + **`-c:a aac`** — H.264/AAC is the universally supported pair across web/mobile/social.

---

## 7. Step-by-step: running the pipeline yourself

### 7.1 One-time setup

```bash
# 1. Python environment
pip install playwright

# 2. Install Chromium for Playwright (one-time download, ~150 MB)
python -m playwright install chromium

# 3. Install FFmpeg
#    Windows: download from https://www.gyan.dev/ffmpeg/builds/ → extract → note the bin path
#    Mac:     brew install ffmpeg
#    Linux:   apt install ffmpeg
```

### 7.2 Configure paths in `record_video.py`

Edit lines 7–11:
- `html_file` — which animation to record
- `audio_file` — the soundtrack
- `ffmpeg_path` — absolute path to your `ffmpeg` binary

### 7.3 Compute the total duration

Open the HTML, search for every `data-duration="..."`, sum them up in milliseconds, and put the total in `record_video.py`. Add ~2 s of buffer for the final slide to finish its fade.

### 7.4 Run

```bash
cd videos
python record_video.py
```

You'll see:
```
Recording video for 51.0 seconds...
Recording presentation...
Video recorded: <temp path>
Video saved to: ...\ai-coding-agents-video.webm
Adding audio track...
Done! Video saved to: ...\ai-coding-agents-video.mp4
```

The whole thing takes about **video duration + 5 seconds** (Playwright launch overhead + FFmpeg encode).

### 7.5 Manual recording (alternative, no Python)

If you don't want to run Python, you can record manually with the browser:

1. Open `index.html` in Chrome.
2. Click any video card — the animation page opens and starts auto-playing.
3. Press **F12 → Ctrl+Shift+M** to enter device-emulation mode.
4. Set dimensions to **1080 × 1080**.
5. Start a screen recorder (Windows Game Bar `Win+G`, OBS, Loom, etc.).
6. Press **F5** to refresh and restart the animation from slide 1.
7. Stop recording when the progress bar at the bottom hits 100 %.
8. (Optional) Mux audio in afterwards with FFmpeg.

This is the fallback documented in the `index.html` "How to Record" section.

---

## 8. Authoring a new video template

If you want to add a video #13:

1. **Copy `video-06-minimalist-apple-full.html`** to `video-13-yourname.html`. It's the most complete template.
2. **Replace the data blocks.** Search for `claudeData = {` etc. and substitute your numbers.
3. **Edit the slides.** Each `<div class="slide">` is one screen. Change copy, colors, layout. Keep the `data-duration` attribute.
4. **Add the slide to `index.html`.** Copy one of the `<a href=...><div class="card">...</div></a>` blocks. Update the title, color, emoji, badges (duration / number of slides).
5. **Test in browser.** Open the file directly. The animation should auto-play. Watch through once.
6. **Update `record_video.py`.** Change `html_file` to the new path and update the duration sum.
7. **Run the script.**

### Tips for new templates

- Stick to **1080 × 1080**. Don't change it unless you also change Playwright's viewport.
- **Animate elements with CSS, transition slides with JS.** That's the pattern the rest of the codebase uses.
- **Keep `data-duration` ≥ 3000 ms.** Shorter than that and viewers can't read the content.
- **Test transitions at recording time.** The recorded WebM doesn't always look identical to the live preview — render once before iterating.
- **Use consistent color codes** for the four agents across all videos: Claude `#a371f7`, Copilot `#58a6ff`, Codex `#3fb950`, Cursor `#f78166`.

---

## 9. Output specifications

| Property | Value |
|---|---|
| **Resolution** | 1080 × 1080 (square) |
| **Frame rate** | 25 fps (Playwright default for WebM capture) |
| **Video codec** | H.264 (after FFmpeg pass) |
| **Audio codec** | AAC, ~128 kbps |
| **Pixel format** | `yuv420p` |
| **Container** | MP4 |
| **Final size** | ~2.5 MB for ~50 s video |
| **Duration** | Determined by sum of slide `data-duration` values |

These specs work natively on:
- LinkedIn (square video preferred for feed)
- Twitter/X (in-feed autoplay)
- Instagram feed (1:1 is the original native aspect)
- Facebook feed
- TikTok (will letterbox; 9:16 is preferred there)

For TikTok / Reels / Shorts, the natural extension is a **1080 × 1920 vertical version** — change Playwright's viewport, the body width/height, and a handful of CSS sizes. Most layouts adapt cleanly.

---

## 10. Cost & performance summary

| Item | Cost |
|---|---|
| Authoring time per template | 2–4 hours (HTML/CSS/JS) |
| Recording time per video | ≈ video duration + 5 s |
| Software cost | $0 (Playwright, FFmpeg, Chromium, Inter font are all free) |
| Per-render API cost | $0 (everything runs locally) |
| Storage per output | ~2.5 MB (MP4) + ~4 MB (intermediate WebM) |

There is **no recurring cost** to regenerate a video. Re-running the script with updated data takes under a minute.

---

## 11. Why this stack beats the alternatives (for our use case)

| Alternative | Why we didn't use it |
|---|---|
| **Adobe After Effects / Premiere** | Steep learning curve; hard to make animations data-driven; expensive license; not reproducible from a script |
| **Remotion (React-based video framework)** | Closest competitor and a great choice — but adds a build step and Node/React dependency. The plain HTML approach is simpler when you're already comfortable with vanilla web tech. |
| **D3 + manual screen recording** | Possible, but the manual recording step is the bottleneck — error-prone and not reproducible |
| **Lottie / Bodymovin** | Designed for icon animations; not great for full slideshow productions with text and data |
| **Canva / Veed.io / SaaS tools** | Templates are inflexible; data must be hand-entered slide by slide; subscription cost; locked into their export quotas |
| **Manim / 3blue1brown stack** | Beautiful for math visualizations but heavy and Python-only — overkill for marketing videos |

**The browser-as-renderer pattern wins when:** (a) your team already writes web code, (b) the animations are mostly typography and bar charts, (c) you want a single source of truth (data → animation → video) that's reproducible from CI.

---

## 12. Caveats and known limitations

- **Manual duration tracking.** The `total_duration_ms` in the Python script must be kept in sync with the slide durations in HTML. Solvable with a 10-line parser.
- **No frame-precise audio sync.** The soundtrack is muxed in as a separate stream after recording. If you need frame-accurate sound effects timed to specific slides, this pipeline is too crude — switch to Remotion or a real NLE.
- **Headless audio is silenced.** That's why we mux audio post-hoc.
- **Font rendering may differ slightly between live browser and headless capture** in edge cases. Inspect the WebM after recording to verify.
- **Single source HTML = single style.** If you want the same data with a different visual treatment, you author a new HTML template (which is fast — ~2 h with the existing templates as starting points).

---

## 13. Quick reference card

| Task | Command / file |
|---|---|
| Preview all 12 videos in browser | `videos/index.html` |
| Default video for the script | `video-06-minimalist-apple-full.html` |
| Run the recording pipeline | `python videos/record_video.py` |
| Switch which video to record | Edit `html_file` on line 7 of `record_video.py` |
| Change soundtrack | Replace `videos/soundtrack.mp3` |
| Output location | `videos/ai-coding-agents-video.mp4` |
| Re-create animation in browser | Open the `.html` file directly, press F5 to restart |

---

## 14. Adapting this for your next product

When you reuse this pipeline for the new product, the only things that change are:

1. **The data.** Replace the embedded JS data objects in the HTML with whatever is relevant for the new product.
2. **The copy.** Edit the `<h1>`, `<p>`, etc. inside each `<div class="slide">`.
3. **The branding.** Swap the color palette and the Inter font for whatever brand system you use.
4. **The soundtrack.** Pick a license-cleared track that fits the tone.

Everything else — the slideshow scheduler, the per-element CSS animations, the Playwright recording loop, the FFmpeg mux command — is product-agnostic and can be lifted as-is.
