import os
import json
import urllib.parse
import requests
import random
import subprocess
import time
from PIL import Image

if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

FALLBACK_SCRIPTS = [
    {
        "title": "What If The Megalodon Never Went Extinct? 🦈🌊 #shorts",
        "description": "What if the 60-foot apex predator still ruled our oceans?",
        "tags": ["shorts", "whatif", "megalodon", "ocean"],
        "voice_script": "What if the Megalodon never went extinct? Year 1, massive 60-foot sharks dominate global shipping lanes, flipping commercial fishing boats. Year 5, coastal beaches are permanently abandoned due to relentless attacks. Year 10, the global marine ecosystem collapses as Megalodons consume millions of whales and dolphins.",
        "image_prompts": ["giant megalodon shark underwater ocean", "massive shark attacking fishing boat", "abandoned coastal beach warning signs", "giant shark hunting sperm whale", "terrifying megalodon jaw open underwater"]
    },
    {
        "title": "What If Every Ant Turned Against Humans? 🐜⚠️ #shorts",
        "description": "Earth has 20 quadrillion ants. What if they organized?",
        "tags": ["shorts", "whatif", "ants", "creepy"],
        "voice_script": "What if every ant on Earth suddenly attacked humans? Hour 1, 20 quadrillion ants emerge from the ground, overwhelming sidewalks and homes. Day 3, massive super-colonies chew through underground power cables, causing global blackouts. Week 2, unstoppable swarms of army ants force humanity to flee onto the oceans.",
        "image_prompts": ["massive swarm of ants street", "ants chewing through electrical wires", "dark city blackout night creepy", "army ants swarming suburban house", "giant ant colony conquering city"]
    },
    {
        "title": "What If Spiders Grew As Big As Dogs? 🕷️😱 #shorts",
        "description": "The terrifying reality of giant arachnids. #shorts",
        "tags": ["shorts", "whatif", "spiders", "scary"],
        "voice_script": "What if spiders grew to the size of large dogs? Day 1, panic erupts as giant wolf spiders hunt stray animals in city streets. Day 5, massive webs the size of fishing nets cover suburban homes. Month 1, human populations are driven underground to escape the venomous hunters.",
        "image_prompts": ["giant spider walking down street", "massive spider web covering house", "terrifying large spider dark alley", "giant tarantula hunting in forest", "people hiding underground bunker dark"]
    },
    {
        "title": "What If Birds Suddenly Disappeared? 🦅❌ #shorts",
        "description": "What happens if every bird on Earth vanishes?",
        "tags": ["shorts", "whatif", "birds", "nature"],
        "voice_script": "What if every bird suddenly disappeared? Month 1, unchecked insect populations explode into massive, continent-sized swarms. Month 6, locust plagues devour global agricultural crops, causing devastating famines. Year 1, without birds spreading seeds, the world's forests begin a rapid and irreversible ecological collapse.",
        "image_prompts": ["empty sky no birds sun", "massive locust swarm eating crops", "dead agricultural farm famine wasteland", "dying forest without new seeds", "barren earth landscape ecological collapse"]
    },
    {
        "title": "What If Octopuses Evolved To Live On Land? 🐙🚶 #shorts",
        "description": "What if the smartest ocean predator walked among us?",
        "tags": ["shorts", "whatif", "octopus", "evolution"],
        "voice_script": "What if octopuses suddenly evolved to live on land? Month 1, thousands of highly intelligent, color-changing predators emerge from the oceans. Year 1, they learn to use human tools and weapons with their tentacles. Year 5, octopus colonies begin building their own advanced amphibious cities on the coastlines.",
        "image_prompts": ["octopus walking on coastal beach", "octopus holding human tools tentacles", "color changing octopus camouflage street", "futuristic amphibious underwater coastal city", "intelligent octopus looking at camera"]
    },
    {
        "title": "What If Dinosaurs Returned To Modern Cities? 🦖🏙️ #shorts",
        "description": "The ultimate Jurassic apocalypse in modern times.",
        "tags": ["shorts", "whatif", "dinosaur", "jurassic"],
        "voice_script": "What if dinosaurs suddenly respawned in modern cities? Minute 10, massive T-Rexes tear through downtown traffic like toys. Day 2, packs of raptors hunt humans trapped in skyscrapers and shopping malls. Month 1, military forces abandon major cities, leaving them as overgrown, prehistoric concrete jungles.",
        "image_prompts": ["t-rex roaring in city traffic", "raptors hunting in shopping mall", "military abandoning ruined city streets", "pterodactyl flying over skyscraper building", "overgrown ruined city dinosaur jungle"]
    },
    {
        "title": "What If Cats Turned Into Apex Predators? 🐈🐅 #shorts",
        "description": "What if your cute pet became a lethal hunter?",
        "tags": ["shorts", "whatif", "cats", "scary"],
        "voice_script": "What if house cats suddenly grew to the size of tigers? Hour 1, millions of indoor pets turn on their owners. Day 3, feral cat colonies overrun neighborhoods, hunting anything that moves. Month 1, human cities are completely abandoned, reclaimed by massive, silent feline predators.",
        "image_prompts": ["giant house cat hunting street", "massive feline predator in alley", "abandoned neighborhood overgrown wild cats", "giant cat sleeping on car", "human hiding from giant cat"]
    },
    {
        "title": "What If All Mosquitoes Were Eradicated? 🦟🌍 #shorts",
        "description": "Would killing all mosquitoes save us, or destroy nature?",
        "tags": ["shorts", "whatif", "mosquito", "science"],
        "voice_script": "What if every mosquito on Earth was wiped out? Day 1, global transmission of malaria and dengue fever stops completely. Month 3, populations of bats, frogs, and fish that rely on mosquito larvae drop sharply. Year 2, despite minor food chain disruptions, humanity thrives in a disease-free era.",
        "image_prompts": ["mosquito falling dying in air", "hospital empty no malaria patients", "starving frog in dark swamp", "bat flying catching insect night", "healthy human population futuristic city"]
    },
    {
        "title": "What If Dogs Could Speak Human Languages? 🐕🗣️ #shorts",
        "description": "What if man's best friend could finally talk?",
        "tags": ["shorts", "whatif", "dogs", "pets"],
        "voice_script": "What if dogs could suddenly speak human languages? Day 1, pets everywhere begin revealing their owners' deepest secrets to neighbors. Month 1, dogs are hired as elite security guards and police interrogators. Year 1, canine rights groups form, demanding equal pay, voting rights, and premium steaks for all dogs.",
        "image_prompts": ["dog talking to human owner", "police dog interrogating criminal room", "dogs protesting with signs street", "dog eating premium steak dinner", "dog sitting in office chair"]
    },
    {
        "title": "What If Rats Grew To The Size Of Wolves? 🐀🐺 #shorts",
        "description": "The horrific reality of giant city rodents.",
        "tags": ["shorts", "whatif", "rats", "monster"],
        "voice_script": "What if rats suddenly grew to the size of wolves? Day 1, giant rodents burst from the sewers, terrorizing subway stations. Week 1, massive rat packs chew through cars and steal food from grocery stores. Month 3, human populations abandon ground-level living, building fortress cities in the sky.",
        "image_prompts": ["giant rat in subway station", "massive rodent chewing car tire", "destroyed grocery store giant rat", "humans building futuristic sky fortress", "giant rat glowing eyes dark"]
    },
    {
        "title": "What If Whales Could Walk On Land? 🐋🌴 #shorts",
        "description": "What if the biggest animals on Earth left the ocean?",
        "tags": ["shorts", "whatif", "whales", "ocean"],
        "voice_script": "What if whales evolved giant legs and walked on land? Day 1, massive 100-ton leviathans crush highways and coastal towns as they emerge. Month 2, grazing herds of blue whales consume entire forests in a matter of days. Year 1, humanity builds massive concrete walls to keep leviathans out.",
        "image_prompts": ["giant whale walking out ocean", "whale crushing highway cars legs", "blue whale eating entire forest", "massive concrete wall protecting city", "giant terrestrial whale walking desert"]
    },
    {
        "title": "What If Snakes Had Wings? 🐍🦅 #shorts",
        "description": "The terrifying evolution of flying serpents.",
        "tags": ["shorts", "whatif", "snakes", "reptiles"],
        "voice_script": "What if all snakes suddenly developed wings? Day 1, venomous cobras drop from the sky into crowded city streets. Month 2, flying constrictors hunt birds into near extinction, disrupting the global food chain. Year 1, humanity lives under massive reinforced domes to escape the aerial serpent threat.",
        "image_prompts": ["venomous snake flying with wings", "flying cobra dropping into city", "flying snake hunting a bird", "massive protective dome over city", "dark sky filled flying snakes"]
    },
    {
        "title": "What If Bees Went Completely Extinct Today? 🐝💀 #shorts",
        "description": "The rapid collapse of Earth without bees.",
        "tags": ["shorts", "whatif", "bees", "nature"],
        "voice_script": "What if every bee on Earth died today? Month 1, global pollination fails, causing massive shortages of fruits and vegetables. Month 6, dairy and meat industries collapse as cows run out of alfalfa to eat. Year 2, global starvation wipes out half of humanity as ecosystems crumble.",
        "image_prompts": ["dead bee falling off flower", "empty grocery store produce section", "starving cow in dry field", "barren apocalyptic farmland cracked earth", "humanity struggling ruined future city"]
    },
    {
        "title": "What If Cheetahs Hunted In Packs of 100? 🐆💨 #shorts",
        "description": "The fastest land animals become an unstoppable army.",
        "tags": ["shorts", "whatif", "cheetah", "wildlife"],
        "voice_script": "What if cheetahs started hunting in massive packs of one hundred? Day 1, synchronized super-packs wipe out entire herds of wildebeests in minutes. Month 3, they begin expanding into human territories, easily outrunning vehicles and defenses. Year 1, the African savanna becomes completely uninhabitable for any other species.",
        "image_prompts": ["massive pack of cheetahs running", "cheetahs chasing cars down highway", "hundred cheetahs hunting in savanna", "abandoned safari village torn apart", "cheetahs standing over defeated prey"]
    },
    {
        "title": "What If Cockroaches Became Indestructible? 🪳🛡️ #shorts",
        "description": "What if the ultimate survivors became truly invincible?",
        "tags": ["shorts", "whatif", "insects", "survival"],
        "voice_script": "What if cockroaches became completely indestructible? Week 1, exterminators realize poisons, fire, and crushing force have zero effect. Month 3, trillions of roaches overrun restaurants, homes, and hospitals. Year 1, humans are forced to abandon Earth's surface, retreating to sterile underwater habitats to escape the immortal insect plague.",
        "image_prompts": ["indestructible cockroach surviving fire explosion", "restaurant kitchen overrun massive cockroaches", "hospital abandoned covered in bugs", "futuristic sterile underwater human city", "immortal cockroach glowing armor close-up"]
    },
    {
        "title": "What If Pigeons Organized City Takeovers? 🕊️🏢 #shorts",
        "description": "The feathered menace reclaims the urban jungle.",
        "tags": ["shorts", "whatif", "birds", "cities"],
        "voice_script": "What if pigeons developed advanced collective intelligence? Day 1, millions of birds coordinate to block traffic and shatter skyscraper windows. Month 2, they intentionally drop corrosive waste to destroy power grids and cell towers. Year 1, humanity surrenders the major metropolitan cities to the new avian overlords.",
        "image_prompts": ["massive flock pigeons blocking traffic", "pigeons shattering glass skyscraper window", "corrosive bird waste destroying powerline", "ruined city ruled by pigeons", "pigeon sitting on abandoned car"]
    },
    {
        "title": "What If Earthworms Consumed All Concrete? 🪱🏗️ #shorts",
        "description": "What if a mutated worm species ate our cities?",
        "tags": ["shorts", "whatif", "science", "disaster"],
        "voice_script": "What if mutated earthworms began digesting concrete? Week 1, microscopic cracks appear in bridges and highways worldwide. Month 1, entire skyscrapers suddenly collapse as their foundations are eaten away into dust. Year 1, modern civilization falls back to the Stone Age, forced to rebuild everything using only wood and steel.",
        "image_prompts": ["mutated glowing earthworm eating concrete", "highway bridge crumbling into dust", "skyscraper collapsing falling apart city", "humans building wooden futuristic city", "close up worm eating cement"]
    },
    {
        "title": "What If Jellyfish Grew To The Size Of Ships? 🪼🚢 #shorts",
        "description": "The oceans become a lethal, electrified nightmare.",
        "tags": ["shorts", "whatif", "ocean", "jellyfish"],
        "voice_script": "What if deep sea jellyfish grew to the size of cruise ships? Day 1, massive glowing tentacles wrap around commercial submarines, crushing them instantly. Month 3, toxic electrified venom poisons the coastlines, making the ocean deadly to touch. Year 1, all international maritime shipping and sea travel ceases completely.",
        "image_prompts": ["giant glowing jellyfish underwater ocean", "jellyfish tentacles crushing submarine deep", "toxic glowing water coastal beach", "abandoned cruise ship floating ocean", "massive jellyfish floating deep sea"]
    },
    {
        "title": "What If Gorillas Entered The Stone Age? 🦍🪨 #shorts",
        "description": "A new intelligent species emerges in the jungle.",
        "tags": ["shorts", "whatif", "gorillas", "evolution"],
        "voice_script": "What if gorillas suddenly entered the Stone Age? Year 1, they begin crafting sharp spears and forming organized tribal armies. Year 5, they successfully domesticate wild jungle predators to ride into battle. Year 10, humanity is forced to negotiate peace treaties as the gorillas establish their own sovereign nation.",
        "image_prompts": ["gorilla crafting stone spear jungle", "organized gorilla tribal army standing", "gorilla riding wild tiger battle", "human negotiating peace with gorilla", "advanced gorilla tribal village jungle"]
    },
    {
        "title": "What If Frogs Ruled The Swamps Again? 🐸🌿 #shorts",
        "description": "The terrifying return of prehistoric giant amphibians.",
        "tags": ["shorts", "whatif", "frogs", "swamp"],
        "voice_script": "What if frogs evolved back into massive prehistoric predators? Month 1, 10-foot-tall amphibians begin swallowing alligators and livestock whole. Month 4, their deafening mating calls trigger massive earthquakes in marshland regions. Year 1, the southern coastlines are abandoned to the giant frogs as humans flee to the mountains.",
        "image_prompts": ["giant prehistoric frog swamp predator", "massive frog swallowing an alligator", "giant frog roaring swamp earthquake", "abandoned flooded coastal town ruins", "giant frog sitting in mud"]
    },
    {
        "title": "What If Bears Stopped Hibernating Completely? 🐻❄️ #shorts",
        "description": "Winter is no longer safe from apex predators.",
        "tags": ["shorts", "whatif", "bears", "winter"],
        "voice_script": "What if bears never hibernated again? Month 1, starving grizzlies invade snowy mountain towns in search of food. Month 3, desperate packs of bears learn to break into cars and homes. Year 1, winter tourism vanishes entirely as the snowy wilderness becomes a deadly hunting ground.",
        "image_prompts": ["starving grizzly bear snowy town", "bear breaking into winter cabin", "abandoned ski resort covered snow", "bear hunting in deep snow", "ferocious bear roaring winter night"]
    },
    {
        "title": "What If Tigers Became Fully Aquatic Hunters? 🐅💧 #shorts",
        "description": "The jungle cats take over the oceans.",
        "tags": ["shorts", "whatif", "tigers", "ocean"],
        "voice_script": "What if tigers evolved to hunt in the ocean? Day 1, apex cats with webbed paws begin ambushing deep sea divers. Month 3, they replace sharks as the absolute terrors of the coral reefs. Year 1, swimming in the ocean is globally banned due to unstoppable underwater tiger strikes.",
        "image_prompts": ["tiger swimming fast underwater ocean", "tiger with webbed paws diving", "tiger hunting fish coral reef", "abandoned beach warning signs ocean", "tiger underwater staring at camera"]
    },
    {
        "title": "What If Crocodiles Swam In Every Ocean? 🐊🌊 #shorts",
        "description": "The ultimate reptilian invasion of global waters.",
        "tags": ["shorts", "whatif", "crocodile", "monster"],
        "voice_script": "What if saltwater crocodiles invaded every ocean on Earth? Week 1, massive 20-foot reptiles swarm popular tourist beaches worldwide. Month 4, they begin attacking and sinking small fishing boats. Year 1, marine ecosystems collapse as millions of armored predators eat everything from fish to great white sharks.",
        "image_prompts": ["massive crocodile swimming deep ocean", "crocodile swarming popular tourist beach", "giant crocodile attacking fishing boat", "crocodile fighting great white shark", "armored reptile swimming dark water"]
    },
    {
        "title": "What If Kangaroos Invaded North America? 🦘🌎 #shorts",
        "description": "An unstoppable marsupial takeover of the West.",
        "tags": ["shorts", "whatif", "kangaroo", "wildlife"],
        "voice_script": "What if millions of kangaroos were dropped into North America? Month 1, massive bouncing herds destroy agricultural farmlands across the Midwest. Month 6, their aggressive kicks make national parks too dangerous for humans. Year 2, native deer populations go completely extinct as the invasive marsupials take over.",
        "image_prompts": ["massive herd kangaroos midwest farm", "kangaroo destroying agricultural crop field", "aggressive kangaroo national park forest", "extinct deer skeletons wild grass", "kangaroos hopping down empty highway"]
    },
    {
        "title": "What If Bats Swarmed During The Day? 🦇☀️ #shorts",
        "description": "The dark creatures of the night conquer the sun.",
        "tags": ["shorts", "whatif", "bats", "scary"],
        "voice_script": "What if billions of bats suddenly became day-walkers? Day 1, screeching black clouds blot out the sun over major cities. Month 3, aggressive swarms ground all commercial airplanes due to constant engine strikes. Year 1, humans are forced to wear heavy protective gear just to walk outside.",
        "image_prompts": ["massive swarm bats blocking sun", "bats flying through city skyscrapers", "commercial airplane flying through bats", "human wearing protective armor daytime", "black cloud bats blue sky"]
    },
    {
        "title": "What If Wolves Hunted In Mega-Packs of 1000? 🐺🌲 #shorts",
        "description": "The ultimate organized forest predators.",
        "tags": ["shorts", "whatif", "wolves", "nature"],
        "voice_script": "What if wolves formed mega-packs of one thousand? Week 1, highly organized armies wipe out entire moose and elk populations in days. Month 3, they begin surrounding rural human towns, cutting off supply roads. Year 1, humanity builds massive electric fences to defend against the forest sieges.",
        "image_prompts": ["massive pack thousand wolves forest", "wolves surrounding rural human town", "wolves blocking snowy supply road", "giant electric fence protecting city", "alpha wolf glowing eyes night"]
    },
    {
        "title": "What If Elephants Evolved Thick Armor? 🐘🛡️ #shorts",
        "description": "The gentle giants become indestructible tanks.",
        "tags": ["shorts", "whatif", "elephant", "evolution"],
        "voice_script": "What if elephants suddenly evolved impenetrable bone armor? Day 1, poachers realize their weapons bounce completely off the giant beasts. Month 6, unstoppable armored herds bulldoze entire human cities to reclaim their ancient migration routes. Year 2, humanity surrenders the savannas to the unstoppable living tanks.",
        "image_prompts": ["elephant with thick bone armor", "bullet bouncing off armored elephant", "elephant bulldozing human city building", "armored elephant herd savanna sunset", "indestructible living tank animal close-up"]
    },
    {
        "title": "What If Deep Sea Anglerfish Hunted In Rivers? 🐟🎣 #shorts",
        "description": "The nightmares of the abyss come to the surface.",
        "tags": ["shorts", "whatif", "ocean", "monster"],
        "voice_script": "What if deep sea anglerfish migrated into freshwater rivers? Week 1, glowing lures begin terrifying fishermen in shallow lakes. Month 3, the razor-toothed monsters decimate native freshwater fish populations. Year 1, entering any river or lake becomes a deadly gamble against the glowing, invisible predators.",
        "image_prompts": ["glowing anglerfish shallow river water", "anglerfish attacking fisherman small boat", "razor teeth fish murky lake", "warning sign bloody river bank", "glowing lure dark water surface"]
    },
    {
        "title": "What If Owls Hunted Humans At Night? 🦉👁️ #shorts",
        "description": "The silent assassins of the dark sky.",
        "tags": ["shorts", "whatif", "owls", "scary"],
        "voice_script": "What if owls mutated to hunt humans in the dark? Day 1, completely silent, giant aerial predators begin swooping down on people walking home at night. Month 3, city streets are strictly placed under curfew after sundown. Year 1, humans are forced to live in absolute fear of the night sky.",
        "image_prompts": ["giant owl swooping dark street", "owl glowing eyes night sky", "city street curfew abandoned night", "human running from flying shadow", "silent aerial predator moonlight"]
    },
    {
        "title": "What If Fish Learned To Walk On Land Again? 🐟🚶 #shorts",
        "description": "The oceans empty onto the continents.",
        "tags": ["shorts", "whatif", "fish", "evolution"],
        "voice_script": "What if millions of fish evolved lungs and legs overnight? Day 1, bizarre crawling fish flood coastal highways, causing massive traffic crashes. Month 6, amphibians adapt to breathe air, invading suburban pools and lakes. Year 2, land predators feast, triggering a bizarre global evolutionary reset.",
        "image_prompts": ["fish walking on legs highway", "massive swarm crawling fish street", "fish swimming in suburban pool", "bear eating walking fish forest", "bizarre evolutionary creature land water"]
    }
]

