from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QListWidget, QFileDialog
from PyQt5.QtGui import QIcon, QMovie, QFont
from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal
from dotenv import dotenv_values

import sys
import os
import json
import html
import re

current_dir = os.path.dirname(os.path.abspath(__file__))


project_root = os.path.dirname(current_dir)


if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Backend.SpeechToText import QueryModifier

env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname", "MechautoX")
Username = env_vars.get("Username", "Siddhesh Asati")
current_dir = os.getcwd()
old_chat_message = ""
TempDirPath = rf"{current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"
ChatSessionsPath = rf"{current_dir}\Data\ChatSessions.json"

# --- Utility Functions ---
def GraphicsDirectoryPath(Filename): return rf'{GraphicsDirPath}\{Filename}'
def TempDirectoryPath(Filename): return rf'{TempDirPath}\{Filename}'

def SetMicrophoneStatus(Command):
    try:
        with open(rf'{TempDirPath}\Mic.data', 'w', encoding='utf-8') as file:
            file.write(Command)
    except: pass

def MicButtonInitialed(): SetMicrophoneStatus("False")
def MicButtonClosed(): SetMicrophoneStatus("True")

def SetSayAloudStatus(Command):
    try:
        with open(TempDirectoryPath('SayAloud.data'), 'w', encoding='utf-8') as file:
            file.write(Command)
    except: pass

def GetSayAloudStatus():
    try:
        with open(TempDirectoryPath('SayAloud.data'), "r", encoding='utf-8') as file:
            return file.read().strip()
    except:
        return "False"

# --- UI Components ---

class PromptInput(QTextEdit):
    submitted = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setAcceptRichText(False)
        self.setPlaceholderText(f"Message {Assistantname}...")
        self.setMinimumHeight(96)
        self.setMaximumHeight(160)
        self.setFont(QFont("Segoe UI", 12))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not event.modifiers() & Qt.ShiftModifier:
            self.submitted.emit()
            return
        super().keyPressEvent(event)

