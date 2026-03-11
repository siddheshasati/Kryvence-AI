import os
import json
import asyncio
import subprocess
import webbrowser
import re
import requests
import logging
import keyboard
import sounddevice as sd
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from pywhatkit import search, playonyt
from groq import Groq
from AppOpener import close, open as appopen
from webbrowser import open as webopen
from scipy.io.wavfile import write
from acrcloud.recognizer import ACRCloudRecognizer
import screen_brightness_control as sbc

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey", "")

if not GroqAPIKey:
    logging.error("Groq API key is missing in the .env file.")

client = Groq(api_key=GroqAPIKey)
DATA_FOLDER = "Data"
os.makedirs(DATA_FOLDER, exist_ok=True)

useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
username = os.environ.get('Username', 'User')

# --- Enhanced Helper Functions ---

def YouTubeSearch(topic):
    url = f"https://www.youtube.com/results?search_query={topic}"
    webbrowser.open(url)
    return True

def PlayYoutube(query):
    playonyt(query)
    return True

def OpenApp(app, sess=requests.session()):
    try:
        # Attempt to open local application
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        # Fallback to web search if local app fails
        def extract_links(html):
            if not html: return []
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', {'jsname': 'UWckNb'})
            return [link.get('href') for link in links]

        def search_google(query):
            url = f"https://www.google.com/search?q={query}"
            headers = {"User-Agent": useragent}
            response = sess.get(url, headers=headers)
            return response.text if response.status_code == 200 else None

        html = search_google(app)
        links = extract_links(html)

        if links:
            webopen(links[0])
            return True
        else:
            logging.warning(f"No valid links found for opening {app}.")
            return False

def CloseApp(app):
    if "chrome" in app.lower():
        return False
    try:
        close(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        return False

def System(command):
    actions = {
        "mute": lambda: keyboard.press_and_release("volume mute"),
        "unmute": lambda: keyboard.press_and_release("volume mute"),
        "volume up": lambda: keyboard.press_and_release("volume up"),
        "volume down": lambda: keyboard.press_and_release("volume down")
    }
    
    # Check for volume actions
    if command in actions:
        actions[command]()
        return True
    # Check for brightness actions
    elif "brightness" in command:
        match = re.search(r'\d+', command)
        if match:
            sbc.set_brightness(int(match.group()))
            return True
    
    logging.warning(f"Unknown system command: {command}")
    return False

# --- Original Helper Functions ---

def TriggerImageGeneration(prompt):
    data_path = r"Frontend\Files\ImageGeneration.data"
    clean_prompt = prompt.lower().replace("generate image of", "").replace("create an image of", "").strip()
    try:
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        with open(data_path, "w", encoding="utf-8") as f:
            f.write(f"{clean_prompt},True")
        return f"🚀 Starting Gemini image generation for: {clean_prompt}"
    except Exception as e:
        return f"Failed to trigger generation: {e}"

async def IdentifyMusicACR():
    config = {
        'host': 'identify-ap-southeast-1.acrcloud.com', 
        'access_key': 'b3dd13b385f257d95b236d5aca0f6deb', 
        'access_secret': 'qaMXJfUSpqZPPBuLooSwkK7ZfYqpQLuZA5lSEswZ',
        'timeout': 10
    }
    fs, duration = 44100, 10 
    temp_file = "Frontend/Files/MusicSample.wav"
    try:
        logging.info("Listening to music...")
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        os.makedirs("Frontend/Files", exist_ok=True)
        write(temp_file, fs, recording)
        recognizer = ACRCloudRecognizer(config)
        result = json.loads(recognizer.recognize_by_file(temp_file, 0))
        if os.path.exists(temp_file): os.remove(temp_file)
        if result.get("status", {}).get("code") == 0:
            track = result["metadata"]["music"][0]
            return f"This is {track['title']} by {track['artists'][0]['name']}."
        return "Music could not be identified."
    except Exception as e:
        return f"Music ID Error: {e}"

def ContentWriterAI(prompt):
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant", 
        messages=[
            {"role": "system", "content": f"Hello, I am {username}, and you're a professional content writer. Write like a letter."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2048,
        temperature=0.7
    )
    return completion.choices[0].message.content.strip()

def Content(topic):
    topic_cleaned = topic.lower().replace(" ", "_")
    file_path = os.path.join(DATA_FOLDER, f"{topic_cleaned}.txt")
    content_by_ai = ContentWriterAI(topic)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content_by_ai)
    subprocess.Popen(["notepad.exe", file_path])
    return True

# --- Core Logic ---

async def TranslateAndExecute(commands: list[str]):
    funcs = []
    for command in commands:
        cmd_lower = command.lower().strip()
        
        if cmd_lower.startswith("open "):
            funcs.append(asyncio.to_thread(OpenApp, cmd_lower.removeprefix("open ")))
        
        elif cmd_lower.startswith("close "):
            funcs.append(asyncio.to_thread(CloseApp, cmd_lower.removeprefix("close ")))
            
        elif cmd_lower.startswith("play "):
            funcs.append(asyncio.to_thread(PlayYoutube, cmd_lower.removeprefix("play ")))
            
        elif cmd_lower.startswith("youtube search "):
            funcs.append(asyncio.to_thread(YouTubeSearch, cmd_lower.removeprefix("youtube search ")))

        elif cmd_lower.startswith("content "):
            funcs.append(asyncio.to_thread(Content, cmd_lower.removeprefix("content ")))
            
        elif "generate image" in cmd_lower or "create an image" in cmd_lower:
            print(TriggerImageGeneration(cmd_lower))
            
        elif "identify music" in cmd_lower or "what song" in cmd_lower:
            funcs.append(IdentifyMusicACR())
            
        elif cmd_lower.startswith("google search "):
            funcs.append(asyncio.to_thread(webbrowser.open, f"https://www.google.com/search?q={cmd_lower.removeprefix('google search ')}"))
            
        elif cmd_lower.startswith("system "):
            funcs.append(asyncio.to_thread(System, cmd_lower.removeprefix("system ")))
        else:
            logging.warning(f"No function found for command: {command}")

    return await asyncio.gather(*funcs)

async def Automation(commands: list[str]):
    results = await TranslateAndExecute(commands)
    for result in results:
        if result: logging.info(f"Execution Result: {result}")
    return True

if __name__ == "__main__":
    cmds = [
        "open notepad",
        "system volume up",
        "youtube search lofi hip hop"
    ]
    asyncio.run(Automation(cmds))