import cv2
import json
import mss
import numpy as np
from obswebsocket import obsws, requests
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk

obs_connection = None
obs_overlay_source_id = None

with open("config.json", "r") as f:
    config = json.load(f)

OBS_OVERLAY_SOURCE = config.get("obs_overlay_source_name", "")
OBS_PASSWORD = config.get("obs_websocket_password", "")
OBS_SCENE = config.get("obs_scene_name", "")
OBS_WEBSOCKET_PORT = config.get("obs_websocket_port", 4455)
TEMPLATES_PATH = "detection_templates/"
THRESHOLD = config.get("similarity_accuracy", 0.8)
valid_extensions = (".png", ".jpg", ".jpeg", ".bmp")
template_files = [f for f in os.listdir(TEMPLATES_PATH) if f.lower().endswith(valid_extensions)]
executor = ThreadPoolExecutor(max_workers=min((len(template_files)) * 2, 4))

def preprocess_image(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return cv2.normalize(gray_image, None, 0, 255, cv2.NORM_MINMAX)

def load_templates():
    templates_edges = []
    for filename in template_files:
        path = os.path.join(TEMPLATES_PATH, filename)
        template = cv2.imread(path)
        if template is None:
            print(f"Failed to load {filename}. Unsupported format or corrupted file.")
        else:
            template_edges = preprocess_image(template)
            scaled_template = [
                cv2.resize(template_edges, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                for scale in np.linspace(0.6, 1, 3)
            ]
            templates_edges.append(scaled_template)
    return templates_edges

def connect_to_obs():
    global obs_connection, obs_overlay_source_id
    if obs_connection is not None:
        return obs_connection
    ws = obsws("localhost", int(OBS_WEBSOCKET_PORT), OBS_PASSWORD)
    try:
        ws.connect()
        obs_connection = ws
    except Exception as e:
        print(f"Failed with '{type(e).__name__}' while trying to connect to OBS: {e}")
        status_label.config(text=f"Status: Failed with '{type(e).__name__}' while trying to connect to OBS", fg="red")
        obs_connection = None
        return None
    try:
        ws.call(requests.SetCurrentProgramScene(sceneName=OBS_SCENE))
    except Exception as e:
        print(f"Failed with '{type(e).__name__}' while trying to set the {OBS_SCENE} scene: {e}")
        status_label.config(text=f"Status: Failed with '{type(e).__name__}' while trying to set the {OBS_SCENE} scene", fg="red")
        return None
    try:
        obs_overlay_source_id = ws.call(requests.GetSceneItemId(sceneName=OBS_SCENE, sourceName=OBS_OVERLAY_SOURCE)).datain.get("sceneItemId")
    except Exception as e:
        print(f"Failed with '{type(e).__name__}' while trying to get the {OBS_OVERLAY_SOURCE} source id: {e}")
        status_label.config(text=f"Status: Failed with '{type(e).__name__}' while trying to get the {OBS_OVERLAY_SOURCE} source id", fg="red")
        return None
    try:
        ws.call(requests.SetSceneItemEnabled(sceneName=OBS_SCENE, sceneItemId=obs_overlay_source_id, sceneItemEnabled=False))
    except Exception as e:
        print(f"Failed with '{type(e).__name__}' while trying to hide the {OBS_OVERLAY_SOURCE} overlay source: {e}")
        status_label.config(text=f"Status: Failed with '{type(e).__name__}' while trying to hide the {OBS_OVERLAY_SOURCE} overlay source", fg="red")
        return None
    return ws

def check_obs_connection():
    global obs_connection
    if obs_connection is None:
        return connect_to_obs()
    try:
        obs_connection.call(requests.GetVersion())
        return obs_connection
    except Exception as e:
        print(f"OBS connection error: {e}")
        print("Attempting to reconnect...")
        for attempt in range(1, 3 + 1):
            time.sleep(5)
            obs_connection = connect_to_obs()
            if obs_connection:
                print("Reconnected to OBS.")
                return obs_connection
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Retry {attempt}/3 failed.")
        print("Failed to reconnect after multiple attempts. Check OBS and try again.")
        return None

def capture_screen():
    with mss.mss() as sct:
        try:
            screenshot = sct.grab(sct.monitors[1])
            frame = np.array(screenshot)
            return frame[:, :, :3]
        except Exception as e:
            print(f"Error capturing screen on monitor 1: {e}")
            return None

def check_template(scaled_template, frame_edges):
    for t in scaled_template:
        res = cv2.matchTemplate(frame_edges, t, cv2.TM_CCOEFF_NORMED)
        max_value = np.max(res)
        # print(f"Max match value: {max_value}") #TODO Remove
        if max_value >= float(THRESHOLD):
            return True
    return False

def set_overlay_visibility(ws, visible):
    global obs_overlay_source_id
    try:
        ws.call(requests.SetSceneItemEnabled(sceneName=OBS_SCENE, sceneItemId=obs_overlay_source_id, sceneItemEnabled=visible))
    except Exception as e:
        print(f"Failed with '{type(e).__name__}' while trying to toggle overlay visibility to {visible}: {e}")
        status_label.config(text=f"Status: Failed with '{type(e).__name__}' while trying to toggle overlay visibility to {visible}", fg="red")

def detect_templates():
    templates_edges = load_templates()
    if not templates_edges:
        print("No valid templates found in detection_templates folder")
        status_label.config(text="Status: No templates found", fg="red")
        return

    ws = check_obs_connection()
    if not ws:
        return

    is_overlay_on = False

    while app.running:
        is_match_found = False
        frame = capture_screen()
        frame_edges = preprocess_image(frame)

        futures = [executor.submit(check_template, scaled_template, frame_edges) for scaled_template in templates_edges]

        for future in as_completed(futures):
            result = future.result()
            if result:
                is_match_found = True
                for f in futures:
                    if not f.done():
                        f.cancel()
                break

        if is_match_found and not is_overlay_on:
            set_overlay_visibility(ws, True)
            is_overlay_on = True
        elif not is_match_found and is_overlay_on:
            set_overlay_visibility(ws, False)
            is_overlay_on = False

def start_detection():
    if OBS_PASSWORD == "":
        print("No OBS websocket password provided in the config.json file")
        status_label.config(text="Status: Missing OBS websocket password", fg="red")
        return
    if OBS_SCENE == "":
        print("No OBS scene name provided in the config.json file")
        status_label.config(text="Status: Missing OBS scene name", fg="red")
        return
    if OBS_OVERLAY_SOURCE == "":
        print("No OBS overlay source name provided in the config.json file")
        status_label.config(text="Status: Missing OBS overlay source name", fg="red")
        return
    if not (isinstance(THRESHOLD, float) and 0.0 <= THRESHOLD <= 1.0):
        print("Similarity accuracy in the config.json file should be a decimal point between 0.0 and 1.0")
        status_label.config(text="Status: Invalid similarity accuracy", fg="red")
        return
    if not app.running:
        app.running = True
        threading.Thread(target=detect_templates).start()
        status_label.config(text="Status: Running", fg="green")

def stop_detection():
    app.running = False
    status_label.config(text="Status: Stopped", fg="grey")

def on_close():
    global obs_connection
    if app.running:
        stop_detection()
    if obs_connection:
        try:
            obs_connection.disconnect()
        except Exception as e:
            print(f"Error while disconnecting: {e}")
    executor.shutdown(wait=False)
    app.destroy()

app = tk.Tk()
app.running = False
app.title("OBS Overlay Controller")
app.geometry("300x150")
status_label = tk.Label(app, text="Status: Stopped", fg="grey")
status_label.pack(pady=10)
start_button = tk.Button(app, text="Start", command=start_detection)
start_button.pack(pady=5)
stop_button = tk.Button(app, text="Stop", command=stop_detection)
stop_button.pack(pady=5)
app.protocol("WM_DELETE_WINDOW", on_close)

app.mainloop()
