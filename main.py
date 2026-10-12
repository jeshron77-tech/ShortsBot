import os
import json
import requests
import random
import time
import subprocess
from PIL import Image

# Fix Pillow 10+ backwards compatibility for MoviePy
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
        "You are a viral YouTube Shorts creator specializing in 'What If' mystery stories, like Zack D. Films.\n"
        "Pick an intense topic. Write a gripping 35-second script split into EXACTLY 5 sequential scenes (Timeline: Day 1, Day 3, Day 5, Day 7, Day 10).\n\n"
        "Respond ONLY in clean JSON without markdown codeblocks or extra text:\n"
        "{\n"
        '  "title": "[Viral title with emoji and #shorts]",\n'
        '  "description": "[2-sentence cliffhanger for comments]",\n'
        '  "tags": ["shorts", "whatif", "mindblown", "mystery"],\n'
        '  "voice_script": "[Punchy, dramatic 35-second script split across the 5 scenes]",\n'
        '  "scenes": [\n'
        '    {\n'
        '      "script_beat": "[Scene 1 narration]",\n'
        '      "search_keyword": "shocked person looking scared 3d animation dramatic face portrait",\n'
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Close-up portrait of stylized person looking shocked, dramatic cinematic lighting, vertical 9:16 aspect ratio"\n'
        '    },\n'
        '    {\n'
        '      "script_beat": "[Scene 2 narration]",\n'
        '      "search_keyword": "panic crowd city chaos night darkness emergency",\n'
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Medium shot showing sudden escalation, stylized people in panic, dark volumetric lighting, vertical 9:16 aspect ratio"\n'
        '    },\n'
        '    {\n'
        '      "script_beat": "[Scene 3 narration]",\n'
        '      "search_keyword": "planet earth disaster apocalyptic atmosphere dark glowing",\n'
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Wide cinematic angle of global catastrophe unfolding, stylized 3D earth environment, vertical 9:16 aspect ratio"\n'
        '    },\n'
        '    {\n'
        '      "script_beat": "[Scene 4 narration]",\n'
        '      "search_keyword": "terrified human face shadows intense nightmare",\n'
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Extreme close-up of stylized person realizing a terrifying truth, intense dramatic shadows, vertical 9:16 aspect ratio"\n'
        '    },\n'
        '    {\n'
        '      "script_beat": "[Scene 5 narration]",\n'
        '      "search_keyword": "mystery silhouette void cosmic strange final anomaly",\n'
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Climactic shocking twist finale, stylized characters freezing in place, vertical 9:16 aspect ratio"\n'
        '    }\n'
        '  ]\n'
        "}"
    )
    
    response = model.generate_content(prompt)
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_text)


