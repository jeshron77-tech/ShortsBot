import os
import json
import requests
import random
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
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Close-up portrait of stylized person looking shocked, bright dramatic cinematic lighting, highly detailed 3D character, vertical 9:16 aspect ratio"\n'
        '    },\n'
        '    {\n'
        '      "script_beat": "[Scene 2 narration]",\n'
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Medium shot showing sudden escalation, stylized people in panic, dark volumetric lighting, vertical 9:16 aspect ratio"\n'
        '    },\n'
        '    {\n'
        '      "script_beat": "[Scene 3 narration]",\n'
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Wide cinematic angle of global catastrophe unfolding, stylized 3D earth environment, eerie glowing atmosphere, vertical 9:16 aspect ratio"\n'
        '    },\n'
        '    {\n'
        '      "script_beat": "[Scene 4 narration]",\n'
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Extreme close-up of stylized person realizing a terrifying truth, intense dramatic shadows, high detail 3D render, vertical 9:16 aspect ratio"\n'
        '    },\n'
        '    {\n'
        '      "script_beat": "[Scene 5 narration]",\n'
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Climactic shocking twist finale, stylized characters freezing in place, apocalyptic volumetric lighting, vertical 9:16 aspect ratio"\n'
        '    }\n'
        '  ]\n'
        "}"
    )
    
    response = model.generate_content(prompt)
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_text)


def make_voice(text):
    print("Generating voiceover via Google TTS...")
    tts = gTTS(text=text, lang='en', tld='com', slow=False)
    tts.save("temp_raw.mp3")
    
    # Use FFmpeg to lower voice pitch into a deep, authoritative male narrator tone
    print("Applying deep male voice filter via FFmpeg...")
    cmd = [
        "ffmpeg", "-y", "-i", "temp_raw.mp3",
        "-filter:a", "asetrate=24000*0.82,aresample=24000,atempo=1/0.82",
        "audio.mp3"
    ]
    subprocess.run(cmd, check=True)
    print("Male voiceover ready: audio.mp3")


def fetch_scene_images(scenes):
    print(f"Fetching {len(scenes)} scene-specific AI images from Pollinations AI...")
    for index, scene in enumerate(scenes):
        prompt = scene['image_prompt']
        encoded_prompt = requests.utils.quote(prompt)
        url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1080&height=1920&seed={random.randint(1,9999999)}"
        
        try:
            print(f"Downloading Image {index+1}/{len(scenes)}: {scene['script_beat'][:40]}...")
            res = requests.get(url, timeout=35)
            if res.status_code == 200:
                with open(f"scene_{index}.jpg", "wb") as f:
                    f.write(res.content)
            else:
                raise RuntimeError(f"HTTP {res.status_code}")
        except Exception as e:
            print(f"Fallback generated for Scene {index+1}: {e}")
            img = Image.new('RGB', (1080, 1920), color=(15 + index * 10, 15, 30))
            img.save(f"scene_{index}.jpg")


def mix_video_with_subtitles(metadata):
    audio = AudioFileClip("audio.mp3")
    total_duration = audio.duration
    
    scenes = metadata['scenes']
    num_scenes = len(scenes)
    duration_per_scene = total_duration / num_scenes
    
    scene_clips = []
    for i in range(num_scenes):
        # Build individual clip per scene
        img_clip = (ImageClip(f"scene_{i}.jpg")
                    .set_duration(duration_per_scene)
                    .resize((1080, 1920)))
        
        # Subtle slow zoom effect for camera motion
        img_clip = img_clip.resize(lambda t, dur=duration_per_scene: 1.0 + 0.12 * (t / dur))
        scene_clips.append(img_clip)
        
    # Concatenate all 5 clips so they play sequentially
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
    
    print("3. Generating 5 Scene Visuals...")
    fetch_scene_images(meta['scenes'])
    
    print("4. Rendering 5-Scene Video with Zoom & Subtitles...")
    mix_video_with_subtitles(meta)
    
    print("5. Uploading to YouTube...")
    post_to_youtube(meta)
