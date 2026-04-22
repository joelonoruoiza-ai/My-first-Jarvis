import os
import re
import time
import ctypes
import threading
import winsound
import numpy as np
import pyaudio
import speech_recognition as sr
import pyttsx3
import psutil
import pyautogui
import wikipedia
import tkinter as tk
import pyperclip # pip install pyperclip
from google import genai
from dotenv import load_dotenv
from openwakeword.model import Model
from colorama import init, Fore, Style

# --- INITIALIZATION ---
init(autoreset=True)
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WAKE_WORD = "hey_jarvis"
LAST_BATTERY_WARN = 0
speech_lock = threading.Lock() # Prevents speech loop crashes

client = genai.Client(api_key=GEMINI_API_KEY)
chat = client.chats.create(model="gemini-2.5-flash")

# --- UI CLASS ---
class JarvisUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", "black")
        self.root.geometry("80x80+1800+900") 
        self.canvas = tk.Canvas(self.root, width=80, height=80, bg='black', highlightthickness=0)
        self.canvas.pack()
        self.orb = self.canvas.create_oval(10, 10, 70, 70, fill="blue", outline="cyan", width=2)
        self.status = "standby"
        self.update_ui()

    def update_ui(self):
        colors = {"standby": "blue", "active": "red", "speaking": "green", "thinking": "yellow"}
        self.canvas.itemconfig(self.orb, fill=colors.get(self.status, "blue"))
        self.root.after(100, self.update_ui)

    def set_status(self, status):
        self.status = status

ui = JarvisUI()

# --- REFINED DEEP VOICE ENGINE ---
is_speaking = False

def clean_text(text):
    return re.sub(r'[*_#>]', '', text)

def _speech_worker(text):
    global is_speaking
    with speech_lock:
        is_speaking = True
        ui.set_status("speaking")
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            
            # IMPROVED VOICE SELECTION
            found_voice = False
            for voice in voices:
                # Look for David (Deep Male) or any name containing 'Male'
                if "david" in voice.name.lower() or "male" in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    found_voice = True
                    break
            
            engine.setProperty("rate", 160) # Formal, slightly slower speed
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            del engine 
        except:
            pass
        finally:
            is_speaking = False
            ui.set_status("standby")

def speak(text):
    cleaned = clean_text(text)
    print(Fore.CYAN + f"Jarvis: {cleaned}")
    if is_speaking:
        os.system("taskkill /f /im sapi.exe >nul 2>&1")
        time.sleep(0.1)
    t = threading.Thread(target=_speech_worker, args=(cleaned,), daemon=True)
    t.start()

# --- TOOLS ---
def type_content(content):
    speak("Standby. Selecting target Master Stark.")
    time.sleep(2.5) 
    pyautogui.write(content, interval=0.03)
    time.sleep(0.5)
    speak("Entry complete, Master Stark.")

def clipboard_manager(action="read"):
    text = pyperclip.paste()
    if not text:
        speak("The clipboard is empty, sir.")
        return
    if action == "read":
        speak(f"Clipboard content is: {text}")
    elif action == "type":
        type_content(text)

def lock_workstation():
    speak("Securing workstation.")
    ctypes.windll.user32.LockWorkStation()

# --- MAIN LOGIC ---
def run_jarvis_logic():
    global LAST_BATTERY_WARN
    recognizer = sr.Recognizer()
    try:
        oww_model = Model(wakeword_models=[WAKE_WORD], inference_framework="onnx")
    except: return

    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1280)
    
    speak("All systems integrated. Welcome back, Mister Leo.")

    try:
        while True:
            battery = psutil.sensors_battery()
            if battery and battery.percent < 20 and not battery.power_plugged:
                if time.time() - LAST_BATTERY_WARN > 300:
                    speak("Warning: Power levels are critical.")
                    LAST_BATTERY_WARN = time.time()

            data = stream.read(1280, exception_on_overflow=False)
            audio_frame = np.frombuffer(data, dtype=np.int16)
            
            if oww_model.predict(audio_frame)[WAKE_WORD] > 0.06:
                if is_speaking: os.system("taskkill /f /im sapi.exe >nul 2>&1")
                winsound.Beep(1000, 80)
                ui.set_status("active")
                
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    try:
                        audio = recognizer.listen(source, timeout=3, phrase_time_limit=8)
                        cmd = recognizer.recognize_google(audio).lower()
                        print(Fore.YELLOW + f"You: {cmd}")
                        
                        if "write" in cmd or "type" in cmd:
                            if "clipboard" in cmd:
                                clipboard_manager("type")
                            else:
                                type_content(cmd.replace("write", "").replace("type", "").strip())
                        
                        elif "read" in cmd and "clipboard" in cmd:
                            clipboard_manager("read")
                        
                        elif "lockdown" in cmd or "go to sleep" in cmd:
                            lock_workstation()
                        
                        elif any(x in cmd for x in ["status", "vitals", "battery"]):
                            battery = psutil.sensors_battery()
                            speak(f"CPU is at {psutil.cpu_percent()} percent. Battery is at {battery.percent} percent.")
                        
                        elif "open" in cmd:
                            os.system(f"start {cmd.replace('open', '').strip()}")
                            speak("Opening application.")
                        
                        elif any(x in cmd for x in ["exit", "shutdown", "i'll take it from here", "that's all for now"]):
                            speak("Goodbye Master Leo."); time.sleep(1); ui.root.quit(); return
                        
                        else:
                            ui.set_status("thinking")
                            speak(chat.send_message(cmd).text)
                    except: pass
                ui.set_status("standby")
    finally:
        stream.close(); pa.terminate()

if __name__ == "__main__":
    logic_thread = threading.Thread(target=run_jarvis_logic, daemon=True)
    logic_thread.start()
    ui.root.mainloop()