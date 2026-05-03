from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import os
import mtranslate as mt
from dotenv import dotenv_values
from time import sleep

# Load environment variables with a fallback to English if missing
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage", "en")

HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                recognition.start();
            };
            recognition.start();
        }

        function stopRecognition() {
            recognition.stop();
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''

# Inject the input language into the JS
HtmlCode = HtmlCode.replace("recognition.lang='';", f"recognition.lang='{InputLanguage}';")

# Ensure Data directory exists to prevent FileNotFoundError
os.makedirs("Data", exist_ok=True)

with open(r"Data\Voice.html", "w", encoding="utf-8") as f:
    f.write(HtmlCode)

current_dir = os.getcwd()
Link = f"{current_dir}/Data/Voice.html"

chrome_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')

# Auto-allows microphone permission without a popup
chrome_options.add_argument("--use-fake-ui-for-media-stream") 

# Hack to hide the window off-screen without triggering headless audio restrictions
chrome_options.add_argument("--window-position=-2000,0") 
chrome_options.add_argument("--window-size=100,100")

# Ensure Frontend/Files directory exists
TempDirPath = rf"{current_dir}/Frontend/Files"
os.makedirs(TempDirPath, exist_ok=True)

def SetAssistantStatus(Status):
    with open(rf'{TempDirPath}/Status.data', "w", encoding='utf-8') as file:
        file.write(Status)

def QueryModifier(Query):
    if not Query:
        return ""
        
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "whom", "whose", "which", "can", "what's", "where's", "how's", "is", "are"]

    is_question = any(new_query.startswith(word + " ") for word in question_words)
    
    if is_question:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] not in ['.', '?', '!']:
            new_query += "."

    return new_query.capitalize()

def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation.capitalize()

# ✅ GLOBAL DRIVER VARIABLE (starts empty)
driver = None

def SpeechRecognition():
    global driver
    
    # ✅ LAZY INITIALIZATION: Start Chrome only when this function is actually called
    if driver is None:
        print("\n[INFO] Starting Chrome for Speech Recognition...")
        print("[INFO] If this is your first time, Selenium is downloading the Chrome Driver.")
        print("[INFO] PLEASE DO NOT PRESS CTRL+C. Wait 30-60 seconds...\n")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("file:///" + Link)

    driver.find_element(By.ID, "start").click()

    while True:
        try:
            Text = driver.find_element(By.ID, "output").text
            if Text:
                driver.find_element(By.ID, "end").click()
                if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                    return QueryModifier(Text)
                else:
                    SetAssistantStatus("Translating...")
                    return QueryModifier(UniversalTranslator(Text))
        except Exception:
            # Prevents overwhelming the socket connection and maxing out CPU
            sleep(0.1)

if __name__ == "__main__":
    print("Listening for voice input...")
    try:
        while True:
            Text = SpeechRecognition()
            if Text:
                print(f"You said: {Text}")
    except KeyboardInterrupt:
        print("\nStopping Speech Recognition... Closing background browser.")
        if driver is not None:
            driver.quit()