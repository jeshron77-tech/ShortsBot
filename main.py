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
from moviepy.editor import AudioFileClip, TextClip, CompositeVideoClip, ImageClip, concatenate_videoclips

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")


def generate_ai_content():
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-3.8-flash')
    
    prompt = (
        "You are a viral YouTube Shorts creator in the 'What If' mystery niche.\n"
        "Pick an intense, mind-bending mystery scenario (e.g., What if the Sun disappeared for 10 days? What if gravity reversed? What if the oceans boiled?).\n\n"
        "STRICT SCRIPT RULES:\n"
        "1. SENTENCE 1 MUST STATE THE TOPIC CLEARLY: Start explicitly with 'What if [insert scenario]?'\n"
        "2. Follow with rapid escalation: 'Day 1...', 'Day 3...', 'Day 5...', 'Day 10...'.\n"
        "3. Total script must be between 50 and 65 words (~25-28 seconds).\n"
        "4. Choose 5 distinct categories for the 5 scenes from: earth, city, storm, space, galaxy, ocean, fire, dark.\n\n"
        "Respond ONLY in valid JSON format without markdown codeblocks:\n"
        "{\n"
        '  "title": "[Viral title with emoji and #shorts]",\n'
        '  "description": "[Cliffhanger description for comments]",\n'
        '  "tags": ["shorts", "whatif", "mystery", "science"],\n'
        '  "voice_script": "What if [Scenario]? Day 1, [Event]. Day 3, [Escalation]. Day 5, [Catastrophe]. Day 10, [Climax]...",\n'
        '  "scenes": [\n'
        '    {"category": "earth"},\n'
        '    {"category": "city"},\n'
        '    {"category": "storm"},\n'
        '    {"category": "space"},\n'
        '    {"category": "galaxy"}\n'
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
        "-filter:a", "asetrate=24000*0.84,aresample=24000,atempo=1.19",
        "audio.mp3"
    ]
    subprocess.run(cmd, check=True)
    print("Voiceover saved: audio.mp3")


def fetch_scenes(scenes):
    print("Downloading 5 distinct high-res visuals...")
    curated_urls = {
        "earth": "https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?w=1080&h=1920&fit=crop",
        "city": "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1080&h=1920&fit=crop",
        "storm": "https://images.unsplash.com/photo-1534088568595-a066f410bcda?w=1080&h=1920&fit=crop",
        "space": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1080&h=1920&fit=crop",
        "galaxy": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=1080&h=1920&fit=crop",
        "ocean": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1080&h=1920&fit=crop",
        "fire": "https://images.unsplash.com/photo-1498429089284-41f8cf3ffd39?w=1080&h=1920&fit=crop",
        "dark": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop"
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}
    categories = list(curated_urls.keys())
    
    for i, s in enumerate(scenes):
        cat = s.get("category", categories[i % len(categories)])
        url = curated_urls.get(cat, curated_urls["space"])
        
        saved = False
        try:
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200 and len(r.content) > 5000:
                with open(f"clip_{i}.jpg", "wb") as f:
                    f.write(r.content)
                saved = True
                print(f"Scene {i+1} [{cat}] downloaded.")
        except Exception as e:
            print(f"Scene {i+1} fetch warning: {e}")
            
        if not saved:
            img = Image.new('RGB', (1080, 1920), color=(20 + i*15, 30, 60 + i*20))
            img.save(f"clip_{i}.jpg")


def render_video(metadata):
    audio = AudioFileClip("audio.mp3")
    total_dur = audio.duration
    scenes = metadata['scenes']
    scene_dur = total_dur / len(scenes)
    
    scene_clips = []
    for i in range(len(scenes)):
        img_path = f"clip_{i}.jpg"
        img = Image.open(img_path).resize((1080, 1920))
        img.save(img_path)
        
        # Fast, pre-sized clip without per-frame CPU lambda bottleneck
        clip = ImageClip(img_path).set_duration(scene_dur)
        scene_clips.append(clip)
        
    print("Stitching all 5 scenes together...")
    background_track = concatenate_videoclips(scene_clips, method="compose").set_duration(total_dur)
    
    words = metadata["voice_script"].split()
    phrases = [" ".join(words[i:i+3]) for i in range(0, len(words), 3)]
    phrase_dur = total_dur / len(phrases)
    
    text_clips = []
    cur_t = 0
    for p in phrases:
        txt = TextClip(
            p.upper(),
            fontsize=65,
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
    
    # Ultra-fast encoding preset for cloud runners
    print("Encoding video with ultrafast preset...")
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
    print("1. Generating hooked script...")
    meta = generate_ai_content()
    
    print("2. Synthesizing deep male voiceover...")
    make_male_voice(meta['voice_script'])
    
    print("3. Fetching 5 HD vertical visuals...")
    fetch_scenes(meta['scenes'])
    
    print("4. Fast rendering composition...")
    render_video(meta)
    
    print("5. Publishing to YouTube...")
    post_to_youtube(meta)
