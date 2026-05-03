import logging
try:
    from googlesearch import search
except ImportError:
    search = None
try:
    from groq import Groq
except ImportError:
    Groq = None
from json import load, dump
import datetime
import os
try:
    from dotenv import dotenv_values
except ImportError:
    def dotenv_values(path):
        values = {}
        if not os.path.exists(path):
            return values
        with open(path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
        return values

# Configure logging
logging.basicConfig(filename='chatbot.log', level=logging.ERROR)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data")
CHAT_LOG_PATH = os.path.join(DATA_DIR, "ChatLog.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")
os.makedirs(DATA_DIR, exist_ok=True)

env_vars = dotenv_values(ENV_PATH)
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "AI Assistant")
GroqAPIKey = env_vars.get("GroqAPIKey", "")

client = Groq(api_key=GroqAPIKey) if Groq and GroqAPIKey else None

System = f"""Hello, I am {Username}. You are an advanced AI chatbot named {Assistantname} with real-time information.
Answer in English. Be professional, accurate, and useful without padding. For simple factual questions, use 4-8 clear lines. For research, learning, planning, debugging, coding, or problem-solving questions, give a fuller structured answer with steps, examples, or reasoning as needed.
When giving code, return the code in fenced Markdown blocks with the correct language name and proper indentation."""

REALTIME_MODEL = "llama-3.3-70b-versatile"

try:
    with open(CHAT_LOG_PATH, "r", encoding="utf-8") as f:
        messages = load(f)
except (FileNotFoundError, ValueError):
    with open(CHAT_LOG_PATH, "w", encoding="utf-8") as f:
        dump([], f)
    messages = []

def GoogleSearch(query, num_results=3):  # Limit to 3 results
    if search is None:
        return "Search package is not installed. Answer from general knowledge and mention if something may need verification."
    try:
        results = list(search(query, num_results=num_results))
        if not results:
            return "No search results were found."
        Answer = f"Here are the top {num_results} results for '{query}':\n"
        for i, url in enumerate(results, 1):
            Answer += f"{i}. {url}\n"
        return Answer
    except Exception as e:
        logging.error(f"Google Search Error: {str(e)}")
        return "Search results are temporarily unavailable. Answer from general knowledge and mention if something may need verification."

def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    return "\n".join(non_empty_lines)

SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"}
]

def Information():
    current_datetime = datetime.datetime.now()
    return f"""Real-time information:
Day: {current_datetime.strftime("%A")}
Date: {current_datetime.strftime("%d")}
Month: {current_datetime.strftime("%B")}
Year: {current_datetime.strftime("%Y")}
Time: {current_datetime.strftime("%H:%M:%S")}."""

def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages
    if client is None:
        return "Realtime search is not ready because the Groq package or API key is missing."
    

    try:
        with open(CHAT_LOG_PATH, "r", encoding="utf-8") as f:
            messages = load(f)
    except (FileNotFoundError, ValueError):
        messages = []
    
    
    messages.append({"role": "user", "content": prompt})
    
    
    if len(messages) > 3:
        messages = messages[-3:]
    

    search_results = GoogleSearch(prompt)
    
    
    real_time_info = Information()
    realtime_context = [
        {"role": "system", "content": search_results},
        {"role": "system", "content": real_time_info}
    ]
    
    try:
        completion = client.chat.completions.create(
            model=REALTIME_MODEL,
            messages=SystemChatBot + realtime_context + messages,
            max_tokens=800,
            temperature=0.5,
            top_p=1,
            stream=False
        )
        
        Answer = completion.choices[0].message.content.strip().replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})

        # Save chat history
        with open(CHAT_LOG_PATH, "w", encoding="utf-8") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer)
    except Exception as e:
        logging.error(f"Groq API Error: {str(e)}")
        return "I could not reach the realtime search engine right now. Please try again in a moment."

if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(RealtimeSearchEngine(prompt))
