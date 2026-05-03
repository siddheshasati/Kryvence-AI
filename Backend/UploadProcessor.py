import base64
import json
import mimetypes
import os
import re
import zipfile
import xml.etree.ElementTree as ET

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

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from PIL import Image
except ImportError:
    Image = None


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data")
ENV_PATH = os.path.join(BASE_DIR, ".env")
UPLOAD_CONTEXT_PATH = os.path.join(DATA_DIR, "UploadedContext.json")
os.makedirs(DATA_DIR, exist_ok=True)

env_vars = dotenv_values(ENV_PATH)
GroqAPIKey = env_vars.get("GroqAPIKey", "")
Assistantname = env_vars.get("Assistantname", "Assistant")
client = Groq(api_key=GroqAPIKey) if Groq and GroqAPIKey else None

VISION_MODEL = env_vars.get("GroqVisionModel", "meta-llama/llama-4-scout-17b-16e-instruct")
TEXT_MODEL = env_vars.get("GroqTextModel", "llama-3.3-70b-versatile")


def save_upload_context(context):
    with open(UPLOAD_CONTEXT_PATH, "w", encoding="utf-8") as file:
        json.dump(context, file, indent=4)


def load_upload_context():
    try:
        with open(UPLOAD_CONTEXT_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, ValueError):
        return {}


def has_upload_context():
    context = load_upload_context()
    return bool(context.get("text") or context.get("summary"))


def clean_text(text):
    text = re.sub(r"\r", "\n", text or "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def extract_docx_text(path):
    paragraphs = []
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as docx:
        with docx.open("word/document.xml") as document:
            tree = ET.parse(document)
    for paragraph in tree.findall(".//w:p", namespace):
        parts = [node.text for node in paragraph.findall(".//w:t", namespace) if node.text]
        if parts:
            paragraphs.append("".join(parts))
    return clean_text("\n".join(paragraphs))


def extract_pdf_text(path):
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        return clean_text("\n".join(page.extract_text() or "" for page in reader.pages))
    except ImportError:
        pass
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(path)
        return clean_text("\n".join(page.extract_text() or "" for page in reader.pages))
    except ImportError:
        return ""


def image_metadata(path):
    if Image is None:
        return "Image uploaded, but Pillow is not installed for local image metadata."
    try:
        with Image.open(path) as image:
            width, height = image.size
            return f"Image file: {os.path.basename(path)}\nFormat: {image.format}\nSize: {width} x {height}px"
    except Exception:
        return f"Image file: {os.path.basename(path)}"


def ask_llm(system_prompt, user_prompt, max_tokens=900):
    if client is None:
        return "AI analysis is not ready because the Groq package or API key is missing."
    try:
        completion = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.4,
            top_p=1,
        )
        return clean_text(completion.choices[0].message.content)
    except Exception as exc:
        return f"I could not analyze this with AI right now: {exc}"


def analyze_image(path):
    metadata = image_metadata(path)
    if client is None:
        return metadata + "\n\nI can store this image, but visual understanding needs the Groq package and API key."

    mime_type = mimetypes.guess_type(path)[0] or "image/png"
    try:
        with open(path, "rb") as file:
            image_data = base64.b64encode(file.read()).decode("utf-8")
        completion = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Understand this image. If there is text, a question, a problem, or a form in it, answer it directly. Otherwise describe the image clearly and mention important details.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
                        },
                    ],
                }
            ],
            max_tokens=900,
            temperature=0.3,
        )
        return clean_text(completion.choices[0].message.content)
    except Exception as exc:
        return metadata + f"\n\nI could not visually analyze the image right now: {exc}"


def looks_like_resume(text, path):
    name = os.path.basename(path).lower()
    keywords = [
        "resume", "cv", "experience", "education", "skills", "projects",
        "certifications", "summary", "objective", "linkedin", "github"
    ]
    hits = sum(1 for keyword in keywords if keyword in text.lower() or keyword in name)
    return hits >= 3


def analyze_resume(text):
    prompt = f"""
Evaluate this resume for ATS quality.

Return:
1. ATS score out of 100
2. Strong points
3. Missing or weak areas
4. Keyword and formatting suggestions
5. Concrete improved bullet examples if useful

Resume text:
{text[:12000]}
"""
    return ask_llm(
        "You are an ATS resume reviewer. Be practical, structured, and direct.",
        prompt,
        max_tokens=1200,
    )


def summarize_document(text, filename):
    prompt = f"""
The user uploaded a document named {filename}.
Summarize the document, identify important points, and tell the user they can ask questions about it.

Document text:
{text[:12000]}
"""
    return ask_llm(
        "You analyze uploaded documents. Be clear, structured, and not too long.",
        prompt,
        max_tokens=900,
    )


def process_uploaded_file(path):
    if not path or not os.path.exists(path):
        return "I could not find the uploaded file. Please upload it again."

    extension = os.path.splitext(path)[1].lower()
    filename = os.path.basename(path)
    context = {
        "path": path,
        "filename": filename,
        "extension": extension,
        "text": "",
        "summary": "",
        "kind": "unknown",
    }

    if extension in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
        context["kind"] = "image"
        analysis = analyze_image(path)
        context["summary"] = analysis
        save_upload_context(context)
        return f"Uploaded image: {filename}\n\n{analysis}"

    if extension == ".docx":
        text = extract_docx_text(path)
    elif extension == ".pdf":
        text = extract_pdf_text(path)
        if not text:
            return "I uploaded the PDF, but I could not extract readable text. Install `pypdf` or upload a text-based PDF instead of a scanned image PDF."
    else:
        return "Unsupported file type. Please upload an image, PDF, or DOCX file."

    context["kind"] = "document"
    context["text"] = text

    if looks_like_resume(text, path):
        context["summary"] = analyze_resume(text)
        context["kind"] = "resume"
    else:
        context["summary"] = summarize_document(text, filename)

    save_upload_context(context)
    return f"Uploaded file: {filename}\n\n{context['summary']}"


def answer_question_about_upload(question):
    context = load_upload_context()
    if not context:
        return ""

    source_text = context.get("text") or context.get("summary", "")
    if not source_text:
        return "I have the uploaded file reference, but no readable text or visual summary was extracted."

    prompt = f"""
Uploaded file: {context.get('filename', 'uploaded file')}
File type: {context.get('kind', 'unknown')}

Uploaded content/context:
{source_text[:14000]}

User question:
{question}
"""
    return ask_llm(
        "Answer questions using the uploaded file context. If the answer is not in the file, say that clearly and then help with the best available reasoning.",
        prompt,
        max_tokens=1000,
    )
