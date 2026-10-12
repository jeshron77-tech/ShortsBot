import os
import json
import requests
import random
from PIL import Image

# Fix Pillow 10+ backwards compatibility for MoviePy
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

from gtts import gTTS
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ImageClip

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")


def generate_ai_content():
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-3.8-flash')
    
    prompt = (
        "You are a viral YouTube Shorts creator specializing in 'What If' mystery stories, like Zack D. Films.\n"
        "Choose an extremely gripping, mind-bending topic and write a story split into 4 chronological visual scenes (Day 1, Day 3, Day 5, Day 10).\n\n"
        "Crucial: Break down the visual progress into exactly 4 sequential visual scenes matching your 35-second voice script, where 3D characters interact with what is happening.\n"
        "You MUST respond ONLY in clean JSON format with these exact keys (no markdown blocks, no prefix text):\n"
        "{\n"
        '  "title": "[Viral title with emoji and #shorts]",\n'
        '  "description": "[2-sentence cliffhanger description for comments]",\n'
        '  "tags": ["shorts", "whatif", "mindblown", "mystery"],\n'
        '  "voice_script": "[Punchy, dramatic 35-second script split into exactly 4 connected visual beats.]",\n'
        '  "scenes": [\n'
        '    {\n'
        '      "script_beat": "[The exact script spoken during this 8-9 second scene]",\n'
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Close-up/Medium cinematic view of [detailed description of a stylized person in a shocking situation matching the spoken beat, dramatic action, vibrant 3D renders, vertical 9:16 aspect ratio]"\n'
        '    },\n'
        '    {\n'
        '      "script_beat": "[The exact script spoken during this second 8-9 second scene]",\n'
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Cinematic [detailed camera view of what escalates, stylized 3D people react, highly detailed 3D assets, dark volumetric lighting, vertical 9:16 aspect ratio]"\n'
        '    },\n'
        '    {\n'
        '      "script_beat": "[The exact script spoken during this third 8-9 second scene]",\n'
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Low angle [detailed 3D escalation, shocking event, stylized cinematic characters fleeing or panicking, bright action lighting, vertical 9:16 aspect ratio]"\n'
        '    },\n'
        '    {\n'
        '      "script_beat": "[The climax script spoken during this last 8-9 second scene]",\n'
        '      "image_prompt": "3D animated style, Zack D. Films aesthetic. Extremely dramatic close-up [final shocking climax twist, stylized characters, dark atmospheric volumetric glow, high-intensity cinematic 3D, vertical 9:16 aspect ratio]"\n'
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
    tts.save("audio.mp3")
    print("Voiceover saved successfully to audio.mp3")


def fetch_scene_images(scenes):
    print("Fetching scene-specific AI images from Pollinations AI...")
    for index, scene in enumerate(scenes):
        prompt = scene['image_prompt']
        # URL encode prompt
        encoded_prompt = requests.utils.quote(prompt)
        url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1080&height=1920&seed={random.randint(1,9999999)}"
        
        try:
            print(f"Downloading Image for Scene {index+1}: {scene['script_beat'][:50]}...")
            res = requests.get(url, timeout=30)
            if res.status_code == 200:
                with open(f"scene_{index}.jpg", "wb") as f:
                    f.write(res.content)
            else:
                raise RuntimeError(f"Failed to generate image, status: {res.status_code}")
        except Exception as e:
            print(f"Error on Scene {index+1}, generating emergency color block: {e}")
            img = Image.new('RGB', (1080, 1920), color=(15, 15, 25 + index * 10))
            img.save(f"scene_{index}.jpg")


def mix_video_with_subtitles(metadata):
    audio = AudioFileClip("audio.mp3")
    total_duration = audio.duration
    
    scenes = metadata['scenes']
    num_scenes = len(scenes)
    duration_per_scene = total_duration / num_scenes
    
    scene_clips = []
    
    for i in range(num_scenes):
        start_t = i * duration_per_scene
        # Let image clip go slightly over or match the endpoint
        clip_dur = duration_per_scene if i < num_scenes - 1 else (total_duration - start_t)
        
        # Load the generated AI image for this scene
        img_clip = ImageClip(f"scene_{i}.jpg").set_duration(clip_dur).set_start(start_t)
        
        # Add a subtle, slow continuous 3D Zoom motion (Ken Burns)
        # Slow zoom factor from 1.0 to 1.15 over duration
        img_clip = img_clip.resize(lambda t: 1.0 + 0.15 * (t / clip_dur))
        
        scene_clips.append(img_clip)
        
    print("Layering text phrases on top of animated scenes...")
    words = metadata["voice_script"].split()
    phrases = [" ".join(words[i:i+3]) for i in range(0, len(words), 3)]
    duration_per_phrase = total_duration / len(phrases)
    text_clips = []
    
    current_time = 0
    for phrase in phrases:
        txt_clip = TextClip(
            phrase.upper(),
            fontsize=55,
            color='yellow',
            font='DejaVu-Sans-Bold',
            stroke_color='black',
            stroke_width=3,
            method='caption',
            size=(960, None) # Stay in portrait screen boundary
        )
        txt_clip = txt_clip.set_start(current_time).set_duration(duration_per_phrase).set_pos('center')
        text_clips.append(txt_clip)
        current_time += duration_per_phrase
        
    final_video = CompositeVideoClip(scene_clips + text_clips)
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
    print("1. Generating AI content & Scene Breakdown...")
    meta = generate_ai_content()
    
    print("2. Generating voiceover...")
    make_voice(meta['voice_script'])
    
    print("3. Generating scene-specific visual frames...")
    fetch_scene_images(meta['scenes'])
    
    print("4. Rendering Video with camera motion & dynamic subtitles...")
    mix_video_with_subtitles(meta)
    
    print("5. Uploading to YouTube...")
    post_to_youtube(meta)