class ChatSection(QWidget):
    def __init__(self):
        super().__init__()
        self.mic_toggled = True
        self.say_aloud_enabled = GetSayAloudStatus() == "True"
        self.latest_code = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(10)

        self.setStyleSheet("""
            QWidget {
                background: #05070d;
                color: #f4fbff;
                font-family: 'Segoe UI';
            }
            QTextEdit#ChatTranscript {
                background-color: rgba(7, 12, 24, 235);
                border: 1px solid #1a9dff;
                border-radius: 18px;
                padding: 14px;
                color: #eaf8ff;
                selection-background-color: #15d6ff;
                selection-color: #02050a;
            }
            QTextEdit#PromptInput {
                background-color: #0a1020;
                border: 1px solid #20d6ff;
                border-radius: 18px;
                padding: 14px 16px;
                color: #ffffff;
                selection-background-color: #27e0ff;
                selection-color: #02050a;
            }
            QTextEdit#PromptInput:focus {
                border: 2px solid #72f5ff;
                background-color: #0d172b;
            }
            QPushButton {
                font-family: 'Segoe UI';
            }
        """)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        self.title = QLabel(f"{Assistantname}")
        self.title.setStyleSheet("color: #f4fbff; font-size: 30px; font-weight: 700; letter-spacing: 0px;")
        subtitle = QLabel("Neural workspace")
        subtitle.setStyleSheet("color: #7ecfff; font-size: 13px; font-weight: 600;")
        title_block.addWidget(self.title)
        title_block.addWidget(subtitle)
        header.addLayout(title_block)
        header.addStretch()

        self.status_pill = QLabel("ONLINE")
        self.status_pill.setStyleSheet("""
            QLabel {
                color: #071019;
                background-color: #52f5c9;
                border-radius: 14px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: 800;
            }
        """)
        header.addWidget(self.status_pill)
        self.new_chat_btn = QPushButton("New chat")
        self.new_chat_btn.setCursor(Qt.PointingHandCursor)
        self.new_chat_btn.setFixedHeight(38)
        self.new_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #101827;
                color: #dff8ff;
                border: 1px solid #245a88;
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 800;
            }
            QPushButton:hover {
                color: #72f5ff;
                border-color: #72f5ff;
            }
        """)
        self.new_chat_btn.clicked.connect(self.start_new_chat)
        header.addWidget(self.new_chat_btn)

        self.say_aloud_btn = QPushButton()
        self.say_aloud_btn.setCursor(Qt.PointingHandCursor)
        self.say_aloud_btn.setFixedHeight(38)
        self.say_aloud_btn.clicked.connect(self.toggle_say_aloud)
        header.addWidget(self.say_aloud_btn)
        self.update_say_aloud_button()
        layout.addLayout(header)
        
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setObjectName("ChatTranscript")
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setMinimumHeight(560)
        self.chat_text_edit.setFont(QFont("Segoe UI", 12))
        self.chat_text_edit.setHtml("""
            <div style="color:#8bdcff; font-size:15px; line-height:1.45;">
                <p style="margin:0 0 8px 0; color:#ffffff; font-size:22px; font-weight:700;">Ready when you are.</p>
                <p style="margin:0; color:#98b9cf;">Ask, create, learn, automate, or generate images from one command center.</p>
            </div>
        """)
        layout.addWidget(self.chat_text_edit, 1)

        copy_row = QHBoxLayout()
        copy_row.setContentsMargins(0, 0, 0, 0)
        self.copy_code_btn = QPushButton("Copy")
        self.copy_code_btn.setFixedSize(78, 34)
        self.copy_code_btn.setCursor(Qt.PointingHandCursor)
        self.copy_code_btn.setVisible(False)
        self.copy_code_btn.setStyleSheet("""
            QPushButton {
                background-color: #101827;
                color: #dff8ff;
                font-size: 12px;
                font-weight: 800;
                border: 1px solid #245a88;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #17243d;
                border-color: #72f5ff;
                color: #72f5ff;
            }
        """)
        self.copy_code_btn.clicked.connect(self.copy_latest_code)
        copy_row.addStretch()
        copy_row.addWidget(self.copy_code_btn)
        layout.addLayout(copy_row)

        self.options_layout = QGridLayout()
        self.options_layout.setSpacing(12)
        options = [ "Create Images", "Help me to learn", "Take my Interview","Write Codes"]
        for i, text in enumerate(options):
            btn = QPushButton(text)
            btn.setMinimumHeight(56)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0b1427;
                    color: #eaf8ff;
                    border: 1px solid #245a88;
                    border-radius: 14px;
                    font-size: 14px;
                    font-weight: 700;
                    padding: 10px 16px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #13294a;
                    color: #72f5ff;
                    border: 1px solid #72f5ff;
                }
            """)
            btn.clicked.connect(lambda ch, t=text: self.send_manual_text(t))
            self.options_layout.addWidget(btn, 0, i)
        layout.addLayout(self.options_layout)

        status_bar = QHBoxLayout()
        self.label = QLabel("STATUS: INITIALIZING...")
        self.label.setStyleSheet("color: #8bdcff; font-size: 14px; font-weight: 700;")
        
        self.gif_label = QLabel()
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        movie.setScaledSize(QSize(96, 56))
        self.gif_label.setMovie(movie)
        movie.start()
        
        status_bar.addWidget(self.label)
        status_bar.addStretch()
        status_bar.addWidget(self.gif_label)
        layout.addLayout(status_bar)

        self.input_layout = QHBoxLayout()
        self.input_layout.setSpacing(12)
        self.upload_btn = QPushButton("+")
        self.upload_btn.setFixedSize(64, 64)
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #101827;
                color: #72f5ff;
                font-size: 28px;
                font-weight: 500;
                border: 1px solid #245a88;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #17243d;
                border: 2px solid #72f5ff;
            }
        """)
        self.upload_btn.clicked.connect(self.upload_file)

        self.mic_chat_btn = QPushButton()
        self.update_mic_icon(self.mic_chat_btn)
        self.mic_chat_btn.setFixedSize(64, 64)
        self.mic_chat_btn.setCursor(Qt.PointingHandCursor)
        self.mic_chat_btn.clicked.connect(self.toggle_mic_local)
        
        self.type_input = PromptInput()
        self.type_input.setObjectName("PromptInput")
        self.type_input.submitted.connect(self.handle_typing)
        
        self.send_btn = QPushButton("SEND")
        self.send_btn.setFixedSize(118, 64)
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #52f5c9;
                color: #031017;
                font-size: 14px;
                font-weight: 900;
                border: none;
                border-radius: 18px;
            }
            QPushButton:hover {
                background-color: #72f5ff;
            }
        """)
        self.send_btn.clicked.connect(self.handle_typing)
        
        self.input_layout.addWidget(self.upload_btn)
        self.input_layout.addWidget(self.mic_chat_btn)
        self.input_layout.addWidget(self.type_input)
        self.input_layout.addWidget(self.send_btn)
        layout.addLayout(self.input_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(300)

    def update_mic_icon(self, button):
        icon_path = GraphicsDirectoryPath('Mic_on.png' if self.mic_toggled else 'Mic_off.png')
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(34, 34))
        border = '#52f5c9' if self.mic_toggled else '#ff5c7a'
        glow = '#132d32' if self.mic_toggled else '#2d1119'
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {glow};
                border: 1px solid {border};
                border-radius: 20px;
            }}
            QPushButton:hover {{
                background-color: #142a45;
                border: 2px solid #72f5ff;
            }}
        """)

    def toggle_mic_local(self):
        self.mic_toggled = not self.mic_toggled
        if self.mic_toggled: MicButtonInitialed()
        else: MicButtonClosed()
        self.update_mic_icon(self.mic_chat_btn)

    def update_say_aloud_button(self):
        self.say_aloud_btn.setText("Say aloud: On" if self.say_aloud_enabled else "Say aloud: Off")
        background = "#17352f" if self.say_aloud_enabled else "#101827"
        border = "#52f5c9" if self.say_aloud_enabled else "#245a88"
        color = "#52f5c9" if self.say_aloud_enabled else "#dff8ff"
        self.say_aloud_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {background};
                color: {color};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 800;
            }}
            QPushButton:hover {{
                border-color: #72f5ff;
                color: #72f5ff;
            }}
        """)

    def toggle_say_aloud(self):
        self.say_aloud_enabled = not self.say_aloud_enabled
        SetSayAloudStatus("True" if self.say_aloud_enabled else "False")
        self.update_say_aloud_button()

    def start_new_chat(self):
        self.store_current_chat_session()
        self.reset_chat_screen()
        self.copy_code_btn.setVisible(False)
        self.latest_code = ""
        global old_chat_message
        old_chat_message = ""
        try:
            os.makedirs("Data", exist_ok=True)
            with open(r"Data\ChatLog.json", "w", encoding="utf-8") as file:
                json.dump([], file, indent=4)
            with open(TempDirectoryPath("Responses.data"), "w", encoding="utf-8") as file:
                file.write("")
            with open(TempDirectoryPath("Database.data"), "w", encoding="utf-8") as file:
                file.write("")
        except Exception as e:
            print(f"Error starting new chat: {e}")

    def reset_chat_screen(self):
        self.chat_text_edit.setHtml("""
            <div style="color:#8bdcff; font-size:15px; line-height:1.45;">
                <p style="margin:0 0 8px 0; color:#ffffff; font-size:22px; font-weight:700;">New chat started.</p>
                <p style="margin:0; color:#98b9cf;">Ask anything, upload a file, or start an interview.</p>
            </div>
        """)

    def store_current_chat_session(self):
        try:
            if not os.path.exists(r"Data\ChatLog.json"):
                return
            with open(r"Data\ChatLog.json", "r", encoding="utf-8") as file:
                logs = json.load(file)
            if not logs:
                return
            os.makedirs("Data", exist_ok=True)
            sessions = []
            if os.path.exists(ChatSessionsPath):
                with open(ChatSessionsPath, "r", encoding="utf-8") as file:
                    sessions = json.load(file)
            first_user = next((log.get("content", "") for log in logs if log.get("role") == "user"), "New chat")
            sessions.append({
                "title": first_user[:60] or "New chat",
                "messages": logs
            })
            with open(ChatSessionsPath, "w", encoding="utf-8") as file:
                json.dump(sessions[-50:], file, indent=4)
        except Exception as e:
            print(f"Error storing chat session: {e}")

    def loadMessages(self):
        global old_chat_message
        try:
            path = TempDirectoryPath('Responses.data')
            if os.path.exists(path):
                with open(path, "r", encoding='utf-8') as file:
                    messages = file.read().strip()
                    if messages and old_chat_message != messages:
                        self.addMessage(f"{Assistantname}: {messages}", '#00d4ff')
                        old_chat_message = messages
        except: pass

    def SpeechRecogText(self):
        try:
            path = TempDirectoryPath('AssistantStatus.data')
            if os.path.exists(path):
                with open(path, "r", encoding='utf-8') as file:
                    status = file.read().strip().upper()
                    self.label.setText(f"STATUS: {status}" if status else "STATUS: STANDBY")
                    self.status_pill.setText(status if status else "STANDBY")
            current_say_aloud = GetSayAloudStatus() == "True"
            if current_say_aloud != self.say_aloud_enabled:
                self.say_aloud_enabled = current_say_aloud
                self.update_say_aloud_button()
        except: pass

    def extract_code_blocks(self, message):
        blocks = re.findall(r"```(?:[a-zA-Z0-9_+.-]+)?\s*\n?(.*?)```", message, flags=re.DOTALL)
        if blocks:
            return [block.strip("\n") for block in blocks if block.strip()]
        code_indicators = ["def ", "class ", "import ", "from ", "function ", "const ", "let ", "var ", "#include", "public class", "<html", "SELECT "]
        lines = message.splitlines()
        code_lines = [line for line in lines if any(indicator in line for indicator in code_indicators)]
        if len(code_lines) >= 2:
            return [message.strip()]
        return []

    def render_message_html(self, message):
        parts = []
        position = 0
        pattern = re.compile(r"```([a-zA-Z0-9_+.-]+)?\s*\n?(.*?)```", re.DOTALL)
        for match in pattern.finditer(message):
            text_part = message[position:match.start()].strip()
            if text_part:
                parts.append(html.escape(text_part).replace("\n", "<br>"))
            language = html.escape(match.group(1) or "code")
            code = html.escape(match.group(2).strip("\n"))
            parts.append(f"""
                <div style="margin:10px 0 6px 0; color:#72f5ff; font-size:12px; font-weight:800;">{language}</div>
                <pre style="background:#020711; color:#eaf8ff; border:1px solid #245a88; border-radius:10px; padding:14px; font-family:Consolas; font-size:13px; line-height:1.35; white-space:pre-wrap;">{code}</pre>
            """)
            position = match.end()
        tail = message[position:].strip()
        if tail:
            parts.append(html.escape(tail).replace("\n", "<br>"))
        rendered = "<br>".join(parts) if parts else html.escape(message).replace("\n", "<br>")
        return self.render_generated_image_preview(message, rendered)

    def image_path_from_line(self, line):
        cleaned = line.strip()
        if ":" in cleaned:
            cleaned = cleaned.split(":", 1)[1].strip()
        if not cleaned.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
            return ""
        candidate = cleaned
        if not os.path.isabs(candidate):
            candidate = os.path.join(project_root, candidate)
        return candidate if os.path.exists(candidate) else ""

    def render_generated_image_preview(self, message, rendered_message):
        preview_path = ""
        for line in message.splitlines():
            if "preview image:" in line.lower():
                preview_path = self.image_path_from_line(line)
                break
        if not preview_path:
            for line in message.splitlines():
                preview_path = self.image_path_from_line(line)
                if preview_path:
                    break
        if not preview_path:
            return rendered_message

        visible_lines = []
        skip_generated_paths = False
        for line in message.splitlines():
            lower_line = line.lower().strip()
            if lower_line.startswith("preview image:"):
                continue
            if lower_line.startswith("all generated images:"):
                skip_generated_paths = True
                continue
            if skip_generated_paths and self.image_path_from_line(line):
                continue
            visible_lines.append(line)
        rendered_message = html.escape("\n".join(visible_lines).strip()).replace("\n", "<br>")

        image_src = preview_path.replace("\\", "/")
        image_html = f"""
            <div style="margin-top:12px;">
                <div style="color:#72f5ff; font-size:12px; font-weight:800; margin-bottom:8px;">Preview</div>
                <img src="{image_src}" width="520" style="border:1px solid #245a88; border-radius:12px;" />
            </div>
        """
        return rendered_message + image_html

    def copy_latest_code(self):
        if self.latest_code:
            QApplication.clipboard().setText(self.latest_code)
            self.copy_code_btn.setText("Copied")
            QTimer.singleShot(1200, lambda: self.copy_code_btn.setText("Copy"))

    def should_follow_new_messages(self):
        scrollbar = self.chat_text_edit.verticalScrollBar()
        return scrollbar.value() >= scrollbar.maximum() - 24

    def scroll_to_bottom(self):
        scrollbar = self.chat_text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def addMessage(self, message, color):
        follow_new_message = self.should_follow_new_messages()
        code_blocks = self.extract_code_blocks(message)
        if code_blocks:
            self.latest_code = "\n\n".join(code_blocks)
            self.copy_code_btn.setVisible(True)
        safe_message = self.render_message_html(message)
        is_user = color.lower() in ("#ffffff", "white")
        bubble_bg = "#17243d" if is_user else "#071e2e"
        border = "#6b7dff" if is_user else "#20d6ff"
        name_color = "#ffffff" if is_user else "#72f5ff"
        align = "right" if is_user else "left"
        html_message = f"""
            <div align="{align}" style="margin:14px 0;">
                <table width="84%" cellspacing="0" cellpadding="0" style="background:{bubble_bg}; border:1px solid {border}; border-radius:14px;">
                    <tr>
                        <td style="padding:14px 16px; color:#eef8ff; font-size:15px; line-height:1.5;">
                            <span style="color:{name_color}; font-weight:700;">{safe_message}</span>
                        </td>
                    </tr>
                </table>
            </div>
        """
        self.chat_text_edit.append(html_message)
        if follow_new_message:
            QTimer.singleShot(0, self.scroll_to_bottom)

    def handle_typing(self):
        query = self.type_input.toPlainText().strip()
        if query:
            query = QueryModifier(query)
            self.addMessage(f"{Username}: {query}", "#ffffff")
            try:
                with open(TempDirectoryPath("TypedQuery.data"), "w", encoding="utf-8") as file:
                    file.write(query)
            
                # Use a specific flag for typed input
                SetMicrophoneStatus("Typed") 
            except Exception as e:
                print(f"Error in handle_typing: {e}")
                pass
            self.type_input.clear()

    def upload_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Upload file",
            "",
            "Supported files (*.png *.jpg *.jpeg *.webp *.bmp *.pdf *.docx);;Images (*.png *.jpg *.jpeg *.webp *.bmp);;Documents (*.pdf *.docx)"
        )
        if not path:
            return
        filename = os.path.basename(path)
        self.addMessage(f"{Username}: Uploaded {filename}", "#ffffff")
        try:
            with open(TempDirectoryPath("UploadedFile.data"), "w", encoding="utf-8") as file:
                file.write(path)
            SetMicrophoneStatus("Upload")
        except Exception as e:
            print(f"Error in upload_file: {e}")

    def send_manual_text(self, text):
        self.type_input.setPlainText(text)
        self.handle_typing()

