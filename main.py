import os
import subprocess
import webbrowser
import requests
import difflib
import re
import pyttsx3
import threading
hotword_thread = None
stop_listening = False  
# Initialize text-to-speech
engine = pyttsx3.init(driverName='nsss')  
engine.setProperty('rate', 180)
# Ensure chatlog file exists
if not os.path.exists("chatlog.txt"):
    with open("chatlog.txt", "w") as f:
        f.write("🤖 Jarvis: Hello! How can I help you today?\n")
engine.say("hi")
engine.runAndWait()
def speak(text):
    print(f"🤖 Jarvis: {text}")
    engine.say(text)
    engine.runAndWait()

# Known macOS apps (customize as needed)
known_apps = {
    "safari": "/System/Applications/Safari.app",
    "textedit": "/System/Applications/TextEdit.app",
    "finder": "/System/Library/CoreServices/Finder.app",
    "calculator": "/System/Applications/Calculator.app",
    "notes": "/System/Applications/Notes.app",
    "terminal": "/System/Applications/Utilities/Terminal.app",
    "preview": "/System/Applications/Preview.app",
    "calendar": "/System/Applications/Calendar.app",
    "reminders": "/System/Applications/Reminders.app",
    "mail": "/System/Applications/Mail.app",
    "music": "/System/Applications/Music.app",
    "photos": "/System/Applications/Photos.app",
    "messages": "/System/Applications/Messages.app",
    "facetime": "/System/Applications/FaceTime.app",
    "contacts": "/System/Applications/Contacts.app",
    "system settings": "/System/Applications/System Settings.app",
    "app store": "/System/Applications/App Store.app",
    "chess": "/System/Applications/Chess.app",
    "screenshot": "/System/Applications/Utilities/Screenshot.app",
    "disk utility": "/System/Applications/Utilities/Disk Utility.app",
    "activity monitor": "/System/Applications/Utilities/Activity Monitor.app",
    "dictionary": "/System/Applications/Dictionary.app",
    "automator": "/System/Applications/Automator.app",
    "voice memos": "/System/Applications/Voice Memos.app",
    "stocks": "/System/Applications/Stocks.app",
    "podcasts": "/System/Applications/Podcasts.app",
    "pycharm": "/System/Applications/PyCharm CE.app",
    "arduino": "/System/Applications/Arduino IDE.app"
}


def ask_ai(message, is_chat=False):
    url = "https://ai.hackclub.com/chat/completions"
    headers = {"Content-Type": "application/json"}

    system_prompt = (
        "You are a task classifier. When given a user's command, return the inferred action in this format:\n\n"
        "ACTION: open_app Safari\n"
        "ACTION: write_file notes.txt Write this down\n"
        "ACTION: open_website https://example.com\n"
        "ACTION: search_google how to tie a tie\n"
        "ACTION: play_music Never Gonna Give You Up\n"
        "ACTION: run_terminal rm myfile.txt\n"
        "ACTION: say Hello! How can I help?\n"
        "ACTION: chat_general\n"
        "ACTION: chat_realtime\n\n"
        "Example:\n"
        "User: Delete the file myfile.txt          → ACTION: run_terminal rm myfile.txt\n"
        "User: List files in current directory     → ACTION: run_terminal ls -la\n"
        "User: Who is Einstein?                    → ACTION: chat_general\n"
        "User: What's the weather today?           → ACTION: chat_realtime\n\n"
        "Respond with only one line starting with ACTION:"
    )

    messages = [{"role": "system", "content": system_prompt}]
    if is_chat:
        messages = [
            {"role": "system", "content": "You are Jarvis, a helpful, funny AI assistant."},
            {"role": "user", "content": message}
        ]
    else:
        messages.append({"role": "user", "content": message})

    data = {"messages": messages}

    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return "Could not connect to AI service."


def open_app(app_name):
    match = difflib.get_close_matches(app_name.lower(), known_apps.keys(), n=1, cutoff=0.5)
    if match:
        subprocess.run(["open", "-a", known_apps[match[0]]])
        return f"Opening {match[0].capitalize()}"
    return f"App '{app_name}' not found."

def open_website(url):
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening website {url}"


def run_terminal(command):
    confirm = input(f"⚠️  Are you sure you want to run this command? `{command}` (y/n): ").strip().lower()
    if confirm != 'y':
        return "Command cancelled."

    # Handle "clear" specially
    if command.strip() == "clear":
        os.system("clear")
        return "Screen cleared."

    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        return result.strip() or "Command executed."
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.strip()}"


def write_file(filename, content):
    try:
        # Decode escaped newlines (e.g., '\n') to real newlines
        content = content.encode().decode('unicode_escape')

        with open(filename, 'w') as f:
            f.write(content)
        subprocess.run(["open", filename])
        return f"Wrote to {filename} and opened it."
    except Exception as e:
        return f"Error writing to file: {e}"


def search_google(query):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Searching Google for '{query}'"

def play_music(song):
    url = f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Playing '{song}' on YouTube"

from vosk import Model, KaldiRecognizer
import sounddevice as sd
import json

