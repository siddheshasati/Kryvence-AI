from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus,
    InitializeEnvironment,
    GetSayAloudStatus,
    SetSayAloudStatus
)
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from Backend.UploadProcessor import process_uploaded_file, answer_question_about_upload, has_upload_context

from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os
import re
import sys

# --- Setup ---
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
DefaultMessage = f'''{Username} : Hello {Assistantname}, How are you?
{Assistantname} : Welcome {Username}. I am doing well. How may I help you?'''

Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

QuickActionReplies = {
    "create images": "Describe the object, scene, or style you want in the image. Example: a futuristic bike in a rainy neon city.",
    "create image": "Describe the object, scene, or style you want in the image. Example: a futuristic bike in a rainy neon city.",
    "generate image": "Describe the object, scene, or style you want in the image. Example: a futuristic bike in a rainy neon city.",
    "generate images": "Describe the object, scene, or style you want in the image. Example: a futuristic bike in a rainy neon city.",
    "help me to learn": "What topic do you want to learn, and what is your current level: beginner, intermediate, or advanced?",
    "help me learn": "What topic do you want to learn, and what is your current level: beginner, intermediate, or advanced?",
    "take my interview": "Which role, subject, or exam should I interview you for? Also tell me your difficulty level.",
    "write codes": "What should I build or code? Tell me the language, features, and any error or requirement you have.",
    "write code": "What should I build or code? Tell me the language, features, and any error or requirement you have."
}

def NormalizeQuickAction(Query):
    return Query.strip().lower().strip(".!?")

def HandleQuickAction(Query):
    reply = QuickActionReplies.get(NormalizeQuickAction(Query))
    if not reply:
        return False
    if NormalizeQuickAction(Query) == "take my interview":
        SetSayAloudStatus("True")
    ShowTextToScreen(f"{Assistantname} : {reply}")
    SetAssistantStatus("Waiting...")
    SpeakIfAllowed(reply)
    return True

