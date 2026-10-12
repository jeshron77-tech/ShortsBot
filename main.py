import os
import json
import requests
import random
from gtts import gTTS
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PIXABAY_KEY = (os.environ.get("PEXELS_API_KEY") or "").strip()


def generate_ai_content():
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-3.8-flash')
    
    prompt = (
        "You are a viral YouTube Shorts creator specializing in the 'What If' mystery niche. "
        "Choose an extremely gripping, mind-bending topic. "
        "The script MUST use psychological retention hooks: open with a shocking question, state an escalating timeline (Day 1, Day 3, Day 10), and end right before the absolute peak climax to force rewatches.\n\n"
        "Respond ONLY in clean JSON format with these exact keys:\n"
        "{\n"
        '  "title": "[Insert Viral Title with a Shocking Emoji and #shorts]",\n'
        '  "description": "[Insert a 2-sentence description that leaves a cliffhanger riddle for the comments section]",\n'
        '  "tags": ["shorts", "whatif", "mindblown", "viralscience", "mysteries"],\n'
        '  "voice_script": "[Insert a 35-second script with short, punching sentences. No introduction, start directly with the hook. Use dramatic words.]"\n'
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


def fetch_background(duration=35):
    search_terms = ["space", "galaxy", "abstract", "nature", "stars"]
    query = random.choice(search_terms)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_KEY}&q={query}&video_type=film&orientation=vertical"
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            hits = data.get('hits', [])
            if hits:
                random_video = random.choice(hits)
                video_url = (
                    random_video.get('videos', {}).get('large', {}).get('url')
                    or random_video.get('videos', {}).get('medium', {}).get('url')
                    or random_video.get('videos', {}).get('small', {}).get('url')
                )
                if video_url:
                    print(f"Downloading clip from Pixabay: {query}")
                    video_data = requests.get(video_url, headers=headers, timeout=30).content
                    with open("bg.mp4", "wb") as f:
                        f.write(video_data)
                    return
    except Exception as e:
        print(f"Pixabay request notice: {e}")

    # Rock-solid fallback: generate a 1080x1920 vertical canvas so the pipeline never stops
    print("Using dynamic vertical canvas for background...")
    clip = ColorClip(size=(1080, 1920), color=(15, 15, 25), duration=duration)
    clip.write_videofile("bg.mp4", fps=24, codec="libx264")


def mix_video_with_subtitles(metadata):
    audio = AudioFileClip("audio.mp3")
    video = VideoFileClip("bg.mp4")
    
    # Loop or trim background to match exact voiceover duration
    if video.duration < audio.duration:
        video = video.loop(duration=audio.duration)
    else:
        video = video.subclip(0, audio.duration)
        
    video = video.resize((1080, 1920))
    
    words = metadata["voice_script"].split()
    phrases = [" ".join(words[i:i+3]) for i in range(0, len(words), 3)]
    duration_per_phrase = audio.duration / len(phrases)
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
            size=(video.w - 120, None)
        )
        txt_clip = txt_clip.set_start(current_time).set_duration(duration_per_phrase).set_pos('center')
        text_clips.append(txt_clip)
        current_time += duration_per_phrase
        
    final_video = CompositeVideoClip([video] + text_clips)
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
    print("1. Generating AI content...")
    meta = generate_ai_content()
    
    print("2. Generating voiceover...")
    make_voice(meta['voice_script'])
    
    print("3. Fetching background video...")
    fetch_background()
    
    print("4. Rendering video with subtitles...")
    mix_video_with_subtitles(meta)
    
    print("5. Uploading to YouTube...")
    post_to_youtube(meta)
