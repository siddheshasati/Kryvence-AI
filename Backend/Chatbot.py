from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
from dotenv import set_key, dotenv_values

# Load existing environment variables
env_vars = dotenv_values(".env")

# Update the Assistantname
env_vars["Assistantname"] = "MechautoX"

# Save the updated environment variables back to the .env file
for key, value in env_vars.items():
    set_key(".env", key, value)

# Reload the environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")

print(f"Updated Assistantname to: {Assistantname}")
GroqAPIKey = env_vars.get("GroqAPIKey")

if not GroqAPIKey:
    logging.error("Groq API key not found in .env file.")
    exit(1)

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# System prompt
System = f"""Hello, I am {Username}. You are a very accurate and advanced AI chatbot named {Assistantname}.
*** Do not tell time unless asked, do not talk too much, just answer the question.***
*** Reply only in English, even if the question is in Hindi.***
*** Do not provide notes in the output, just answer the question concisely. ***
"""

# Chat history (Limited to last 50 messages)
chat_log_path = r"Data/ChatLog.json"

try:
    with open(chat_log_path, "r") as f:
        messages = load(f)[-50:]  # Keep only the last 50 messages
except (FileNotFoundError, ValueError):
    messages = []

# Function to get real-time information (only when explicitly asked)
def RealtimeInformation():
    now = datetime.datetime.now()
    return f"Day: {now.strftime('%A')}, Date: {now.strftime('%d %B %Y')}, Time: {now.strftime('%H:%M:%S')}."

# Function to clean up answer formatting
def AnswerModifier(Answer):
    return "\n".join(line.strip() for line in Answer.split("\n") if line.strip()).replace("</s>", "").strip()

# Chat function
def ChatBot(Query):
    try:
        # Append user query to messages
        messages.append({"role": "user", "content": Query})
        
        # Prepare chat context
        chat_context = [{"role": "system", "content": System}]
        
        # Check if user asked for real-time info
        if any(keyword in Query.lower() for keyword in ["time", "date", "day", "current"]):
            chat_context.append({"role": "system", "content": RealtimeInformation()})
        
        chat_context += messages
        
        # Generate AI response
        # Generate AI response
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # ✅ Updated model
            messages=chat_context,
            max_tokens=1024,
            temperature=0.7,
            top_p=1
        )

        
        # Get AI response
        Answer = completion.choices[0].message.content.strip()
        
        # Save response
        messages.append({"role": "assistant", "content": Answer})
        
        # Keep only the last 50 messages for storage
        with open(chat_log_path, "w") as f:
            dump(messages[-50:], f, indent=4)

        return AnswerModifier(Answer)
    
    except Exception as e:
        logging.error(f"Error in ChatBot: {e}")
        return "An error occurred. Please try again."

# Run chatbot in loop
if __name__ == "__main__":
    while True:
        user_input = input("Enter your question: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        print(ChatBot(user_input))