class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget, toggle_sidebar_func):
        super().__init__(parent)
        self.setFixedHeight(72)
        self.setStyleSheet("background-color: #03070d; border-bottom: 1px solid #15445a;")
        layout = QHBoxLayout(self)
        
        self.menu_btn = QPushButton(" ☰ ")
        self.menu_btn.setText("Menu")
        self.menu_btn.setFixedSize(64, 46)
        self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.setStyleSheet("""
            QPushButton {
                color: #72f5ff;
                font-size: 13px;
                font-weight: 800;
                background-color: #071425;
                border: 1px solid #1c536a;
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: #10243c;
                border-color: #72f5ff;
            }
        """)
        self.menu_btn.clicked.connect(toggle_sidebar_func)
        layout.addWidget(self.menu_btn)

        title = QLabel(f"{Assistantname.upper()} AI")
        title.setStyleSheet("color: #f4fbff; font-weight: 800; font-size: 20px; font-family: 'Segoe UI'; letter-spacing: 0px;")
        layout.addWidget(title)
        layout.addStretch()

        nav_style = """
            QPushButton {
                background-color: #071425;
                border: 1px solid #1c536a;
                color: #d9f8ff;
                font-weight: 700;
                padding: 10px 18px;
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: #123251;
                color: #72f5ff;
                border-color: #72f5ff;
            }
        """
        self.home_btn = QPushButton("HOME")
        self.chat_btn = QPushButton("CHAT")
        for btn in [self.home_btn, self.chat_btn]:
            btn.setStyleSheet(nav_style)
            layout.addWidget(btn)

        self.home_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(0))
        self.chat_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(1))

        close_btn = QPushButton("×")
        close_btn.setText("X")
        close_btn.setFixedSize(46, 46)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                color: #ff5c7a;
                font-size: 17px;
                font-weight: 900;
                background-color: #16070b;
                border: 1px solid #4b1e2a;
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: #3a101a;
                border-color: #ff5c7a;
            }
        """)
        close_btn.clicked.connect(parent.close)
        layout.addWidget(close_btn)

class ModernTopBar(QWidget):
    def __init__(self, parent, stacked_widget, toggle_sidebar_func):
        super().__init__(parent)
        self.setFixedHeight(72)
        self.setStyleSheet("""
            QWidget {
                background-color: #05070d;
                border-bottom: 1px solid #14395c;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(12)

        self.menu_btn = QPushButton("MENU")
        self.menu_btn.setFixedSize(82, 42)
        self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.setStyleSheet("""
            QPushButton {
                color: #72f5ff;
                font-size: 13px;
                font-weight: 800;
                background-color: #0b1427;
                border: 1px solid #245a88;
                border-radius: 14px;
            }
            QPushButton:hover {
                color: #031017;
                background-color: #72f5ff;
            }
        """)
        self.menu_btn.clicked.connect(toggle_sidebar_func)
        layout.addWidget(self.menu_btn)

        title = QLabel(f"{Assistantname.upper()} AI")
        title.setStyleSheet("color: #f4fbff; font-weight: 800; font-size: 19px; font-family: 'Segoe UI';")
        layout.addWidget(title)
        layout.addStretch()

        nav_style = """
            QPushButton {
                background-color: #080d18;
                border: 1px solid #203653;
                color: #dff8ff;
                font-weight: 800;
                padding: 10px 18px;
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: #142a45;
                border-color: #72f5ff;
                color: #72f5ff;
            }
        """
        self.home_btn = QPushButton("HOME")
        self.chat_btn = QPushButton("CHAT")
        for btn in [self.home_btn, self.chat_btn]:
            btn.setStyleSheet(nav_style)
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)

        self.home_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(0))
        self.chat_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(1))

        close_btn = QPushButton("X")
        close_btn.setFixedSize(44, 42)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                color: #ff7a91;
                font-size: 16px;
                font-weight: 900;
                background-color: #16070c;
                border: 1px solid #5f1b2a;
                border-radius: 14px;
            }
            QPushButton:hover {
                color: #ffffff;
                background-color: #d9365b;
            }
        """)
        close_btn.clicked.connect(parent.close)
        layout.addWidget(close_btn)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #05070d;")
        
        # --- Sidebar ---
        self.sidebar = QFrame(self)
        self.sidebar.setGeometry(-360, 72, 360, 1000)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #070b14;
                border-right: 1px solid #1a9dff;
            }
        """)
        
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(18, 20, 18, 18)
        side_layout.setSpacing(14)

        side_title = QLabel("History")
        side_title.setStyleSheet("color: #f4fbff; font-size: 20px; font-weight: 800;")
        side_layout.addWidget(side_title)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search history...")
        self.search_bar.setMinimumHeight(44)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background: #0b1427;
                color: #f4fbff;
                border: 1px solid #245a88;
                border-radius: 12px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #72f5ff;
            }
        """)
        self.search_bar.textChanged.connect(self.filter_history)
        side_layout.addWidget(self.search_bar)

        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                color: #dff8ff;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #17243d;
                border-radius: 10px;
            }
            QListWidget::item:hover {
                background: #102139;
                color: #72f5ff;
            }
        """)
        side_layout.addWidget(self.history_list)
        
        self.sidebar_ani = QPropertyAnimation(self.sidebar, b"geometry")
        self.sidebar_open = False

        # --- Content ---
        stacked = QStackedWidget()
        home = QWidget()
        home.setStyleSheet("background-color: #05070d;")
        home_layout = QVBoxLayout(home)
        home_layout.setContentsMargins(30, 30, 30, 30)
        hero_title = QLabel(f"{Assistantname}")
        hero_title.setAlignment(Qt.AlignCenter)
        hero_title.setStyleSheet("color: #f4fbff; font-size: 44px; font-weight: 900;")
        hero_subtitle = QLabel("A faster, cleaner command center for voice, chat, automation, and creation.")
        hero_subtitle.setAlignment(Qt.AlignCenter)
        hero_subtitle.setStyleSheet("color: #8bdcff; font-size: 16px; font-weight: 600;")
        self.home_gif = QLabel()
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        movie.setScaledSize(QSize(500, 320))
        self.home_gif.setMovie(movie)
        self.home_gif.setAlignment(Qt.AlignCenter)
        movie.start()
        home_layout.addStretch()
        home_layout.addWidget(hero_title)
        home_layout.addWidget(hero_subtitle)
        home_layout.addWidget(self.home_gif, alignment=Qt.AlignCenter)
        home_layout.addStretch()

        chat_screen = QWidget()
        chat_layout = QVBoxLayout(chat_screen)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        chat_layout.addWidget(ChatSection(), 1)
        
        stacked.addWidget(home)
        stacked.addWidget(chat_screen)

        self.setMenuWidget(ModernTopBar(self, stacked, self.toggle_sidebar))
        self.setCentralWidget(stacked)
        self.showMaximized()

    def toggle_sidebar(self):
        if self.sidebar_open:
            self.sidebar_ani.setEndValue(QRect(-360, 72, 360, self.height()))
            self.sidebar_open = False
        else:
            self.update_history()
            self.sidebar_ani.setEndValue(QRect(0, 72, 360, self.height()))
            self.sidebar_open = True
            self.sidebar.raise_()
        
        self.sidebar_ani.setDuration(300)
        self.sidebar_ani.setEasingCurve(QEasingCurve.OutQuint)
        self.sidebar_ani.start()

    def update_history(self):
        self.history_list.clear()
        try:
            if os.path.exists(ChatSessionsPath):
                with open(ChatSessionsPath, 'r', encoding='utf-8') as f:
                    sessions = json.load(f)
                    for session in reversed(sessions):
                        title = session.get("title", "New chat")
                        count = len(session.get("messages", []))
                        self.history_list.addItem(f"CHAT: {title[:42]} ({count})")
            if os.path.exists(r'Data\ChatLog.json'):
                with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    for log in reversed(logs):
                        self.history_list.addItem(f"{log['role'].upper()}: {log['content'][:40]}...")
        except: pass

    def filter_history(self, text):
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
            
    # Add these to the BOTTOM of Frontend/GUI.py
