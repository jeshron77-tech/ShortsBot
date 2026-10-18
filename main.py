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

# 30+ completely diverse fallback scenarios across science, nature, and the universe
FALLBACK_SCRIPTS = [
    {
        "title": "What If The Moon Crashed Into Earth? 🌑💥 #shorts",
        "description": "What happens if the Moon suddenly falls toward our planet?",
        "tags": ["shorts", "whatif", "moon", "space", "mystery"],
        "voice_script": "What if the Moon crashed into Earth? Day 1, catastrophic tidal waves over a mile high drown entire coastal nations. Day 3, gravitational tides fracture tectonic plates into violent supervolcanoes. Day 6, the Moon crosses the Roche limit, shattering into a massive ring of fire. Day 7, trillions of meteors incinerate the atmosphere.",
        "image_prompts": ["giant moon looming over earth sky", "mile high tsunami swallowing city", "cracked tectonic plates magma earth", "moon shattering into debris ring space", "asteroid bombardment apocalyptic earth"]
    },
    {
        "title": "What If Earth Stopped Spinning for 10 Days? 🌍😱 #shorts",
        "description": "What would happen if our planet suddenly locked in place?",
        "tags": ["shorts", "whatif", "mystery", "science"],
        "voice_script": "What if Earth stopped spinning for ten days? Day 1, supersonic winds obliterate every skyscraper on the equator. Day 3, oceans shift violently toward the poles under titanic water walls. Day 5, one half freezes into endless darkness while the other roasts. Day 10, the planetary magnetic shield collapses completely.",
        "image_prompts": ["earth halting space orbit", "titanic ocean tsunami city destruction", "frozen globe glaciers blue ice landscape", "earth magnetic field solar storm space", "shattered apocalyptic planet earth orbit"]
    },
    {
        "title": "What If Oxygen Vanished For 5 Seconds? 💨⚠️ #shorts",
        "description": "You might think 5 seconds is harmless, but think again! #shorts",
        "tags": ["shorts", "whatif", "science", "danger"],
        "voice_script": "What if Earth lost oxygen for just five seconds? Second 1, every concrete building crumbles instantly into massive dust clouds. Second 2, the daytime sky turns pitch black as sunlight stops scattering. Second 3, everyone's eardrums violently rupture from sudden air pressure collapse. Second 5, unbonded oceans instantly vaporize into space.",
        "image_prompts": ["skyscraper collapsing into dust clouds", "daytime city pitch black sky bright stars", "atmospheric pressure shockwave disaster", "ocean boiling vaporizing into space atmosphere", "barren desolate rocky planet landscape"]
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
    },
    {
        "title": "What If You Fell Into Jupiter? 🪐⚡ #shorts",
        "description": "The terrifying journey through the solar system's biggest gas giant. #shorts",
        "tags": ["shorts", "whatif", "jupiter", "space"],
        "voice_script": "What if you fell straight into Jupiter? Minute 1, you plunge through ammonia ice clouds at supersonic speeds. Minute 15, the sky turns pitch black as crushing atmospheric pressure builds. Minute 30, hurricane winds and lightning bolts thousands of times stronger than Earth's tear through you. Hour 1, you dissolve in oceans of liquid metallic hydrogen.",
        "image_prompts": ["giant jupiter clouds space plunge", "dark stormy turbulent gas atmosphere", "massive cosmic lightning gas giant", "liquid metallic hydrogen ocean jupiter", "jupiter vortex storm eye"]
    },
    {
        "title": "What If Earth Had Two Suns? ☀️☀️ #shorts",
        "description": "How a binary star system would reshape life on Earth. #shorts",
        "tags": ["shorts", "whatif", "space", "earth"],
        "voice_script": "What if Earth had two suns in the sky? Month 1, night never truly falls, driving global ecosystems and sleep cycles into total chaos. Month 3, scorching double solar radiation boils away freshwater lakes and rivers. Month 6, catastrophic mega-droughts transform green continents into burning deserts. Year 1, temperatures soar past 150 degrees.",
        "image_prompts": ["two suns in alien sky over city", "scorched drying river bed cracked earth", "massive desert dunes burning suns", "dried out globe viewed from space", "sun flare storm hitting atmosphere"]
    },
    {
        "title": "What If All Insects Disappeared? 🐝🦗 #shorts",
        "description": "The rapid collapse of Earth's biosphere without insects. #shorts",
        "tags": ["shorts", "whatif", "nature", "biology"],
        "voice_script": "What if every insect vanished overnight? Week 1, flowering plants fail to pollinate, collapsing commercial crop harvests globally. Month 1, bird and reptile populations plummet as their primary food source vanishes. Month 6, un-decomposed biological waste piles up worldwide. Year 1, global starvation triggers total economic and societal collapse.",
        "image_prompts": ["dead wilted flower field without bees", "starving bird desolate forest", "dying crops agriculture drought", "empty supermarket shelves abandoned city", "overgrown barren wasteland landscape"]
    },
    {
        "title": "What If A Rogue Planet Entered Our Solar System? 🪐🚨 #shorts",
        "description": "What happens when a wandering planet invades our solar system? #shorts",
        "tags": ["shorts", "whatif", "rogueplanet", "space"],
        "voice_script": "What if a rogue planet crossed our solar system? Day 1, alien gravitational pull destabilizes the orbits of every planet. Day 5, Earth is violently yanked outward into deep freezing space. Day 10, global oceans freeze solid as we drift away from the Sun. Day 30, temperatures plunge to negative 300 degrees in permanent darkness.",
        "image_prompts": ["dark rogue planet approaching solar system", "earth pulled away from glowing sun", "freezing dark frozen globe space", "frozen skyscrapers ice sheets dark sky", "drifting lonely planet deep cosmos"]
    },
    {
        "title": "What If Gravity Was Cut In Half? 🛸⚖️ #shorts",
        "description": "What happens when Earth's gravity drops by 50%? #shorts",
        "tags": ["shorts", "whatif", "physics", "science"],
        "voice_script": "What if Earth's gravity suddenly dropped by half? Minute 1, every human and vehicle leaps effortlessly into the air. Minute 10, high-pressure atmospheric gases begin leaking permanently into space. Hour 1, ocean tides rise into chaotic standing water towers. Day 1, human bone density degrades rapidly while weather systems turn wildly unpredictable.",
        "image_prompts": ["cars and people floating above city street", "atmosphere leaking away glowing earth space", "chaotic towering ocean waves", "astronaut floating over fractured landscape", "earth distorted atmosphere orbit"]
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
    "biological mutations, deep sleep comas, and human body physics",
    "ancient Earth catastrophes, dinosaur extinction meteors, and primordial climates"
]

def get_channel_recent_titles():
    """Queries YouTube API directly for the channel's 15 most recent uploads to prevent duplicates."""
    titles = []
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"])
            yt = build("youtube", "v3", credentials=creds)
            # Fetch channel uploads
            ch_resp = yt.channels().list(mine=True, part="contentDetails").execute()
            uploads_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            pl_resp = yt.playlistItems().list(playlistId=uploads_id, part="snippet", maxResults=15).execute()
            for item in pl_resp.get("items", []):
                t = item["snippet"]["title"]
                titles.append(t.lower())
            print(f"Retrieved {len(titles)} past videos from YouTube channel.")
    except Exception as e:
        print(f"Could not retrieve channel history (proceeding with fallback check): {e}")
    return titles


def generate_ai_content(past_titles):
    selected_niche = random.choice(NICHES)
    prompt = (
        f"You are Zack D. Films creating a viral YouTube Short about {selected_niche}.\n"
        f"CRITICAL: Do NOT write about any of these recent topics: {past_titles}\n"
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
                    title_clean = parsed["title"].lower()
                    if not any(past in title_clean for past in past_titles):
                        print(f"Generated successfully via {model_name}: {parsed['title']}")
                        return parsed
            except Exception as e:
                print(f"Model {model_name} error: {e}")

    print("Selecting an unrepeated scenario from fallback library...")
    available = [
        s for s in FALLBACK_SCRIPTS 
        if not any(p in s["title"].lower() for p in past_titles)
    ]
    if not available:
        available = FALLBACK_SCRIPTS

    chosen = random.choice(available)
    print(f"Selected unique scenario: {chosen['title']}")
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

    creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"])
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
    print("1. Checking past YouTube uploads to prevent duplicates...")
    past = get_channel_recent_titles()
    
    print("2. Generating a completely unique topic...")
    meta = generate_ai_content(past)
    
    print("3. Synthesizing Piper neural voice...")
    make_male_voice(meta['voice_script'])
    
    print("4. Assembling video and subtitles...")
    render_video(meta)
    
    print("5. Publishing to YouTube...")
    post_to_youtube(meta)
