import asyncio
from random import randint
from PIL import Image
import requests
from dotenv import load_dotenv
import os
from time import sleep

# Load environment variables
load_dotenv()
API_KEY = os.getenv("HuggingFaceAPIKey")

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Ensure data folder exists
DATA_FOLDER = "Data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# Number of images to generate
n = 4  # Define n before using it


def open_image(prompt):
    """Open generated images from the Data folder."""
    prompt = prompt.replace(" ", "_")  # Ensure filename consistency
    files = [f"{prompt}{i}.jpg" for i in range(1, n + 1)]
    
    for jpg_file in files:
        image_path = os.path.join(DATA_FOLDER, jpg_file)
        try:
            img = Image.open(image_path)
            print(f"Opening Image: {image_path}")
            img.show()
            sleep(1)
        except IOError:
            print(f"Unable to open {image_path}")


# Async function to send a query to the Hugging Face API
async def query(payload):
    response = await asyncio.to_thread(requests.post, API_URL, headers=HEADERS, json=payload)
    return response.content


# Async function to generate images based on the given prompt
async def generate_images(prompt: str):
    tasks = []
    
    for _ in range(n):
        payload = {
            "inputs": f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, seed={randint(0,1000000)}"
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    image_bytes_list = await asyncio.gather(*tasks)

    for i, image_bytes in enumerate(image_bytes_list):
        image_path = os.path.join(DATA_FOLDER, f"{prompt.replace(' ', '_')}{i+1}.jpg")
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        print(f"Image saved: {image_path}")


def GenerateImages(prompt: str):
    """Run the image generation and then open the generated images."""
    asyncio.run(generate_images(prompt))
    open_image(prompt)


# Main loop to read prompts from file
FILE_PATH = r"Frontend\Files\ImageGeneration.data"

while True:
    try:
        with open(FILE_PATH, "r") as f:
            data = f.read()

        if data:
            prompt, status = data.split(",")
            if status.strip().lower() == "true":
                print("Generating Images...")
                GenerateImages(prompt)

                # Update the status to False after generating images
                with open(FILE_PATH, "w") as f:
                    f.write(f"{prompt},False")
                
                break  # Exit loop after generating images
            else:
                sleep(1)
    except Exception as e:
        print(f"Error: {e}")
        sleep(1)