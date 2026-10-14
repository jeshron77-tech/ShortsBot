import os
import json
import requests
import random
import subprocess
from PIL import Image

if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

from gtts import gTTS
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")


def generate_ai_content():
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-3.8-flash')
    
    prompt = (
        "You are a viral YouTube Shorts creator specializing in high-retention 'What If' mystery stories.\n"
        "Pick a mind-bending mystery or apocalypse scenario.\n\n"
        "STRICT SCRIPT RULES:\n"
        "1. SENTENCE 1 MUST HOOK: Start with 'What if [exact scenario]?'\n"
        "2. Follow with rapid escalation: 'Day 1...', 'Day 3...', 'Day 5...', 'Day 10...'.\n"
        "3. Keep total script between 45 and 55 words (~25 seconds) so it is punchy and fast.\n"
        "4. Assign each scene one of these dramatic categories: 'space', 'storm', 'fire', 'dark', 'galaxy', 'earth', 'ruins'.\n\n"
        "Respond ONLY in valid JSON format without markdown codeblocks:\n"
        "{\n"
        '  "title": "[Viral title with emoji and #shorts]",\n'
        '  "description": "[Cliffhanger description]",\n'
        '  "tags": ["shorts", "whatif", "mystery", "science"],\n'
        '  "voice_script": "What if [Scenario]? Day 1, [Event]. Day 3, [Escalation]. Day 5, [Catastrophe]. Day 10, [Climax]...",\n'
        '  "scenes": [\n'
        '    {"category": "earth"},\n'
        '    {"category": "ruins"},\n'
        '    {"category": "storm"},\n'
        '    {"category": "dark"},\n'
        '    {"category": "space"}\n'
        '  ]\n'
        "}"
    )
    
    response = model.generate_content(prompt)
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_text)


def make_male_voice(text):
    print("Synthesizing narration via Google TTS...")
    tts = gTTS(text=text, lang='en', tld='com', slow=False)
    tts.save("temp_raw.mp3")
    
    print("Applying deep male narrator filter via FFmpeg...")
    cmd = [
        "ffmpeg", "-y", "-i", "temp_raw.mp3",
        "-filter:a", "asetrate=24000*0.83,aresample=24000,atempo=1.20",
        "audio.mp3"
    ]
    subprocess.run(cmd, check=True)
    print("Deep male voiceover saved: audio.mp3")


def fetch_and_animate_scenes(scenes, duration_per_scene):
    print("Fetching themed HD visuals and applying FFmpeg camera zooms...")
    
    thematic_library = {
        "earth": "https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?w=1080&h=1920&fit=crop",
        "ruins": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop",
        "storm": "https://images.unsplash.com/photo-1534088568595-a066f410bcda?w=1080&h=1920&fit=crop",
        "space": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop",
        "galaxy": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=1080&h=1920&fit=crop",
        "dark": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1080&h=1920&fit=crop",
        "fire": "https://images.unsplash.com/photo-1498429089284-41f8cf3ffd39?w=1080&h=1920&fit=crop"
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}
    total_frames = int(duration_per_scene * 24)
    
    for i, s in enumerate(scenes):
        cat = s.get("category", "dark")
        url = thematic_library.get(cat, thematic_library["dark"])
        img_file = f"raw_{i}.jpg"
        clip_file = f"motion_{i}.mp4"
        
        # 1. Download clean image
        try:
            r = requests.get(url, headers=headers, timeout=20)
            with open(img_file, "wb") as f:
                f.write(r.content)
        except Exception:
            Image.new('RGB', (1080, 1920), color=(15 + i*15, 20, 40)).save(img_file)
            
        # 2. Hardware-accelerated zoom/pan via native FFmpeg
        zoom_filter = f"zoompan=z='min(zoom+0.0015,1.25)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=24"
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", img_file,
            "-vf", zoom_filter,
            "-t", str(duration_per_scene),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
            clip_file
        ]
        subprocess.run(cmd, check=True)
        print(f"Rendered dynamic camera motion for Scene {i+1} [{cat}]")


def render_video(metadata):
    audio = AudioFileClip("audio.mp3")
    total_dur = audio.duration
    scenes = metadata['scenes']
    duration_per_scene = total_dur / len(scenes)
    
    # Generate the animated motion clips via FFmpeg
    fetch_and_animate_scenes(scenes, duration_per_scene)
    
    video_clips = [VideoFileClip(f"motion_{i}.mp4") for i in range(len(scenes))]
    background_track = concatenate_videoclips(video_clips, method="compose").set_duration(total_dur)
    
    # Synchronized subtitles
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
    print("1. Generating narrative script...")
    meta = generate_ai_content()
    
    print("2. Synthesizing voiceover...")
    make_male_voice(meta['voice_script'])
    
    print("3. Assembling video and subtitles...")
    render_video(meta)
    
    print("4. Publishing to YouTube...")
    post_to_youtube(meta)
