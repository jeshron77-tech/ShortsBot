import os
import json
import requests
import random
import asyncio
from PIL import Image

if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import edge_tts
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ImageClip, concatenate_videoclips

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PEXELS_KEY = (os.environ.get("PEXELS_API_KEY") or "").strip()


def generate_ai_content():
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-3.8-flash')
    
    prompt = (
        "You are a viral YouTube Shorts creator. Write a gripping 'What If' mystery story (30-35s).\n"
        "Break into EXACTLY 5 sequential scenes (Day 1, 3, 5, 7, 10).\n"
        "Return ONLY clean JSON without markdown codeblocks:\n"
        "{\n"
        '  "title": "[Viral title with emoji and #shorts]",\n'
        '  "description": "[2-sentence cliffhanger]",\n'
        '  "tags": ["shorts", "whatif", "mystery"],\n'
        '  "voice_script": "[Full 30-35s narration text]",\n'
        '  "scenes": [\n'
        '    {"keyword": "dark bedroom ceiling shock", "beat": "Day 1: ..."}, \n'
        '    {"keyword": "ocean mega tsunami storm", "beat": "Day 3: ..."}, \n'
        '    {"keyword": "sky clouds space atmosphere", "beat": "Day 5: ..."}, \n'
        '    {"keyword": "volcano earthquake fire destruction", "beat": "Day 7: ..."}, \n'
        '    {"keyword": "galaxy black hole cosmos void", "beat": "Day 10: ..."}\n'
        '  ]\n'
        "}"
    )
    
    response = model.generate_content(prompt)
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_text)


async def make_male_voice(text):
    print("Generating natural male voiceover via Edge-TTS (ChristopherNeural)...")
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural", rate="+5%")
    await communicate.save("audio.mp3")
    print("Voiceover saved: audio.mp3")


def fetch_scenes(scenes):
    headers = {"Authorization": PEXELS_KEY} if PEXELS_KEY else {}
    for i, s in enumerate(scenes):
        kw = s.get("keyword", "mystery")
        saved = False
        
        # Try fetching vertical video from Pexels
        if PEXELS_KEY:
            try:
                url = f"https://api.pexels.com/videos/search?query={kw}&orientation=portrait&per_page=5"
                r = requests.get(url, headers=headers, timeout=15).json()
                vids = r.get("videos", [])
                if vids:
                    v_files = random.choice(vids).get("video_files", [])
                    v_files = [f for f in v_files if f.get("width", 0) <= 1080 and f.get("link")]
                    if v_files:
                        link = sorted(v_files, key=lambda x: x.get("width", 0), reverse=True)[0]["link"]
                        with open(f"clip_{i}.mp4", "wb") as f:
                            f.write(requests.get(link, timeout=30).content)
                        saved = True
            except Exception as e:
                print(f"Pexels video fallback {i}: {e}")
        
        # Fallback: Fetch vertical image from Pollinations / Unsplash
        if not saved:
            try:
                p_url = f"https://image.pollinations.ai/p/{requests.utils.quote(kw)}?width=1080&height=1920&nologo=true&seed={random.randint(1,99999)}"
                r = requests.get(p_url, timeout=20)
                if r.status_code == 200:
                    with open(f"clip_{i}.jpg", "wb") as f:
                        f.write(r.content)
                    saved = True
            except Exception:
                pass
        
        if not saved:
            Image.new('RGB', (1080, 1920), color=(10 + i * 15, 10, 25)).save(f"clip_{i}.jpg")


def render_video(metadata):
    audio = AudioFileClip("audio.mp3")
    total_dur = audio.duration
    scenes = metadata['scenes']
    scene_dur = total_dur / len(scenes)
    
    clips = []
    for i in range(len(scenes)):
        if os.path.exists(f"clip_{i}.mp4"):
            clip = VideoFileClip(f"clip_{i}.mp4").without_audio()
            clip = clip.loop(duration=scene_dur) if clip.duration < scene_dur else clip.subclip(0, scene_dur)
            clip = clip.resize((1080, 1920))
        else:
            clip = ImageClip(f"clip_{i}.jpg").set_duration(scene_dur).resize((1080, 1920))
            clip = clip.resize(lambda t, dur=scene_dur: 1.0 + 0.08 * (t / dur))
        clips.append(clip)
        
    bg = concatenate_videoclips(clips, method="compose").set_duration(total_dur)
    
    words = metadata["voice_script"].split()
    phrases = [" ".join(words[i:i+3]) for i in range(0, len(words), 3)]
    phrase_dur = total_dur / len(phrases)
    
    texts = []
    cur_t = 0
    for p in phrases:
        txt = TextClip(
            p.upper(), fontsize=65, color='yellow', font='DejaVu-Sans-Bold',
            stroke_color='black', stroke_width=4, method='caption', size=(960, None)
        ).set_start(cur_t).set_duration(phrase_dur).set_pos('center')
        texts.append(txt)
        cur_t += phrase_dur
        
    final = CompositeVideoClip([bg] + texts, size=(1080, 1920)).set_audio(audio)
    final.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")


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
    meta = generate_ai_content()
    asyncio.run(make_male_voice(meta['voice_script']))
    fetch_scenes(meta['scenes'])
    render_video(meta)
    post_to_youtube(meta)
