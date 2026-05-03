import os
from urllib.parse import quote
from io import BytesIO
from random import randint
from time import sleep

try:
    import requests
except ImportError:
    requests = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = os.path.join(BASE_DIR, "Data")
FRONTEND_FILES = os.path.join(BASE_DIR, "Frontend", "Files")
REQUEST_PATH = os.path.join(FRONTEND_FILES, "ImageGeneration.data")
RESPONSE_PATH = os.path.join(FRONTEND_FILES, "Responses.data")
STATUS_PATH = os.path.join(FRONTEND_FILES, "AssistantStatus.data")
ENV_PATH = os.path.join(BASE_DIR, ".env")

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(FRONTEND_FILES, exist_ok=True)

if load_dotenv:
    load_dotenv(ENV_PATH)

API_KEY = os.getenv("HuggingFaceAPIKey", "")
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
NUM_IMAGES = 2


def write_file(path, text):
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)


def set_status(status):
    write_file(STATUS_PATH, status)


def show_to_chat(message):
    write_file(RESPONSE_PATH, message)


def safe_filename(prompt):
    cleaned = "".join(char if char.isalnum() else "_" for char in prompt.lower())
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned[:80] or "generated_image"


def read_request():
    if not os.path.exists(REQUEST_PATH):
        write_file(REQUEST_PATH, ",False")
        return "", "False"

    with open(REQUEST_PATH, "r", encoding="utf-8") as file:
        data = file.read().strip()

    if not data or "," not in data:
        return "", "False"

    prompt, status = data.rsplit(",", 1)
    return prompt.strip(), status.strip()


def mark_done(prompt):
    write_file(REQUEST_PATH, f"{prompt},False")


def request_image(prompt, seed):
    if requests is None:
        raise RuntimeError("The `requests` package is not installed. Install project requirements first.")

    if not API_KEY:
        encoded_prompt = quote(f"{prompt}, 4K, sharp, ultra detailed, high resolution")
        fallback_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&nologo=true"
        response = requests.get(fallback_url, timeout=180)
        if response.status_code != 200:
            raise RuntimeError(f"Fallback image API error {response.status_code}: {response.text[:300]}")
        return response.content

    payload = {
        "inputs": f"{prompt}, 4K, sharp, ultra detailed, high resolution, seed={seed}",
        "options": {"wait_for_model": True},
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=180)

    content_type = response.headers.get("content-type", "")
    if response.status_code != 200:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text[:500]
        raise RuntimeError(f"Hugging Face API error {response.status_code}: {detail}")

    if "image" not in content_type:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text[:500]
        raise RuntimeError(f"API did not return an image: {detail}")

    return response.content


def save_image(image_bytes, prompt, index):
    if Image is None:
        raise RuntimeError("The `Pillow` package is not installed. Install project requirements first.")
    image = Image.open(BytesIO(image_bytes))
    filename = f"{safe_filename(prompt)}_{index}.jpg"
    image_path = os.path.join(DATA_FOLDER, filename)
    image.convert("RGB").save(image_path, "JPEG", quality=95)
    return image_path


def generate_images(prompt):
    saved_paths = []
    for index in range(1, NUM_IMAGES + 1):
        image_bytes = request_image(prompt, randint(0, 1_000_000))
        saved_paths.append(save_image(image_bytes, prompt, index))
    return saved_paths


def choose_preview_image(paths):
    if not paths:
        return ""
    return max(paths, key=lambda path: os.path.getsize(path) if os.path.exists(path) else 0)


def process_generation(prompt):
    set_status("Generating image...")
    show_to_chat(f"Generating image for: {prompt}")
    try:
        saved_paths = generate_images(prompt)
        preview_path = choose_preview_image(saved_paths)
        preview_relative = os.path.relpath(preview_path, BASE_DIR) if preview_path else ""
        relative_paths = [os.path.relpath(path, BASE_DIR) for path in saved_paths]
        message = (
            f"Image generation complete.\n\n"
            f"Preview image: {preview_relative}\n\n"
            f"All generated images:\n" + "\n".join(relative_paths)
        )
        show_to_chat(message)
        set_status("Image ready")
        print(message)
    except Exception as exc:
        error = f"Image generation failed: {exc}"
        show_to_chat(error)
        set_status("Image error")
        print(error)
    finally:
        mark_done(prompt)


def main():
    print("Image generation worker started.")
    while True:
        prompt, status = read_request()
        if prompt and status.lower() == "true":
            process_generation(prompt)
        sleep(1)


if __name__ == "__main__":
    main()
