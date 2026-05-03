import pygame
import random
import asyncio
import edge_tts
import os
from dotenv import dotenv_values

# Load environment variables, provide a default fallback voice if missing
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-US-AriaNeural")

# Ensure Data folder exists
os.makedirs("Data", exist_ok=True)

async def TextTOAudioFile(text) -> None:
    file_path = r"Data\speech.mp3"
    
    # Safely remove the old file, forcing pygame to release it if locked
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except PermissionError:
            pygame.mixer.quit() # Force release the file lock
            os.remove(file_path)

    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
    await communicate.save(file_path)

def TTS(Text, func=lambda r=None: True):
    try:
        # Generate the audio file
        asyncio.run(TextTOAudioFile(Text))
        
        # Initialize pygame and play
        pygame.mixer.init()
        pygame.mixer.music.load(r"Data\speech.mp3")
        pygame.mixer.music.play()

        # Wait for the audio to finish playing
        while pygame.mixer.music.get_busy():
            if func() == False:
                break
            pygame.time.Clock().tick(10)
            
        return True
    except Exception as e:
        print(f"Error in TTS: {e}")
    finally:
        try:
            # Always clean up the mixer when done to prevent memory leaks
            func(False)
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception as e:
            print(f"Error in finally block: {e}")

def TextToSpeech(Text, func=lambda r=None: True):
    # Prevent crashing on empty inputs
    if not str(Text).strip():
        return

    Data = str(Text).split(",")

    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "The rest of the text is now on the chat screen, sir, please check it.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see.",
        "The rest of the answer is now on the chat screen, sir.",
        "Sir, please look at the chat screen, the rest of the answer is there.",
        "You'll find the complete answer on the chat screen, sir.",
        "The next part of the text is on the chat screen, sir.",
        "Sir, please check the chat screen for more information.",
        "There's more text on the chat screen for you, sir.",
        "Sir, take a look at the chat screen for additional text.",
        "You'll find more to read on the chat screen, sir.",
        "Sir, check the chat screen for the rest of the text.",
        "The chat screen has the rest of the text, sir.",
        "There's more to see on the chat screen, sir, please look.",
        "Sir, the chat screen holds the continuation of the text.",
        "You'll find the complete answer on the chat screen, kindly check it out sir.",
        "Please review the chat screen for the rest of the text, sir.",
        "Sir, look at the chat screen for the complete answer."
    ]

    # Fixed float slice syntax [0.2] to integer slice [:2]
    if len(Data) > 4 and len(Text) >= 250:
        shortened_text = " ".join(Text.split(".")[:2]) + ". " + random.choice(responses)
        TTS(shortened_text, func)
    else:
        TTS(Text, func)

if __name__ == "__main__":
    print("Text-to-Speech Engine Initialized. Type something and press Enter.")
    while True:
        try:
            user_input = input("Enter the text: ")
            TextToSpeech(user_input)
        except KeyboardInterrupt:
            # Cleanly exit the script if Ctrl+C is pressed
            print("\nExiting TTS engine.")
            break