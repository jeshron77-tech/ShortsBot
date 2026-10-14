import os
import json
import requests
import random
import subprocess
from PIL import Image

if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

FALLBACK_SCRIPTS = [
    {
        "title": "What If Earth Stopped Spinning for 10 Days? 🌍😱 #shorts",
        "description": "What would happen if our planet suddenly locked in place? Watch till the end!",
        "tags": ["shorts", "whatif", "mystery", "science"],
        "voice_script": "What if Earth stopped spinning for 10 days? Day 1, supersonic winds obliterate every skyscraper and city on the equator. Day 3, oceans shift violently toward the poles, swallowing continents under titanic water walls. Day 5, one half freezes into endless arctic darkness while the other roasts. Day 10, the magnetic shield collapses completely.",
        "scenes": [{"category": "city_ruins"}, {"category": "ocean_tsunami"}, {"category": "dark_ice"}, {"category": "space_shield"}, {"category": "earth_space"}]
    },
    {
        "title": "What If Oxygen Vanished For 5 Seconds? 💨⚠️ #shorts",
        "description": "You might think 5 seconds is harmless, but think again! #shorts",
        "tags": ["shorts", "whatif", "science", "danger"],
        "voice_script": "What if Earth lost oxygen for just five seconds? Second 1, every concrete building crumbles instantly into massive dust clouds. Second 2, the daytime sky turns pitch black as atmospheric sunlight stops scattering. Second 3, everyone's eardrums violently rupture from sudden air pressure collapse. Second 5, unbonded oceans instantly vaporize into space.",
        "scenes": [{"category": "earth_space"}, {"category": "city_ruins"}, {"category": "pitch_black"}, {"category": "human_pressure"}, {"category": "ocean_tsunami"}]
    },
    {
        "title": "What If The Sun Disappeared For 7 Days? ☀️❄️ #shorts",
        "description": "The terrifying timeline if our star suddenly vanished. #shorts",
        "tags": ["shorts", "whatif", "sun", "space", "mystery"],
        "voice_script": "What if the Sun vanished for seven whole days? Minute 8, complete pitch blackness engulfs the globe as the final sunlight dies. Day 1, panic sweeps Earth as global temperatures plunge below freezing. Day 3, power grids collapse worldwide under catastrophic blizzards. Day 7, entire oceans freeze solid on the surface.",
        "scenes": [{"category": "space_shield"}, {"category": "pitch_black"}, {"category": "city_ruins"}, {"category": "dark_ice"}, {"category": "earth_space"}]
    }
]

# High-impact apocalyptic / mystery stock visuals (1080x1920 portrait)
THEMATIC_IMAGES = {
    "earth_space": "https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?w=1080&h=1920&fit=crop",
    "city_ruins": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop",
    "ocean_tsunami": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1080&h=1920&fit=crop",
    "pitch_black": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1080&h=1920&fit=crop",
    "dark_ice": "https://images.unsplash.com/photo-1517411032315-54ef2cb783bb?w=1080&h=1920&fit=crop",
    "space_shield": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop",
    "human_pressure": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1080&h=1920&fit=crop"
}


def generate_ai_content():
    prompt = (
        "You are Zack D. Films creating a viral YouTube Short.\n"
        "Pick an intense mystery or 'What If' scenario.\n\n"
        "RULES:\n"
        "1. Sentence 1 MUST start with 'What if [Scenario]?'\n"
        "2. Follow with rapid timeline: 'Day 1...', 'Day 3...', 'Day 5...', 'Day 10...'.\n"
        "3. Length: 45 to 55 words.\n"
        "4. Assign each scene one category from: 'earth_space', 'city_ruins', 'ocean_tsunami', 'pitch_black', 'dark_ice', 'space_shield'.\n\n"
        "Respond ONLY in valid JSON:\n"
        "{\n"
        '  "title": "[Title #shorts]",\n'
        '  "description": "[Description]",\n'
        '  "tags": ["shorts", "whatif", "mystery"],\n'
        '  "voice_script": "What if [Scenario]? Day 1, [Event]. Day 3, [Escalation]. Day 5, [Catastrophe]. Day 10, [Climax]...",\n'
        '  "scenes": [\n'
        '    {"category": "earth_space"},\n'
        '    {"category": "city_ruins"},\n'
        '    {"category": "ocean_tsunami"},\n'
        '    {"category": "pitch_black"},\n'
        '    {"category": "space_shield"}\n'
        '  ]\n'
        "}"
    )

    models_to_try = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-1.5-pro']
    
    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        for model_name in models_to_try:
            try:
                print(f"Requesting script from {model_name}...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_text)
                print(f"Generated successfully via {model_name}!")
                return parsed
            except Exception as e:
                print(f"Model {model_name} quota/error: {e}")

    print("Gemini quota exhausted. Sourcing high-retention scenario from fallback library...")
    return random.choice(FALLBACK_SCRIPTS)


def make_male_voice(text):
    print("Generating natural Zack D. Films style neural voiceover via Piper...")
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


def fetch_and_animate_scenes(scenes, duration_per_scene):
    print("Fetching high-impact visuals and generating dynamic camera motion...")
    headers = {"User-Agent": "Mozilla/5.0"}
    total_frames = int(duration_per_scene * 24)
    
    for i, s in enumerate(scenes):
        cat = s.get("category", "earth_space")
        url = THEMATIC_IMAGES.get(cat, THEMATIC_IMAGES["earth_space"])
        img_file = f"raw_{i}.jpg"
        clip_file = f"motion_{i}.mp4"
        
        # Download and ensure exact 1080x1920 base dimensions
        try:
            r = requests.get(url, headers=headers, timeout=20)
            with open(img_file, "wb") as f:
                f.write(r.content)
            base_img = Image.open(img_file).resize((1080, 1920))
            base_img.save(img_file)
        except Exception:
            Image.new('RGB', (1080, 1920), color=(15 + i*15, 20, 40)).save(img_file)
            
        # Fast, noticeable 20% Ken Burns push-in zoom on every cut
        zoom_filter = f"zoompan=z='min(pzoom+0.003,1.20)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=24"
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", img_file,
            "-vf", zoom_filter,
            "-t", str(duration_per_scene),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
            clip_file
        ]
        subprocess.run(cmd, check=True)
        print(f"Rendered dynamic zoom for Scene {i+1} [{cat}]")


def render_video(metadata):
    audio = AudioFileClip("audio.mp3")
    total_dur = audio.duration
    scenes = metadata['scenes']
    duration_per_scene = total_dur / len(scenes)
    
    fetch_and_animate_scenes(scenes, duration_per_scene)
    
    video_clips = [VideoFileClip(f"motion_{i}.mp4") for i in range(len(scenes))]
    background_track = concatenate_videoclips(video_clips, method="compose").set_duration(total_dur)
    
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
    final_video = final_video.set_audio(audio)
    
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
    print("1. Sourcing narrative script...")
    meta = generate_ai_content()
    
    print("2. Synthesizing Piper neural voice...")
    make_male_voice(meta['voice_script'])
    
    print("3. Assembling video and subtitles...")
    render_video(meta)
    
    print("4. Publishing to YouTube...")
    post_to_youtube(meta)