vosk_model = Model("vosk-model-small-en-us-0.15")
def on_wake_word():
    speak("Yes?")
    user_input = get_voice_input()
    result = handle_command(user_input)
    if len(result.split()) <= 15:
        speak(result)
    else:
        print(f"🤖 Jarvis: {result}")
import time
def get_voice_input(timeout_seconds=7):
    recognizer = KaldiRecognizer(vosk_model, 16000)
    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print("Mic error:", status)
        q.put(bytes(indata))

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
        print("🎤 Listening for your command...")
        result_text = ""
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            if not q.empty():
                data = q.get()
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    result_text = result.get("text", "").strip()
                    if result_text:
                        print(f"🧑 You: {result_text}")
                        return result_text

        print("⚠️ Timeout — no speech detected.")
        return ""




def handle_command(user_input):
    ai_reply = ask_ai(user_input)

    if ai_reply.startswith("ACTION:"):
        command = ai_reply[len("ACTION:"):].strip()

        if command.startswith("open_app"):
            _, app = command.split(" ", 1)
            return open_app(app)

        elif command.startswith("open_website"):
            _, url = command.split(" ", 1)
            return open_website(url)

        elif command.startswith("write_file"):
            match = re.match(r"write_file ([^\s]+) (.+)", command)
            if match:
                filename, content = match.groups()
                return write_file(filename, content)
            return "Could not parse write_file command."

        elif command.startswith("search_google"):
            _, query = command.split(" ", 1)
            return search_google(query)

        elif command.startswith("play_music"):
            _, song = command.split(" ", 1)
            return play_music(song)

        elif command.startswith("say"):
            _, message = command.split(" ", 1)
            return message

        elif command == "chat_general":
            if "create a file called" in user_input.lower() or "make a file called" in user_input.lower():
                match = re.search(r'(?:create|make) a file called (\S+)', user_input.lower())
                if match:
                    filename = match.group(1)
                    code_content = ask_ai(user_input, is_chat=True)

                    # Clean the AI response: Remove markdown formatting, decode escape characters
                    if "```" in code_content:
                        code_content = re.findall(r"```(?:\w*\n)?([\s\S]+?)```", code_content)
                        code_content = code_content[0] if code_content else ""
                    code_content = code_content.encode().decode("unicode_escape")

                    with open(filename, 'w') as f:
                        f.write(code_content)
                    subprocess.run(["open", filename])
                    return f"File {filename} created."

                return "Couldn't detect filename."
            else:
                response = ask_ai(user_input, is_chat=True)
                return response

        elif command == "chat_realtime":
            return search_google(user_input)
        elif command.startswith("run_terminal"):
            _, terminal_cmd = command.split(" ", 1)
            return run_terminal(terminal_cmd)

        else:
            return "Unknown command from AI."

    else:
        return ai_reply
import queue
import json
recognizer = KaldiRecognizer(vosk_model, 16000)
q = queue.Queue()
def audio_callback(indata, frames, time, status):
    if status:
        print("Audio status:", status)
    q.put(bytes(indata))


def hotword_listener(trigger_word="jarvis", callback=None):
    recognizer = KaldiRecognizer(vosk_model, 16000)
    q = queue.Queue()

    def audio_callback(indata, frames, time, status):
        if status:
            print("Audio status:", status)
        q.put(bytes(indata))

    print("Hotword detection running... Say 'Jarvis' to wake me up.")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                text = json.loads(recognizer.Result()).get("text", "").strip()
                if text:
                    print("Heard:", text)
                    if trigger_word.lower() in text.lower():
                        print("👂 Wake word detected!")
                        if callback:
                            callback()

def log_response(text):
    try:
        with open("chatlog.txt", "r") as f:
            lines = f.readlines()
        if lines and lines[-1].strip() == f"Jarvis: {text}".strip():
            return  
    except FileNotFoundError:
        pass 

    with open("chatlog.txt", "a") as f:
        f.write(f"Jarvis: {text}\n")
def run_jarvis():
    print("Jarvis is always listening. Say 'Jarvis' to activate me. Say 'exit' anytime to quit.")

    def on_hotword():
        user_input = get_voice_input()
        if not user_input:
            print("Jarvis: I didn’t catch that.")
            return

        if user_input.lower() in ["exit", "quit", "goodbye"]:
            speak("Goodbye!")
            os._exit(0)

        result = handle_command(user_input)

        if len(result.split()) <= 15:
            speak(result)
        else:
            print(f"Jarvis: {result}")

        log_response(result)

    try:
        hotword_listener(callback=on_hotword)
    except KeyboardInterrupt:
        speak("Goodbye!")

def toggle_listening(enabled: bool) -> bool:
    global stop_listening, hotword_thread

    stop_listening = not enabled

    if enabled:
        if not hotword_thread or not hotword_thread.is_alive():
            hotword_thread = threading.Thread(target=hotword_listener, kwargs={"callback": on_wake_word}, daemon=True)
            hotword_thread.start()
            print("Hotword listener started.")
    else:
        print("Hotword listener stopped.")
    return True

if __name__ == "__main__":
    run_jarvis()
