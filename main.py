import os
import json
import requests
import random
from gtts import gTTS
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PIXABAY_KEY = os.environ.get("PEXELS_API_KEY")


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


def fetch_background():
    search_terms = ["space", "nature", "galaxy", "abstract", "ocean"]
    query = random.choice(search_terms)
    
    url = f"https://pixabay.com/api/videos/?key={PIXABAY_KEY}&q={query}&video_type=film&orientation=vertical"
    res = requests.get(url)
    data = res.json()
    hits = data.get('hits', [])
    
    if not hits:
        raise RuntimeError(f"No Pixabay videos found for query: {query}")
        
    random_video = random.choice(hits)
    video_url = random_video['videos']['large']['url']
    if not video_url:
        video_url = random_video['videos']['medium']['url']
        
    print(f"Downloading background clip from Pixabay: {query}")
    with open("bg.mp4", "wb") as f:
        f.write(requests.get(video_url).content)


def mix_video_with_subtitles(metadata):
    audio = AudioFileClip("audio.mp3")
    video = VideoFileClip("bg.mp4").subclip(0, audio.duration)
    
    words = metadata["voice_script"].split()
    phrases = [" ".join(words[i:i+3]) for i in range(0, len(words), 3)]
    duration_per_phrase = audio.duration / len(phrases)
    text_clips = []
    
    current_time = 0
    for phrase in phrases:
        txt_clip = TextClip(
            phrase.upper(),
            fontsize=45,
            color='yellow',
            font='DejaVu-Sans-Bold',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(video.w - 100, None)
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