# --- Bridge Functions for Main.py ---

def InitializeEnvironment():
    """Creates necessary directories and files if they don't exist."""
    os.makedirs(TempDirPath, exist_ok=True)
    os.makedirs(GraphicsDirPath, exist_ok=True)
    if not os.path.exists(TempDirectoryPath('Mic.data')):
        with open(TempDirectoryPath('Mic.data'), 'w') as f: f.write("False")
    if not os.path.exists(TempDirectoryPath('AssistantStatus.data')):
        with open(TempDirectoryPath('AssistantStatus.data'), 'w') as f: f.write("IDLE")
    if not os.path.exists(TempDirectoryPath('SayAloud.data')):
        with open(TempDirectoryPath('SayAloud.data'), 'w') as f: f.write("False")

def AnswerModifier(Text):
    """Clean up the assistant's response for better display."""
    # Removes extra spaces, lines, or specific patterns if needed
    return Text.strip()

def QueryModifier(Query):
    """Clean up the user's input query."""
    return Query.lower().strip()

def GraphicalUserInterface():
    """The entry point for Main.py to start the GUI."""
    app = QApplication(sys.argv)
    InitializeEnvironment()
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

def SetAssistantStatus(Status):
    """Updates the status bar text."""
    with open(TempDirectoryPath('AssistantStatus.data'), "w", encoding='utf-8') as file:
        file.write(Status)

def ShowTextToScreen(Text):
    """Sends text to the GUI chat window via the Responses file."""
    with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as file:
        file.write(Text)

def GetMicrophoneStatus():
    """Reads whether the mic should be listening."""
    try:
        with open(TempDirectoryPath('Mic.data'), "r", encoding='utf-8') as file:
            return file.read().strip()
    except:
        return "False"

def GetAssistantStatus():
    """Reads current status for synchronization."""
    try:
        with open(TempDirectoryPath('AssistantStatus.data'), "r", encoding='utf-8') as file:
            return file.read().strip()
    except:
        return "IDLE"
def MicButtonInitialed(): SetMicrophoneStatus("True") # Now True = Listen
def MicButtonClosed(): SetMicrophoneStatus("False")   # Now False = Stop


if __name__ == "__main__":
    app = QApplication(sys.argv)
    os.makedirs(TempDirPath, exist_ok=True)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
