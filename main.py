import os
import json
import urllib.parse
import requests
import random
import subprocess
import time
import io
from PIL import Image

if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_IMAGE_KEY = os.environ.get("GEMINI_IMAGE_API_KEY")

FALLBACK_SCRIPTS = [
    {
        "title": "What If Earth Stopped Spinning for 10 Days? 🌍😱 #shorts",
        "description": "What would happen if our planet suddenly locked in place?",
        "tags": ["shorts", "whatif", "mystery", "science"],
        "voice_script": "What if Earth stopped spinning for ten days? Day 1, supersonic winds obliterate every skyscraper on the equator. Day 3, oceans shift violently toward the poles under titanic water walls. Day 5, one half freezes into endless darkness while the other roasts. Day 10, the planetary magnetic shield collapses completely.",
        "image_prompts": ["earth planet halting space orbit", "titanic ocean tsunami city destruction", "frozen globe glaciers blue ice landscape", "earth magnetic field solar storm space", "shattered apocalyptic planet earth orbit"]
    },
    {
        "title": "What If All Volcanoes Erupted At Once? 🌋🔥 #shorts",
        "description": "The terrifying scenario of global volcanic apocalypse. #shorts",
        "tags": ["shorts", "whatif", "volcano", "earth"],
        "voice_script": "What if every volcano on Earth erupted simultaneously? Hour 1, massive shockwaves level surrounding cities and trigger global tsunamis. Day 2, trillions of tons of ash blot out the Sun completely. Day 5, global temperatures plunge into an artificial volcanic winter. Day 10, toxic acid rain burns all plant life.",
        "image_prompts": ["massive volcanic eruption lightning magma explosion", "dark volcanic ash cloud blocking sun city", "freezing apocalyptic volcanic winter ice snow", "toxic red acid rain storm ruins", "burning planet earth view from space"]
    },
    {
        "title": "What If The Mariana Trench Opened Up? 🌊🕳️ #shorts",
        "description": "What if the deepest ocean abyss opened directly into Earth's mantle? #shorts",
        "tags": ["shorts", "whatif", "ocean", "trench"],
        "voice_script": "What if the Mariana Trench split wide open? Hour 1, trillions of tons of seawater drain directly into Earth's boiling mantle. Day 2, titanic steam explosions blast superheated volcanic plumes into the atmosphere. Day 5, global ocean levels drop hundreds of feet. Day 10, seismic tsunamis batter every continent.",
        "image_prompts": ["deep ocean abyss trench crack glowing magma", "massive underwater steam explosion sea eruption", "ocean receding dry seabed shipwrecks", "colossal tidal wave hitting coastal city", "earth oceans draining view from orbit"]
    }
]

HIGHRES_BACKUPS = [
    "https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?w=1080&h=1920&fit=crop",
    "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1080&h=1920&fit=crop",
    "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1080&h=1920&fit=crop",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop"
]

NICHES = [
    "deep ocean abyss anomalies and trench discoveries",
    "interstellar astrophysics, supernovas, and rogue cosmic objects",
    "atmospheric and magnetosphere collapses",
    "geological super-disasters like continental rift ruptures and supervolcanoes",
    "ancient Earth catastrophes, dinosaur extinction meteors, and primordial climates"
]

