from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QListWidget, QMessageBox
from PyQt5.QtGui import QIcon, QMovie, QColor, QTextCharFormat, QFont, QPixmap
from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect
from dotenv import dotenv_values

import sys
import os
import json
import sys
import os

# Get absolute path of GUI.py
current_dir = os.path.dirname(os.path.abspath(__file__))

# Go one level up (project root: Assissant)
project_root = os.path.dirname(current_dir)

# Add project root to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import from Backend
from Backend.SpeechToText import QueryModifier


# Configuration
env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname", "MechautoX")
Username = env_vars.get("Username", "Siddhesh Asati")
current_dir = os.getcwd()
old_chat_message = ""
TempDirPath = rf"{current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"

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

# --- UI Components ---

class ChatSection(QWidget):
    def __init__(self):
        super().__init__()
        self.mic_toggled = True
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setStyleSheet("""
            background-color: #050505; border: 2px solid #00d4ff; 
            border-radius: 8px; padding: 12px; color: #00d4ff;
        """)
        self.chat_text_edit.setFont(QFont("Consolas", 12))
        layout.addWidget(self.chat_text_edit)

        self.options_layout = QGridLayout()
        options = ["Book tickets", "Create Images", "Create Videos", "Create Music", "Help me to learn"]
        for i, text in enumerate(options):
            btn = QPushButton(text)
            btn.setMinimumHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0a0a0a; color: #00d4ff; border: 2px solid #00d4ff; 
                    border-radius: 10px; font-weight: bold;
                }
                QPushButton:hover { background-color: #00d4ff; color: #000; }
            """)
            btn.clicked.connect(lambda ch, t=text: self.send_manual_text(t))
            self.options_layout.addWidget(btn, 0, i)
        layout.addLayout(self.options_layout)

        status_bar = QHBoxLayout()
        self.label = QLabel("STATUS: INITIALIZING...")
        self.label.setStyleSheet("color: #00d4ff; font-family: 'Agency FB'; font-size: 18px; font-weight: bold;")
        
        self.gif_label = QLabel()
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        movie.setScaledSize(QSize(120, 80))
        self.gif_label.setMovie(movie)
        movie.start()
        
        status_bar.addWidget(self.label)
        status_bar.addStretch()
        status_bar.addWidget(self.gif_label)
        layout.addLayout(status_bar)

        self.input_layout = QHBoxLayout()
        self.mic_chat_btn = QPushButton()
        self.update_mic_icon(self.mic_chat_btn)
        self.mic_chat_btn.setFixedSize(50, 50)
        self.mic_chat_btn.clicked.connect(self.toggle_mic_local)
        
        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText(f"ASK {Assistantname}...")
        self.type_input.setStyleSheet("background-color: #111; border: 2px solid #00d4ff; border-radius: 5px; padding: 12px; color: #fff; font-family: 'Consolas';")
        self.type_input.returnPressed.connect(self.handle_typing)
        
        self.send_btn = QPushButton("SEND")
        self.send_btn.setFixedSize(100, 45)
        self.send_btn.setStyleSheet("background-color: #00d4ff; color: #000; font-weight: bold; border-radius: 5px;")
        self.send_btn.clicked.connect(self.handle_typing)
        
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
        button.setIconSize(QSize(30, 30))
        button.setStyleSheet(f"background-color: #0a0a0a; border: 2px solid {'#00d4ff' if self.mic_toggled else '#ff3333'}; border-radius: 25px;")

    def toggle_mic_local(self):
        self.mic_toggled = not self.mic_toggled
        if self.mic_toggled: MicButtonInitialed()
        else: MicButtonClosed()
        self.update_mic_icon(self.mic_chat_btn)

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
        except: pass

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(f">>> {message}\n\n")
        self.chat_text_edit.setTextCursor(cursor)
        self.chat_text_edit.ensureCursorVisible()

    def handle_typing(self):
        query = self.type_input.text().strip()
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

    def send_manual_text(self, text):
        self.type_input.setText(text)
        self.handle_typing()

class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget, toggle_sidebar_func):
        super().__init__(parent)
        self.setFixedHeight(65)
        self.setStyleSheet("background-color: #000; border-bottom: 2px solid #00d4ff;")
        layout = QHBoxLayout(self)
        
        self.menu_btn = QPushButton(" ☰ ")
        self.menu_btn.setStyleSheet("color: #00d4ff; font-size: 24px; background: transparent; border: none;")
        self.menu_btn.clicked.connect(toggle_sidebar_func)
        layout.addWidget(self.menu_btn)

        title = QLabel(f"{Assistantname.upper()} AI")
        title.setStyleSheet("color: #00d4ff; font-weight: bold; font-size: 20px; font-family: 'Agency FB';")
        layout.addWidget(title)
        layout.addStretch()

        nav_style = "QPushButton { background: transparent; border: 1px solid #333; color: #fff; font-weight: bold; padding: 8px 15px; border-radius: 5px; }"
        self.home_btn = QPushButton(" HOME ")
        self.chat_btn = QPushButton(" CHAT ")
        for btn in [self.home_btn, self.chat_btn]:
            btn.setStyleSheet(nav_style)
            layout.addWidget(btn)

        self.home_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(0))
        self.chat_btn.clicked.connect(lambda: stacked_widget.setCurrentIndex(1))

        close_btn = QPushButton("×")
        close_btn.setFixedSize(40, 30)
        close_btn.setStyleSheet("color: #ff3333; font-size: 22px; background: transparent;")
        close_btn.clicked.connect(parent.close)
        layout.addWidget(close_btn)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #000;")
        
        # --- Sidebar ---
        self.sidebar = QFrame(self)
        self.sidebar.setGeometry(-350, 65, 350, 1000)
        self.sidebar.setStyleSheet("background-color: #050505; border-right: 2px solid #00d4ff;")
        
        side_layout = QVBoxLayout(self.sidebar)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search history...")
        self.search_bar.setStyleSheet("background: #111; color: #00d4ff; border: 1px solid #00d4ff; padding: 8px;")
        self.search_bar.textChanged.connect(self.filter_history)
        side_layout.addWidget(self.search_bar)

        self.history_list = QListWidget()
        self.history_list.setStyleSheet("QListWidget { background: transparent; border: none; color: #fff; } QListWidget::item { padding: 10px; border-bottom: 1px solid #222; }")
        side_layout.addWidget(self.history_list)
        
        self.sidebar_ani = QPropertyAnimation(self.sidebar, b"geometry")
        self.sidebar_open = False

        # --- Content ---
        stacked = QStackedWidget()
        home = QWidget()
        home_layout = QVBoxLayout(home)
        self.home_gif = QLabel()
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        self.home_gif.setMovie(movie)
        movie.start()
        home_layout.addStretch()
        home_layout.addWidget(self.home_gif, alignment=Qt.AlignCenter)
        home_layout.addStretch()

        chat_screen = QWidget()
        chat_layout = QVBoxLayout(chat_screen)
        chat_layout.addWidget(ChatSection())
        
        stacked.addWidget(home)
        stacked.addWidget(chat_screen)

        self.setMenuWidget(CustomTopBar(self, stacked, self.toggle_sidebar))
        self.setCentralWidget(stacked)
        self.showMaximized()

    def toggle_sidebar(self):
        if self.sidebar_open:
            self.sidebar_ani.setEndValue(QRect(-350, 65, 350, self.height()))
            self.sidebar_open = False
        else:
            self.update_history()
            self.sidebar_ani.setEndValue(QRect(0, 65, 350, self.height()))
            self.sidebar_open = True
            self.sidebar.raise_()
        
        self.sidebar_ani.setDuration(300)
        self.sidebar_ani.setEasingCurve(QEasingCurve.OutQuint)
        self.sidebar_ani.start()

    def update_history(self):
        self.history_list.clear()
        try:
            if os.path.exists(r'Data\ChatLog.json'):
                with open(r'Data\ChatLog.json', 'r') as f:
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