HIGHRES_BACKUPS = [
    "https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?w=1080&h=1920&fit=crop", 
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&h=1920&fit=crop", 
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1080&h=1920&fit=crop", 
    "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1080&h=1920&fit=crop", 
    "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=1920&fit=crop"
]

NICHES = [
    "dangerous predatory animal mutations and giant beasts",
    "extinct ancient creatures returning to modern earth",
    "massive insect swarms, plagues, and bug adaptations",
    "deep sea monsters and aquatic evolutionary anomalies",
    "domestic pets turning wild, feral, or highly intelligent",
    "wildlife taking over human cities and infrastructure"
]

def get_channel_recent_titles():
    titles = []
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
            yt = build("youtube", "v3", credentials=creds)
            ch_resp = yt.channels().list(mine=True, part="contentDetails").execute()
            uploads_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            pl_resp = yt.playlistItems().list(playlistId=uploads_id, part="snippet", maxResults=20).execute()
            for item in pl_resp.get("items", []):
                titles.append(item["snippet"]["title"].lower())
    except Exception:
        pass
    return titles

def generate_ai_content(past_titles):
    selected_niche = random.choice(NICHES)
    prompt = (
        f"You are Zack D. Films creating a viral YouTube Short about {selected_niche}.\n"
        f"CRITICAL: Do NOT write about any of these recent topics: {past_titles}\n"
        "Pick a BRAND NEW, completely unique 'What If' scenario.\n\n"
        "RULES:\n"
        "1. Sentence 1 MUST start with 'What if [Unique Scenario]?'\n"
        "2. Follow with rapid timeline: 'Day 1...', 'Day 3...', 'Day 5...', 'Day 10...' (or Seconds/Minutes/Hours).\n"
        "3. Total voice script length: 45 to 55 words.\n"
        "4. Provide EXACTLY 5 concise visual prompts (3 to 6 words each) in 'image_prompts'.\n\n"
        "Respond ONLY in valid JSON:\n"
        "{\n"
        '  "title": "[Unique Title #shorts]",\n'
        '  "description": "[Description]",\n'
        '  "tags": ["shorts", "whatif", "mystery"],\n'
        '  "voice_script": "What if [Scenario]? Day 1, [Event]. Day 3, [Escalation]. Day 5, [Catastrophe]. Day 10, [Climax]...",\n'
        '  "image_prompts": [\n'
        '    "giant wolf hunting city street",\n'
        '    "massive swarm locusts black sky"\n'
        '  ]\n'
        "}"
    )

    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        for model_name in ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-1.5-flash-8b']:
            try:
                print(f"Requesting novel script ({selected_niche}) from {model_name}...")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_text)
                if "image_prompts" in parsed and len(parsed["image_prompts"]) >= 5:
                    if not any(past in parsed["title"].lower() for past in past_titles):
                        print(f"Generated successfully: {parsed['title']}")
                        return parsed
            except Exception as e:
                print(f"Model {model_name} error: {e}")

    print("Selecting an unrepeated scenario from fallback library...")
    available = [s for s in FALLBACK_SCRIPTS if not any(p in s["title"].lower() for p in past_titles)]
    return random.choice(available if available else FALLBACK_SCRIPTS)

