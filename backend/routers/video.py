"""
Video Generation Router
Pillow-based text rendering — no ImageMagick, no TextClip, Windows compatible.
Requires: moviepy==1.0.3 gTTS Pillow numpy imageio-ffmpeg
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os, sys, uuid, logging, tempfile, textwrap, json
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()

if sys.platform == "win32":
    VIDEO_DIR = Path(os.environ.get("TEMP", "C:/Temp")) / "finvise_videos"
else:
    VIDEO_DIR = Path("/tmp/finvise_videos")
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


class BriefSection(BaseModel):
    duration: str
    text: str

class BriefSections(BaseModel):
    hook: BriefSection
    stock_snapshot: BriefSection
    whats_happening: BriefSection
    beginner_takeaway: BriefSection
    call_to_action: BriefSection

class VideoRequest(BaseModel):
    company_name: str
    symbol: str
    current_price: float
    pct_change: float
    sentiment: str
    sections: BriefSections
    full_script: str


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def get_font(size):
    from PIL import ImageFont
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_slide(section, W, H):
    import numpy as np
    from PIL import Image, ImageDraw
    bg = hex_to_rgb(section["bg_color"])
    ac = hex_to_rgb(section["accent"])
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=ac)
    title = section["title"].encode("ascii", "ignore").decode("ascii").strip()
    d.text((60, 50), title, font=get_font(44), fill=(255, 255, 255))
    d.text((60, 108), section["subtitle"], font=get_font(26), fill=ac)
    d.rectangle([60, 140, W - 60, 143], fill=ac)
    y = 160
    for line in textwrap.wrap(section["text"], width=62)[:8]:
        d.text((60, y), line, font=get_font(28), fill=(220, 228, 248))
        y += 38
    if section.get("price_display"):
        pd = section["price_display"].encode("ascii", "ignore").decode("ascii").strip()
        d.text((60, H - 90), pd, font=get_font(32), fill=ac)
    d.rectangle([0, H - 6, W, H], fill=ac)
    d.text((W - 380, H - 30), "FinVise AI  |  Educational Content Only",
           font=get_font(16), fill=(80, 90, 110))
    return np.array(img)


def generate_video_sync(req, output_path):
    try:
        try:
            import imageio_ffmpeg
            import moviepy.config as mpconf
            mpconf.FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()
            logger.info(f"FFmpeg: {mpconf.FFMPEG_BINARY}")
        except ImportError:
            logger.warning("imageio-ffmpeg not installed, using system FFmpeg")

        import numpy as np
        from gtts import gTTS
        from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips

        sentiment_map = {
            "bullish": ("#00C853", "#0A2E1A"),
            "bearish": ("#D50000", "#2E0A0A"),
            "neutral":  ("#448AFF", "#0A1A2E"),
        }
        accent, dark = sentiment_map.get(req.sentiment, sentiment_map["neutral"])
        up_down = "UP" if req.pct_change >= 0 else "DOWN"

        sections = [
            {
                "title": "TODAYS BRIEF",
                "subtitle": f"{req.company_name} ({req.symbol})",
                "text": req.sections.hook.text,
                "duration": 10,
                "bg_color": dark,
                "accent": accent,
                "price_display": f"Rs.{req.current_price:,.2f}  {up_down} {abs(req.pct_change):.2f}%",
            },
            {
                "title": "STOCK SNAPSHOT",
                "subtitle": f"{req.symbol} - NSE/BSE",
                "text": req.sections.stock_snapshot.text,
                "duration": 20,
                "bg_color": "#080D18",
                "accent": accent,
                "price_display": None,
            },
            {
                "title": "WHATS HAPPENING",
                "subtitle": "Latest Developments",
                "text": req.sections.whats_happening.text,
                "duration": 30,
                "bg_color": "#080D18",
                "accent": accent,
                "price_display": None,
            },
            {
                "title": "BEGINNER TAKEAWAY",
                "subtitle": "What This Means For You",
                "text": req.sections.beginner_takeaway.text,
                "duration": 20,
                "bg_color": "#080D18",
                "accent": accent,
                "price_display": None,
            },
            {
                "title": "STAY INFORMED",
                "subtitle": "FinVise AI",
                "text": req.sections.call_to_action.text,
                "duration": 10,
                "bg_color": dark,
                "accent": accent,
                "price_display": "Not Financial Advice  |  Do Your Research",
            },
        ]

        W, H = 1280, 720
        temp_dir = tempfile.mkdtemp()

        # Step 1 — TTS voiceover
        logger.info(f"Generating TTS for {req.symbol}...")
        audio_path = os.path.join(temp_dir, "voiceover.mp3")
        gTTS(text=req.full_script, lang="en", slow=False).save(audio_path)
        full_audio = AudioFileClip(audio_path)
        total_dur = full_audio.duration

        # Scale durations to match audio
        scale = total_dur / sum(s["duration"] for s in sections)
        for s in sections:
            s["duration"] *= scale

        # Step 2 — Render slides with Pillow
        logger.info("Rendering slides...")
        clips = []
        t = 0.0
        for s in sections:
            dur = s["duration"]
            frame = draw_slide(s, W, H)
            clip = ImageClip(frame, duration=dur).set_audio(
                full_audio.subclip(t, min(t + dur, total_dur))
            )
            clips.append(clip)
            t += dur

        # Step 3 — Export MP4
        logger.info("Exporting MP4...")
        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None,
            temp_audiofile=os.path.join(temp_dir, "tmp.m4a"),
        )
        final.close()
        full_audio.close()
        logger.info(f"Video ready: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Video generation failed: {e}", exc_info=True)
        return False


@router.post("/generate")
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    output_path = str(VIDEO_DIR / f"{job_id}.mp4")
    status_path = str(VIDEO_DIR / f"{job_id}.json")
    with open(status_path, "w") as f:
        json.dump({"status": "processing", "job_id": job_id}, f)

    def run():
        success = generate_video_sync(request, output_path)
        with open(status_path, "w") as f:
            json.dump({
                "status": "ready" if success else "failed",
                "job_id": job_id,
                "path": output_path if success else None,
            }, f)

    import threading
    threading.Thread(target=run, daemon=True).start()
    return {"job_id": job_id, "status": "processing"}


@router.get("/status/{job_id}")
async def get_video_status(job_id: str):
    p = VIDEO_DIR / f"{job_id}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    with open(p) as f:
        return json.load(f)


@router.get("/download/{job_id}")
async def download_video(job_id: str):
    p = VIDEO_DIR / f"{job_id}.mp4"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Video not ready")
    return FileResponse(
        path=str(p),
        media_type="video/mp4",
        filename=f"finvise_brief_{job_id[:8]}.mp4",
    )
