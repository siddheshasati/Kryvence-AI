import logging
from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values

# Configure logging
logging.basicConfig(filename='chatbot.log', level=logging.ERROR)

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "AI Assistant")
GroqAPIKey = env_vars.get("GroqAPIKey", "")

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# System prompt
System = f"""Hello, I am {Username}. You are an advanced AI chatbot named {Assistantname} with real-time information.
*** Provide professional, concise, and accurate answers. Avoid unnecessary details unless explicitly requested. ***"""

# Load chat history
try:
    with open(r"Data/ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data/ChatLog.json", "w") as f:
        dump([], f)
    messages = []

# Google search function
def GoogleSearch(query, num_results=3):  # Limit to 3 results
    try:
        results = list(search(query, num_results=num_results))
        Answer = f"Here are the top {num_results} results for '{query}':\n"
        for i, url in enumerate(results, 1):
            Answer += f"{i}. {url}\n"
        return Answer
    except Exception as e:
        logging.error(f"Google Search Error: {str(e)}")
        return f"Error during Google Search: {str(e)}"

# Remove empty lines from response
def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    return "\n".join(non_empty_lines)

# Chatbot context
SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"}
]

# Get real-time information
def Information():
    current_datetime = datetime.datetime.now()
    return f"""Real-time information:
Day: {current_datetime.strftime("%A")}
Date: {current_datetime.strftime("%d")}
Month: {current_datetime.strftime("%B")}
Year: {current_datetime.strftime("%Y")}
Time: {current_datetime.strftime("%H:%M:%S")}."""

# Main AI function
def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages
    
    # Load chat history
    with open(r"Data/ChatLog.json", "r") as f:
        messages = load(f)
    
    # Append user's prompt to chat history
    messages.append({"role": "user", "content": prompt})
    
    # Truncate chat history to keep only the last 3 messages
    if len(messages) > 3:
        messages = messages[-3:]
    
    # Get summarized Google search results
    search_results = GoogleSearch(prompt)
    
    # Append summarized search results to the context
    SystemChatBot.append({"role": "system", "content": search_results})
    
    # Append real-time information
    real_time_info = Information()
    
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=SystemChatBot + [{"role": "system", "content": real_time_info}] + messages,
            max_tokens=500,  # Limit response length
            temperature=0.7,
            top_p=1,
            stream=False
        )
        
        Answer = completion.choices[0].message.content.strip().replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})

        # Save chat history
        with open(r"Data/ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer)
    except Exception as e:
        logging.error(f"Groq API Error: {str(e)}")
        return f"Error during response generation: {str(e)}"
# CLI mode
if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(RealtimeSearchEngine(prompt))