def make_male_voice(text):
    print("Generating voiceover via Piper neural TTS...")
    with open("script_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    subprocess.run(["python", "-m", "piper", "--model", "en_US-lessac-medium.onnx", "--output_file", "temp_voice.wav"], stdin=open("script_text.txt", "rb"), check=True)
    subprocess.run(["ffmpeg", "-y", "-i", "temp_voice.wav", "-filter:a", "compand=.3|.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2", "audio.mp3"], check=True)

def fetch_and_animate_scenes(image_prompts, duration_per_scene):
    print(f"Rendering 5 cinematic scenes ({duration_per_scene:.2f}s each) with FLUX.1-schnell...")
    total_frames = int(duration_per_scene * 24)
    
    # 1. ANTI-BOT HEADERS: We must trick Cloudflare into thinking this is a real human on Google Chrome
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    for i, raw_prompt in enumerate(image_prompts[:5]):
        img_file = f"raw_{i}.jpg"
        clip_file = f"motion_{i}.mp4"
        
        # 2. NANO BANANA STYLE INJECTION: Forces FLUX.1-schnell to make it vibrant, 3D, and hyper-realistic
        clean_p = f"{raw_prompt}, Nano Banana style, viral youtube shorts aesthetic, 3D hyper-realistic, vibrant exaggerated colors, Unreal Engine 5 render, 8k resolution"
        
        encoded = urllib.parse.quote(clean_p)
        seed = random.randint(100, 999999)
        # 3. EXPLICIT FLUX MODEL parameter
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&seed={seed}&nologo=true&model=flux"
        
        downloaded = False
        
        for attempt in range(3):
            try:
                print(f"Downloading scene {i+1}/5: {raw_prompt} (Attempt {attempt+1})...")
                r = requests.get(url, headers=headers, timeout=60)
                
                # Check if it actually downloaded an image and not a Cloudflare error page
                if r.status_code == 200 and len(r.content) > 30000:
                    with open(img_file, "wb") as f:
                        f.write(r.content)
                    base_img = Image.open(img_file).convert("RGB").resize((1080, 1920))
                    base_img.save(img_file, quality=95)
                    downloaded = True
                    print(f"✅ Scene {i+1} FLUX.1-schnell generation successful!")
                    break
                else:
                    print(f"Server blocked request or image too small. Status code: {r.status_code}")
            except Exception as e:
                print(f"Pollinations timeout: {e}")
            
            # 4. MASSIVE 15 SECOND DELAY on retry to guarantee IP unblock
            print("Sleeping for 15 seconds before retry...")
            time.sleep(15)
                
        if not downloaded:
            print(f"⚠️ Using high-res photographic backup for scene {i+1}...")
            backup_url = HIGHRES_BACKUPS[i % len(HIGHRES_BACKUPS)]
            try:
                r_backup = requests.get(backup_url, headers=headers, timeout=20)
                with open(img_file, "wb") as f:
                    f.write(r_backup.content)
                base_img = Image.open(img_file).convert("RGB").resize((1080, 1920))
                base_img.save(img_file, quality=95)
            except Exception:
                pass
            
        zoom_filter = f"zoompan=z='min(pzoom+0.003,1.25)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=24"
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", img_file,
            "-vf", zoom_filter,
            "-t", str(duration_per_scene),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
            clip_file
        ]
        subprocess.run(cmd, check=True)
        
        # 5. MASSIVE 15 SECOND DELAY between successful images
        print("Cooling down 15 seconds to respect server limits...")
        time.sleep(15)

def render_video(metadata):
    audio = AudioFileClip("audio.mp3")
    total_dur = audio.duration
    prompts = metadata.get('image_prompts', [])[:5]
    duration_per_scene = total_dur / len(prompts)
    
    fetch_and_animate_scenes(prompts, duration_per_scene)
    
    video_clips = []
    for i in range(len(prompts)):
        c = VideoFileClip(f"motion_{i}.mp4").subclip(0, duration_per_scene).set_duration(duration_per_scene)
        video_clips.append(c)
        
    background_track = concatenate_videoclips(video_clips, method="chain").set_duration(total_dur)
    
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
    final_video = final_video.set_audio(audio).set_duration(total_dur)
    
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

    try:
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
    except Exception as e:
        print(f"YOUTUBE UPLOAD FAILED: {e}")

if __name__ == "__main__":
    print("1. Generating unique topic...")
    meta = generate_ai_content(get_channel_recent_titles())
    
    print("2. Synthesizing Piper neural voice...")
    make_male_voice(meta['voice_script'])
    
    print("3. Assembling video and subtitles...")
    render_video(meta)
    
    print("4. Publishing to YouTube...")
    post_to_youtube(meta)
