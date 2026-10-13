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
        "You are a viral YouTube Shorts creator in the 'What If' mystery niche.\n"
        "Pick an intense, mind-bending scenario (e.g. What if the Sun disappeared for 10 days? What if gravity reversed? What if sleep was illegal?).\n\n"
        "STRICT SCRIPT RULES:\n"
        "1. SENTENCE 1 MUST STATE THE TOPIC CLEARLY: Start explicitly with 'What if [insert exact scenario]?'\n"
        "2. Follow with rapid escalation: 'Day 1...', 'Day 3...', 'Day 5...', 'Day 10...'.\n"
        "3. Keep total script length under 65 words so it stays fast-paced (~25 to 30 seconds).\n"
        "4. Provide simple 1-2 word stock video search terms for each scene so Pexels finds real HD videos.\n\n"
        "Respond ONLY in valid JSON format without markdown blocks:\n"
        "{\n"
        '  "title": "[Viral title with emoji and #shorts]",\n'
        '  "description": "[Cliffhanger description for comments]",\n'
        '  "tags": ["shorts", "whatif", "mystery", "science"],\n'
        '  "voice_script": "What if [Scenario]? Day 1, [Event]. Day 3, [Escalation]. Day 5, [Catastrophe]. Day 10, [Climax]...",\n'
        '  "scenes": [\n'
        '    {"keyword": "space earth"},\n'
        '    {"keyword": "panic crowd"},\n'
        '    {"keyword": "storm disaster"},\n'
        '    {"keyword": "fire destruction"},\n'
        '    {"keyword": "galaxy void"}\n'
        '  ]\n'
        "}"
    )
    
    response = model.generate_content(prompt)
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_text)


async def make_male_voice(text):
    print("Synthesizing deep male voiceover with Edge-TTS...")
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural", rate="+6%", pitch="-5Hz")
    await communicate.save("audio.mp3")
    print("Voiceover saved successfully to audio.mp3")


def fetch_scenes(scenes):
    headers = {"Authorization": PEXELS_KEY} if PEXELS_KEY else {}
    fallback_terms = ["space", "storm", "fire", "ocean", "darkness", "earth", "clouds"]
    
    for i, s in enumerate(scenes):
        kw = s.get("keyword", random.choice(fallback_terms))
        saved = False
        
        # Search Pexels for vertical HD video footage
        if PEXELS_KEY:
            try:
                url = f"https://api.pexels.com/videos/search?query={kw}&orientation=portrait&per_page=10"
                res = requests.get(url, headers=headers, timeout=15)
                if res.status_code == 200:
                    vids = res.json().get("videos", [])
                    if vids:
                        target_vid = random.choice(vids)
                        v_files = target_vid.get("video_files", [])
                        valid = [f for f in v_files if f.get("link") and f.get("height", 0) >= f.get("width", 0)]
                        if not valid:
                            valid = v_files
                        if valid:
                            chosen = sorted(valid, key=lambda x: x.get("width", 0))[0]
                            print(f"Scene {i+1}: Found Pexels video for '{kw}'")
                            v_data = requests.get(chosen["link"], timeout=30).content
                            with open(f"clip_{i}.mp4", "wb") as f:
                                f.write(v_data)
                            saved = True
            except Exception as e:
                print(f"Notice on Pexels Scene {i+1}: {e}")

        # Secondary fallback: Pollinations AI vertical image with zoom
        if not saved:
            try:
                print(f"Scene {i+1}: Sourcing high-res visual for '{kw}'...")
                p_url = f"https://image.pollinations.ai/p/cinematic%20dramatic%203D%20render%20{requests.utils.quote(kw)}?width=1080&height=1920&nologo=true&seed={random.randint(100, 999999)}"
                r = requests.get(p_url, timeout=20)
                if r.status_code == 200 and len(r.content) > 5000:
                    with open(f"clip_{i}.jpg", "wb") as f:
                        f.write(r.content)
                    saved = True
            except Exception:
                pass

        if not saved:
            Image.new('RGB', (1080, 1920), color=(15, 15, 30 + i * 15)).save(f"clip_{i}.jpg")


def render_video(metadata):
    audio = AudioFileClip("audio.mp3")
    total_dur = audio.duration
    scenes = metadata['scenes']
    scene_dur = total_dur / len(scenes)
    
    clips = []
    for i in range(len(scenes)):
        if os.path.exists(f"clip_{i}.mp4"):
            try:
                c = VideoFileClip(f"clip_{i}.mp4").without_audio()
                if c.duration < scene_dur:
                    c = c.loop(duration=scene_dur)
                else:
                    c = c.subclip(0, scene_dur)
                c = c.resize(height=1920)
                if c.w > 1080:
                    c = c.crop(x_center=c.w / 2, width=1080, height=1920)
                clips.append(c)
                continue
            except Exception as e:
                print(f"MoviePy fallback to image for clip {i}: {e}")

        img_path = f"clip_{i}.jpg"
        img = Image.open(img_path).resize((1080, 1920))
        img.save(img_path)
        img_clip = ImageClip(img_path).set_duration(scene_dur)
        img_clip = img_clip.resize(lambda t, dur=scene_dur: 1.0 + 0.10 * (t / dur))
        clips.append(img_clip)

    background_track = concatenate_videoclips(clips, method="compose").set_duration(total_dur)
    
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
    final_video.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac")


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
    print("1. Generating hooked script & visual breakdown...")
    meta = generate_ai_content()
    
    print("2. Synthesizing voiceover...")
    asyncio.run(make_male_voice(meta['voice_script']))
    
    print("3. Sourcing vertical clips for all 5 scenes...")
    fetch_scenes(meta['scenes'])
    
    print("4. Rendering composition...")
    render_video(meta)
    
    print("5. Publishing to YouTube...")
    post_to_youtube(meta)