def ExtractImagePrompt(Query):
    query = Query.strip()
    match = re.match(
        r"^(?:please\s+)?(?:generate|create|make|draw)\s+(?:me\s+)?(?:an?\s+)?(?:image|images|picture|pictures|photo|photos|art|drawing)\s*(?:of|for|about)?\s+(.+)$",
        query,
        flags=re.IGNORECASE
    )
    if match:
        return match.group(1).strip(" .")

    lower_query = query.lower()
    if any(word in lower_query for word in ["generate", "create", "make", "draw"]) and any(word in lower_query for word in ["image", "picture", "photo"]):
        cleaned = re.sub(r"\b(generate|create|make|draw|me|an?|the|image|images|picture|pictures|photo|photos|of|for|about)\b", " ", query, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
        return cleaned

    return ""

def HandleImageGenerationRequest(Query):
    final_prompt = ExtractImagePrompt(Query)
    if not final_prompt:
        return False

    SetAssistantStatus("Generating...")
    with open(TempDirectoryPath("ImageGeneration.data"), "w", encoding="utf-8") as file:
        file.write(f"{final_prompt},True")
    ShowTextToScreen(f"{Assistantname} : Generating image for: {final_prompt}")
    print(f"--- Triggered Image Gen for: {final_prompt} ---")
    return True

def SpeakIfAllowed(Text):
    if GetSayAloudStatus() == "True":
        TextToSpeech(Text)

def ShouldUseUploadedContext(Query):
    if not has_upload_context():
        return False
    query = Query.lower()
    upload_words = [
        "this file", "this pdf", "this document", "this resume", "uploaded",
        "resume", "ats", "score", "document", "pdf", "docx", "image",
        "what is written", "summarize", "explain this", "answer from",
        "improve", "improvement", "suggest", "suggestion", "skills",
        "experience", "education", "projects", "job", "role", "match",
        "what about it", "how is it", "is it good"
    ]
    return any(word in query for word in upload_words)

def HandleUploadedQuestion(Query):
    if not ShouldUseUploadedContext(Query):
        return False
    SetAssistantStatus("Reading upload...")
    Answer = answer_question_about_upload(Query)
    if not Answer:
        return False
    ShowTextToScreen(f"{Assistantname} : {Answer}")
    SetAssistantStatus("Answering...")
    SpeakIfAllowed(Answer)
    return True

def HandleFileUpload():
    upload_path = TempDirectoryPath("UploadedFile.data")
    if not os.path.exists(upload_path):
        return False
    try:
        with open(upload_path, "r", encoding="utf-8") as file:
            path = file.read().strip()
        try:
            os.remove(upload_path)
        except OSError:
            pass
        if not path:
            return False
        SetAssistantStatus("Analyzing upload...")
        Answer = process_uploaded_file(path)
        ShowTextToScreen(f"{Assistantname} : {Answer}")
        SetAssistantStatus("Ready...")
        SpeakIfAllowed(Answer)
        return True
    except Exception as e:
        print(f"Upload Processing Error: {e}")
        SetAssistantStatus("Error...")
        return False

def ShowDefaultChatIfNoChats():
    if not os.path.exists(r'Data\ChatLog.json'):
        with open(r'Data\ChatLog.json', 'w', encoding='utf-8') as file:
            json.dump([], file)
    with open(r'Data\ChatLog.json', "r", encoding='utf-8') as file:
        if len(file.read()) < 5:
            with open(TempDirectoryPath('Database.data'), "w", encoding='utf-8') as db_file:
                db_file.write("")
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as res_file:
                res_file.write(DefaultMessage)

def ReadChatLogJson():
    with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:
        try:
            chatlog_data = json.load(file)
        except json.JSONDecodeError:
            chatlog_data = []
    return chatlog_data

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User: {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant: {entry['content']}\n"
    formatted_chatlog = formatted_chatlog.replace("User", Username + " ")
    formatted_chatlog = formatted_chatlog.replace("Assistant", Assistantname + " ")
    with open(TempDirectoryPath("Database.data"), "w", encoding="utf-8") as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    if os.path.exists(TempDirectoryPath('Database.data')):
        with open(TempDirectoryPath('Database.data'), "r", encoding='utf-8') as file:
            Data = file.read()
        if len(str(Data)) > 0:
            with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as file:
                file.write(Data)

def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

InitialExecution()

def MainExecution(Query=None):
    try:
        # --- Initialization (Fixes the UnboundLocalError) ---
        TaskExecution = False
        ImageExecution = False
        ImageGenerationQuery = ""
        
        # 1. Input Handling
        if Query is None:
            SetAssistantStatus("Listening...")
            # Check for typed data first to prioritize manual input
            typed_path = TempDirectoryPath("TypedQuery.data")
            if os.path.exists(typed_path):
                with open(typed_path, "r", encoding="utf-8") as f:
                    Query = f.read().strip()
                try: os.remove(typed_path) # Clean up immediately
                except: pass
            else:
                Query = SpeechRecognition()

        if not Query:
            return False

        ShowTextToScreen(f"{Username} : {Query}")
        if HandleImageGenerationRequest(Query):
            return True
        if HandleQuickAction(Query):
            return True
        if HandleUploadedQuestion(Query):
            return True

        SetAssistantStatus("Thinking...")
        
        # 2. Decision Making
        Decision = FirstLayerDMM(Query)
        if not Decision:
            return False
        
        print(f"\nDecision : {Decision}\n")
        
        # 3. Handle Image Generation Trigger
        for queries in Decision:
            if "generate " in queries.lower():
                ImageGenerationQuery = queries.lower().replace("generate ", "").replace("image ", "").strip()
                ImageExecution = True

        if ImageExecution:
            HandleImageGenerationRequest(f"generate image of {ImageGenerationQuery}")

        # 4. Handle Automation Tasks (Open, Close, System, etc.)
        for queries in Decision:
            if not TaskExecution:
                if any(queries.startswith(func) for func in Functions):
                    run(Automation(list(Decision)))
                    TaskExecution = True
        
        # 5. Handle General/Realtime Responses
        G = any([i for i in Decision if i.startswith("general")])
        R = any([i for i in Decision if i.startswith("realtime")])
        Merged_query = " and ".join([" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")])
        
        if R or (G and R):
            SetAssistantStatus("Searching...")
            Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
            ShowTextToScreen(f"{Assistantname} : {Answer}")
            SetAssistantStatus("Answering...")
            SpeakIfAllowed(Answer)
            return True
        else:
            for Queries in Decision:
                if "general" in Queries:
                    SetAssistantStatus("Thinking...")
                    QueryFinal = Queries.replace("general ", "")
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname} : {Answer}")
                    SetAssistantStatus("Answering...")
                    SpeakIfAllowed(Answer)
                    return True
                elif "exit" in Queries:
                    Answer = "Okay, Bye!"
                    ShowTextToScreen(f"{Assistantname} : {Answer}")
                    SpeakIfAllowed(Answer)
                    os._exit(1)
    
    except Exception as e:
        print(f"Error in Execution Logic: {e}")
        SetAssistantStatus("Error...")
        return False

# Simple wrapper for the Thread logic
def MainExecutionTyped(Query):
    return MainExecution(Query)


def FirstThread():
    while True:
        CurrentStatus = GetMicrophoneStatus()

        if CurrentStatus == "True":
            MainExecution()
            SetMicrophoneStatus("False")

        elif CurrentStatus == "Typed":
            query = ""
            # Use 'with' to ensure the file is closed immediately after reading
            try:
                with open(TempDirectoryPath("TypedQuery.data"), "r", encoding="utf-8") as f:
                    query = f.read().strip()
                
                if query:
                    MainExecutionTyped(query)
            except Exception as e:
                print(f"File Read Error: {e}")
            
            SetMicrophoneStatus("False")

        elif CurrentStatus == "Upload":
            HandleFileUpload()
            SetMicrophoneStatus("False")

        sleep(0.1)

def SecondThread():
    GraphicalUserInterface()

if __name__ == "__main__":
    # --- Start Image Generation Engine as a single background process ---
    try:
        # This starts the second script immediately when main.py runs
        subprocess.Popen([sys.executable, r'Backend\ImageGeneration.py'], shell=False)
        print(">> Image Generation Engine Started Successfully.")
    except Exception as e:
        print(f">> Failed to start Image Gen Engine: {e}")

    # --- Start Assistant Logic Threads ---
    thread1 = threading.Thread(target=FirstThread, daemon=True)
    thread1.start()
    
    SecondThread() #threadsecond