def generate_ai_content():
    used_file = "history_topics.json"
    used_titles = []
    if os.path.exists(used_file):
        try:
            with open(used_file, "r") as f:
                used_titles = json.load(f)
        except Exception:
            pass

    selected_niche = random.choice(NICHES)
    prompt = (
        f"You are Zack D. Films creating a viral YouTube Short about {selected_niche}.\n"
        f"CRITICAL: Do NOT write about any of these recent topics: {used_titles[-10:]}\n"
        "Pick a BRAND NEW, completely unique 'What If' scenario.\n\n"
        "RULES:\n"
        "1. Sentence 1 MUST start with 'What if [Unique Scenario]?'\n"
        "2. Follow with rapid timeline: 'Day 1...', 'Day 3...', 'Day 5...', 'Day 10...' (or Seconds/Minutes/Hours).\n"
        "3. Total voice script length: 45 to 55 words.\n"
        "4. Provide EXACTLY 5 concise visual prompts (3 to 6 words each) in 'image_prompts'.\n\n"
        "Respond ONLY in valid JSON:\n"
        "{\n"
        '  "title": "[Unique Title #shorts]",\n'
        '  "description": "[Description]",\n'
        '  "tags": ["shorts", "whatif", "mystery"],\n'
        '  "voice_script": "What if [Scenario]? Day 1, [Event]. Day 3, [Escalation]. Day 5, [Catastrophe]. Day 10, [Climax]...",\n'
        '  "image_prompts": [\n'
        '    "space view planet earth",\n'
        '    "massive ocean storm waves"\n'
        '  ]\n'
        "}"
    )

    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        for model_name in ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-1.5-flash-8b']:
            try:
                print(f"Requesting novel script ({selected_niche}) from {model_name}...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_text)
                if "image_prompts" in parsed and len(parsed["image_prompts"]) >= 5:
                    if parsed["title"] not in used_titles:
                        print(f"Generated successfully: {parsed['title']}")
                        used_titles.append(parsed["title"])
                        with open(used_file, "w") as f:
                            json.dump(used_titles[-50:], f)
                        return parsed
            except Exception as e:
                print(f"Model {model_name} error: {e}")

    print("Selecting an unrepeated scenario from fallback library...")
    available = [s for s in FALLBACK_SCRIPTS if s["title"] not in used_titles]
    if not available:
        available = FALLBACK_SCRIPTS
        used_titles = []
        
    chosen = random.choice(available)
    used_titles.append(chosen["title"])
    with open(used_file, "w") as f:
        json.dump(used_titles[-50:], f)
    return chosen


def make_male_voice(text):
    print("Generating voiceover via Piper neural TTS...")
    with open("script_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    subprocess.run(["python", "-m", "piper", "--model", "en_US-lessac-medium.onnx", "--output_file", "temp_voice.wav"], stdin=open("script_text.txt", "rb"), check=True)
    subprocess.run(["ffmpeg", "-y", "-i", "temp_voice.wav", "-filter:a", "compand=.3|.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2", "audio.mp3"], check=True)


def fetch_and_animate_scenes(image_prompts, duration_per_scene):
    print(f"Rendering 5 cinematic scenes ({duration_per_scene:.2f}s each) with Imagen 3...")
    total_frames = int(duration_per_scene * 24)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    if GEMINI_IMAGE_KEY:
        genai.configure(api_key=GEMINI_IMAGE_KEY)
        print("Successfully loaded second Gemini API key for images.")
    
    for i, raw_prompt in enumerate(image_prompts[:5]):
        img_file = f"raw_{i}.jpg"
        clip_file = f"motion_{i}.mp4"
        clean_p = f"{raw_prompt}, cinematic, 8k, highly detailed, photorealistic"
        
        downloaded = False
        
        # 1. ATTEMPT IMAGEN 3
        if GEMINI_IMAGE_KEY:
            try:
                print(f"Generating scene {i+1}/5 with Imagen 3: {raw_prompt}...")
                imagen = genai.ImageGenerationModel("imagen-3.0-generate-001")
                result = imagen.generate_images(
                    prompt=clean_p,
                    number_of_images=1,
                    aspect_ratio="9:16",
                    output_mime_type="image/jpeg"
                )
                img_bytes = result.images[0].image.image_bytes
                with open(img_file, "wb") as f:
                    f.write(img_bytes)
                base_img = Image.open(img_file).convert("RGB").resize((1080, 1920))
                base_img.save(img_file, quality=95)
                downloaded = True
                print("Imagen 3 Success!")
            except Exception as e:
                print(f"Imagen 3 fallback needed: {e}")

        # 2. ATTEMPT POLLINATIONS
        if not downloaded:
            encoded = urllib.parse.quote(clean_p)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&model=turbo"
            try:
                print(f"Falling back to Pollinations for scene {i+1}...")
                r = requests.get(url, headers=headers, timeout=25)
                if r.status_code == 200 and len(r.content) > 10000:
                    with open(img_file, "wb") as f:
                        f.write(r.content)
                    base_img = Image.open(img_file).convert("RGB").resize((1080, 1920))
                    base_img.save(img_file, quality=95)
                    downloaded = True
            except Exception:
                pass
                
        # 3. ATTEMPT PHOTOGRAPHY
        if not downloaded:
            print(f"Using high-res photographic backup for scene {i+1}...")
            backup_url = HIGHRES_BACKUPS[i % len(HIGHRES_BACKUPS)]
            try:
                r_backup = requests.get(backup_url, headers=headers, timeout=20)
                with open(img_file, "wb") as f:
                    f.write(r_backup.content)
                base_img = Image.open(img_file).convert("RGB").resize((1080, 1920))
                base_img.save(img_file, quality=95)
            except Exception:
                pass
            
        zoom_filter = f"zoompan=z='min(pzoom+0.003,1.25)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=24"
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", img_file,
            "-vf", zoom_filter,
            "-t", str(duration_per_scene),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
            clip_file
        ]
        subprocess.run(cmd, check=True)

def render_video(metadata):
    audio = AudioFileClip("audio.mp3")
    total_dur = audio.duration
    prompts = metadata.get('image_prompts', [])[:5]
    duration_per_scene = total_dur / len(prompts)
    
    fetch_and_animate_scenes(prompts, duration_per_scene)
    
    video_clips = []
    for i in range(len(prompts)):
        c = VideoFileClip(f"motion_{i}.mp4").subclip(0, duration_per_scene).set_duration(duration_per_scene)
        video_clips.append(c)
        
    background_track = concatenate_videoclips(video_clips, method="chain").set_duration(total_dur)
    
    words = metadata["voice_script"].split()
    phrases = [" ".join(words[i:i+3]) for i in range(0, len(words), 3)]
    phrase_dur = total_dur / len(phrases)
    
    text_clips = []
    cur_t = 0
    for p in phrases:
        txt = TextClip(
            p.upper(),
            fontsize=68,
            color='yellow',
            font='DejaVu-Sans-Bold',
            stroke_color='black',
            stroke_width=4,
            method='caption',
            size=(960, None)
        ).set_start(cur_t).set_duration(phrase_dur).set_pos('center')
        text_clips.append(txt)
        cur_t += phrase_dur
        
    final_video = CompositeVideoClip([background_track] + text_clips, size=(1080, 1920))
    final_video = final_video.set_audio(audio).set_duration(total_dur)
    
    print("Writing final assembled Short...")
    final_video.write_videofile(
        "final.mp4",
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=2
    )

def post_to_youtube(metadata):
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from googleapiclient.http import MediaFileUpload

    try:
        # Reverted to ONLY youtube.upload so it matches your existing token exactly
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)
        
        body = {
            "snippet": {
                "title": metadata["title"],
                "description": metadata["description"] + "\n\n" + " ".join(["#" + t for t in metadata["tags"]]),
                "tags": metadata["tags"],
                "categoryId": "27"
            },
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
        }
        
        media = MediaFileUpload("final.mp4", chunksize=-1, resumable=True, mimetype="video/mp4")
        res = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
        print(f"Uploaded successfully! Video ID: {res.get('id')}")
    except Exception as e:
        print(f"YOUTUBE UPLOAD FAILED: {e}")

if __name__ == "__main__":
    print("1. Generating unique topic...")
    meta = generate_ai_content()
    
    print("2. Synthesizing Piper neural voice...")
    make_male_voice(meta['voice_script'])
    
    print("3. Assembling video and subtitles...")
    render_video(meta)
    
    print("4. Publishing to YouTube...")
    post_to_youtube(meta)