def make_voice(text):
    print("Generating voiceover via Google TTS...")
    # Generate base voice
    tts = gTTS(text=text, lang='en', tld='com', slow=False)
    tts.save("temp_raw.mp3")
    
    # Pitch shift with FFmpeg: asetrate shifts pitch down, atempo normalizes playback speed
    print("Applying deep male narrator pitch transform via FFmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-i", "temp_raw.mp3",
        "-af", "asetrate=24000*0.80,aresample=24000,atempo=1.25",
        "audio.mp3"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FFmpeg audio filter warning: {res.stderr}")
        os.rename("temp_raw.mp3", "audio.mp3")
    else:
        print("Deep male voiceover generated successfully: audio.mp3")


def fetch_scene_images(scenes):
    print(f"Fetching {len(scenes)} distinct scene images...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for index, scene in enumerate(scenes):
        downloaded = False
        
        # 1. Primary Source: Pollinations AI with clean prompt
        prompt = scene.get('image_prompt', '3D dramatic cinematic animation character scene')
        encoded_prompt = requests.utils.quote(prompt)
        pollinations_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={random.randint(1000, 999999)}"
        
        try:
            print(f"Trying Pollinations for Scene {index+1}...")
            r = requests.get(pollinations_url, headers=headers, timeout=25)
            if r.status_code == 200 and len(r.content) > 5000:
                with open(f"scene_{index}.jpg", "wb") as f:
                    f.write(r.content)
                downloaded = True
                print(f"Scene {index+1} downloaded from Pollinations!")
        except Exception as e:
            print(f"Pollinations error on Scene {index+1}: {e}")
            
        # 2. Secondary Source: Unsplash Source fallback (Guaranteed real image)
        if not downloaded:
            keyword = scene.get('search_keyword', 'mystery,dark').replace(' ', ',')
            unsplash_url = f"https://source.unsplash.com/1080x1920/?{keyword}"
            try:
                print(f"Using secondary HD image source for Scene {index+1} ({keyword})...")
                r = requests.get(unsplash_url, headers=headers, timeout=20)
                if r.status_code == 200 and len(r.content) > 5000:
                    with open(f"scene_{index}.jpg", "wb") as f:
                        f.write(r.content)
                    downloaded = True
                    print(f"Scene {index+1} downloaded from secondary source!")
            except Exception as e:
                print(f"Secondary source error on Scene {index+1}: {e}")

        # 3. Last-resort fallback: If both network calls failed, copy from scene 0 rather than a black canvas
        if not downloaded:
            print(f"Re-using prior image for Scene {index+1} to avoid dark canvas...")
            if index > 0 and os.path.exists("scene_0.jpg"):
                with open("scene_0.jpg", "rb") as fsrc, open(f"scene_{index}.jpg", "wb") as fdst:
                    fdst.write(fsrc.read())
            else:
                img = Image.new('RGB', (1080, 1920), color=(20, 20, 45))
                img.save(f"scene_{index}.jpg")
                
        # Pause 2 seconds between requests to avoid rate limits
        time.sleep(2)


def mix_video_with_subtitles(metadata):
    audio = AudioFileClip("audio.mp3")
    total_duration = audio.duration
    
    scenes = metadata['scenes']
    num_scenes = len(scenes)
    duration_per_scene = total_duration / num_scenes
    
    scene_clips = []
    for i in range(num_scenes):
        img_path = f"scene_{i}.jpg"
        clip_dur = duration_per_scene if i < num_scenes - 1 else (total_duration - (i * duration_per_scene))
        
        img = Image.open(img_path).resize((1080, 1920))
        img.save(img_path)
        
        img_clip = ImageClip(img_path).set_duration(clip_dur)
        scene_clips.append(img_clip)
        
    print("Stitching all 5 scene clips sequentially...")
    background_track = concatenate_videoclips(scene_clips, method="compose")
    background_track = background_track.set_duration(total_duration)
    
    print("Generating synchronous subtitles...")
    words = metadata["voice_script"].split()
    phrases = [" ".join(words[i:i+3]) for i in range(0, len(words), 3)]
    duration_per_phrase = total_duration / len(phrases)
    text_clips = []
    
    current_time = 0
    for phrase in phrases:
        txt_clip = TextClip(
            phrase.upper(),
            fontsize=60,
            color='yellow',
            font='DejaVu-Sans-Bold',
            stroke_color='black',
            stroke_width=4,
            method='caption',
            size=(960, None)
        )
        txt_clip = txt_clip.set_start(current_time).set_duration(duration_per_phrase).set_pos('center')
        text_clips.append(txt_clip)
        current_time += duration_per_phrase
        
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
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload("final.mp4", chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    print(f"Uploaded successfully! Video ID: {response.get('id')}")


if __name__ == "__main__":
    print("1. Generating AI content & 5-Scene Breakdown...")
    meta = generate_ai_content()
    
    print("2. Generating Male Voiceover...")
    make_voice(meta['voice_script'])
    
    print("3. Fetching 5 Distinct Scene Images...")
    fetch_scene_images(meta['scenes'])
    
    print("4. Rendering 5-Scene Video & Subtitles...")
    mix_video_with_subtitles(meta)
    
    print("5. Uploading to YouTube...")
    post_to_youtube(meta)
