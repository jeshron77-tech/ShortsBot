import os
import json
import urllib.parse
import requests
import random
import subprocess
import time
from PIL import Image

if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

FALLBACK_SCRIPTS = [
    {
        "title": "What If Earth Stopped Spinning for 10 Days? 🌍😱 #shorts",
        "description": "What would happen if our planet suddenly locked in place?",
        "tags": ["shorts", "whatif", "mystery", "science"],
        "voice_script": "What if Earth stopped spinning for ten days? Day 1, supersonic winds obliterate every skyscraper on the equator. Day 3, oceans shift violently toward the poles under titanic water walls. Day 5, one half freezes into endless darkness while the other roasts. Day 10, the planetary magnetic shield collapses completely.",
        "image_prompts": [
            "earth planet halting space orbit",
            "titanic ocean tsunami city destruction",
            "frozen globe glaciers blue ice landscape",
            "earth magnetic field solar storm space",
            "shattered apocalyptic planet earth orbit"
        ]
    },
    {
        "title": "What If Oxygen Vanished For 5 Seconds? 💨⚠️ #shorts",
        "description": "You might think 5 seconds is harmless, but think again! #shorts",
        "tags": ["shorts", "whatif", "science", "danger"],
        "voice_script": "What if Earth lost oxygen for just five seconds? Second 1, every concrete building crumbles instantly into massive dust clouds. Second 2, the daytime sky turns pitch black as sunlight stops scattering. Second 3, everyone's eardrums violently rupture from sudden air pressure collapse. Second 5, unbonded oceans instantly vaporize into space.",
        "image_prompts": [
            "skyscraper collapsing into dust clouds",
            "daytime city pitch black sky bright stars",
            "atmospheric pressure shockwave disaster",
            "ocean boiling vaporizing into space atmosphere",
            "barren desolate rocky planet landscape"
        ]
    },
    {
        "title": "What If All Volcanoes Erupted At Once? 🌋🔥 #shorts",
        "description": "The terrifying scenario of global volcanic apocalypse. #shorts",
        "tags": ["shorts", "whatif", "volcano", "earth"],
        "voice_script": "What if every volcano on Earth erupted simultaneously? Hour 1, massive shockwaves level surrounding cities and trigger global tsunamis. Day 2, trillions of tons of ash blot out the Sun completely. Day 5, global temperatures plunge into an artificial volcanic winter. Day 10, toxic acid rain burns all plant life.",
        "image_prompts": [
            "massive volcanic eruption lightning magma explosion",
            "dark volcanic ash cloud blocking sun city",
            "freezing apocalyptic volcanic winter ice snow",
            "toxic red acid rain storm ruins",
            "burning planet earth view from space"
        ]
    },
    {
        "title": "What If The Mariana Trench Opened Up? 🌊🕳️ #shorts",
        "description": "What if the deepest ocean abyss opened directly into Earth's mantle? #shorts",
        "tags": ["shorts", "whatif", "ocean", "trench"],
        "voice_script": "What if the Mariana Trench split wide open? Hour 1, trillions of tons of seawater drain directly into Earth's boiling mantle. Day 2, titanic steam explosions blast superheated volcanic plumes into the atmosphere. Day 5, global ocean levels drop hundreds of feet. Day 10, seismic tsunamis batter every continent.",
        "image_prompts": [
            "deep ocean abyss trench crack glowing magma",
            "massive underwater steam explosion sea eruption",
            "ocean receding dry seabed shipwrecks",
            "colossal tidal wave hitting coastal city",
            "earth oceans draining view from orbit"
        ]
    }
]

# Guaranteed high-resolution 1080x1920 disaster photography backups
HIGHRES_BACKUPS = [
    "https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?w=1080&h=1920&fit=crop", # Planet Earth in space
    "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop", # Apocalypse ruins
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1080&h=1920&fit=crop", # Rough ocean storm
    "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1080&h=1920&fit=crop", # Dark aurora storm
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop"  # Deep nebula / space
]

NICHES = [
    "deep ocean exploration and Mariana trench mysteries",
    "space disasters, black holes, and rogue planets",
    "atmospheric and planetary science collapses",
    "geological super-disasters like tectonic shifts and supervolcanoes",
    "biology, human body limits, and microscopic anomalies",
    "ancient Earth, prehistoric climates, and mega-asteroid impacts"
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
        f"Do NOT write about any of these recent topics: {used_titles[-10:]}\n\n"
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
        '    "massive ocean storm waves",\n'
        '    "frozen ruined city blizzard",\n'
        '    "dark glowing aurora sky",\n'
        '    "shattered earth space orbit"\n'
        '  ]\n'
        "}"
    )

    models_to_try = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-1.5-pro']
    
    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        for model_name in models_to_try:
            try:
                print(f"Requesting novel script ({selected_niche}) from {model_name}...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_text)
                if "image_prompts" in parsed and len(parsed["image_prompts"]) >= 5:
                    if parsed["title"] not in used_titles:
                        print(f"Generated successfully via {model_name}!")
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
        
    cmd_piper = [
        "python", "-m", "piper",
        "--model", "en_US-lessac-medium.onnx",
        "--output_file", "temp_voice.wav"
    ]
    with open("script_text.txt", "rb") as f_in:
        subprocess.run(cmd_piper, stdin=f_in, check=True)
    
    cmd_ffmpeg = [
        "ffmpeg", "-y", "-i", "temp_voice.wav",
        "-filter:a", "compand=.3|.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2",
        "audio.mp3"
    ]
    subprocess.run(cmd_ffmpeg, check=True)
    print("Voice ready: audio.mp3")


def fetch_and_animate_scenes(image_prompts, duration_per_scene):
    print(f"Rendering 5 cinematic scenes ({duration_per_scene:.2f}s each)...")
    total_frames = int(duration_per_scene * 24)
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for i, raw_prompt in enumerate(image_prompts[:5]):
        img_file = f"raw_{i}.jpg"
        clip_file = f"motion_{i}.mp4"
        
        # Clean, punchy prompt for fast generation
        clean_p = f"{raw_prompt}, cinematic, 8k, photorealistic"
        encoded = urllib.parse.quote(clean_p)
        seed = random.randint(100, 99999)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&seed={seed}&nologo=true&model=turbo"
        
        downloaded = False
        for attempt in range(2):
            try:
                print(f"Downloading scene {i+1}/5: {raw_prompt}...")
                r = requests.get(url, headers=headers, timeout=30)
                if r.status_code == 200 and len(r.content) > 10000:
                    with open(img_file, "wb") as f:
                        f.write(r.content)
                    base_img = Image.open(img_file).convert("RGB").resize((1080, 1920))
                    base_img.save(img_file, quality=95)
                    downloaded = True
                    break
            except Exception as e:
                print(f"Pollinations scene {i+1} attempt {attempt+1} note: {e}")
                time.sleep(2)
                
        # If AI image times out, immediately pull matching 4K photographic disaster visual (NEVER flat solid color)
        if not downloaded:
            print(f"Using high-res photographic visual for scene {i+1}...")
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
        time.sleep(1)


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


if __name__ == "__main__":
    print("1. Generating novel script and visual prompts...")
    meta = generate_ai_content()
    
    print("2. Synthesizing Piper neural voice...")
    make_male_voice(meta['voice_script'])
    
    print("3. Assembling video and subtitles...")
    render_video(meta)
    
    print("4. Publishing to YouTube...")
    post_to_youtube(meta)
