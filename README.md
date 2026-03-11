# 🌌 Kryvence AI: The Autonomous Multi-Modal Ecosystem

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Architecture-Modular-orange.svg?style=for-the-badge)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**Kryvence AI** is a high-performance, modular artificial intelligence assistant. Designed with a decoupled architecture, it bridges the gap between sophisticated backend logic—covering real-time search, image synthesis, and bi-directional voice—and a sleek, responsive frontend.

---

## 📺 Project Demonstration

Experience the fluid interaction and automation capabilities of **Kryvence AI** in the video below:

Home Page<img width="1919" height="1012" alt="Home" src="https://github.com/user-attachments/assets/fe298ce1-c793-40fa-9c31-b7f9e728aa6f" />

Chat Screen]<img width="1917" height="1010" alt="chatscreen" src="https://github.com/user-attachments/assets/71c79fd5-c621-4532-88b6-58feabb45286" />

Chat Screen and Reply <img width="1919" height="1012" alt="chatscreen2" src="https://github.com/user-attachments/assets/68ca3a53-8a27-4546-9745-c41d38c6fe7e" />


[![Kryvence AI Demo](https://img.shields.io/badge/Watch_Demo_Video-▶-red?style=for-the-badge&logo=youtube)](https://drive.google.com/file/d/1lbTG1y7o5xaPoIrw8LgAm0BtIr8XDWYL/view?usp=drive_link)

---

## 🚀 Key Capabilities

| Feature | Module | Description |
| :--- | :--- | :--- |
| **Real-Time Intelligence** | `RealtimeSearchEngine.py` | Fetches live web data to bypass knowledge cut-offs. |
| **Neural Vision** | `ImageGeneration.py` | Transforms textual concepts into high-fidelity visual assets. |
| **Task Automation** | `Automation.py` | Executes system-level workflows and repetitive tasks autonomously. |
| **Voice Interface** | `SpeechToText.py` & `TTS.py` | Enables natural, low-latency voice-to-voice communication. |
| **Core Logic** | `Model.py` & `Chatbot.py` | The centralized "brain" managing state and LLM orchestration. |

---

## 📂 Project Structure

The repository is organized into distinct layers for scalability:



* **`Backend/`**: Contains the core engines for search, voice, and generation.
* **`Frontend/`**: Houses the user interface components (Main.py entry point).
* **`Data/`**: Local repository for cached assets and configuration files.

---

## 🛠️ Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone [https://github.com/your-username/Kryvence-AI.git](https://github.com/your-username/Kryvence-AI.git)
   cd Kryvence-AI
2. Environment Virtualization (Recommended)
To prevent dependency conflicts, it is highly recommended to use a virtual environment:

On Windows:

Bash
python -m venv venv
.\venv\Scripts\activate
On macOS/Linux:

Bash
python3 -m venv venv
source venv/bin/activate
3. Install Core Dependencies
The system requires several libraries for Speech, Search, and AI processing. Install them using the Requirements.txt file:

Bash
pip install -r Requirements.txt
[!IMPORTANT]
Some audio modules may require system-level dependencies like portaudio. If you encounter errors, ensure your system drivers are up to date.

🔑 Configuration & API Setup
Kryvence AI requires specific API keys to power the Realtime Search and Model engines.

Create a Secrets File:
In your root directory, create a .env file (or use secrets.toml if using Streamlit).

Add Your Credentials:

Code snippet
GEMINI_API_KEY="your_api_key_here"
SEARCH_ENGINE_ID="your_id_here"
STT_ENGINE_KEY="your_key_here"
Initialize the Backend:
The Model.py file is pre-configured to read these secrets. Ensure the variable names in your code match your environment file.

🚀 Execution Flow
To launch the full ecosystem:

# To run the Interactive Web Dashboard (if using Streamlit)
streamlit run GUI.py
🧪 Testing the Modules
You can test individual modules to ensure your hardware (Mic/GPU) is compatible:

Test Voice: python Backend/SpeechToText.py
Test Search: python Backend/RealtimeSearchEngine.py
Test Vision: python Backend/ImageGeneration.py
