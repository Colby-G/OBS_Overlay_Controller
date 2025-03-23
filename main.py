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

with open("config.json", "r") as f:
    config = json.load(f)

GAME_SCENE = config.get("game_scene_without_overlay_name", "")
TEMPLATES_PATH = "detection_templates/"
OBS_WEBSOCKET_PORT = config.get("obs_websocket_port", 4455)
OBS_PASSWORD = config.get("obs_websocket_password", "")
OVERLAY_SCENE = config.get("game_scene_with_overlay_name", "")
THRESHOLD = config.get("similarity_accuracy", 0.8)
TIMES_TO_CHECK = config.get("times_to_check_per_second", 10)
MILLISECONDS_PER_CHECK = int(1000 / TIMES_TO_CHECK)
executor = ThreadPoolExecutor(max_workers=len(os.listdir(TEMPLATES_PATH)))
current_scene = None

def connect_to_obs():
    ws = obsws("localhost", int(OBS_WEBSOCKET_PORT), OBS_PASSWORD)
    try:
        ws.connect()
        return ws
    except Exception as e:
        print(f"Failed to connect to OBS: {e}")
        status_label.config(text="Status: Failed to connect to OBS", fg="red")
        return None

def preprocess_image(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return cv2.normalize(gray_image, None, 0, 255, cv2.NORM_MINMAX)

def load_templates():
    templates_edges = []
    for filename in os.listdir(TEMPLATES_PATH):
        path = os.path.join(TEMPLATES_PATH, filename)
        template = cv2.imread(path)
        if template is not None:
            template_edges = preprocess_image(template)
            scaled_template = [
                cv2.resize(template_edges, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                for scale in np.linspace(0.7, 1, 3)
            ]
            templates_edges.append(scaled_template)
    return templates_edges

def capture_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)
        return frame[:, :, :3]

def check_template(scaled_template, frame_edges):
    for t in scaled_template:
        res = cv2.matchTemplate(frame_edges, t, cv2.TM_CCOEFF_NORMED)
        k = max(10, int(0.01 * res.size))
        top_k_mean = np.mean(np.partition(res.flatten(), -k)[-k:])
        print(f"Top-k Mean match value: {top_k_mean}") #TODO
        if top_k_mean >= float(THRESHOLD):
            return True
    return False

def detect_templates():
    templates_edges = load_templates()
    if not templates_edges:
        print("No valid templates found in detection_templates folder")
        status_label.config(text="Status: No templates found", fg="red")
        return

    ws = connect_to_obs()
    if not ws:
        return

    global current_scene
    response = ws.call(requests.SetCurrentProgramScene(sceneName=GAME_SCENE))
    # print(f"OBS Response: {response}") #TODO
    current_scene = GAME_SCENE

    while app.running:
        start_time = time.time()
        frame = capture_screen()
        frame_edges = preprocess_image(frame)

        futures = [executor.submit(check_template, scaled_template, frame_edges) for scaled_template in templates_edges]
        is_overlay_on = current_scene == OVERLAY_SCENE

        for future in as_completed(futures):
            result = future.result()
            if result and not is_overlay_on:
                response = ws.call(requests.SetCurrentProgramScene(sceneName=OVERLAY_SCENE))
                # print(f"OBS Response: {response}") #TODO
                current_scene = OVERLAY_SCENE
                break
            elif not result and is_overlay_on:
                response = ws.call(requests.SetCurrentProgramScene(sceneName=GAME_SCENE))
                # print(f"OBS Response: {response}") #TODO
                current_scene = GAME_SCENE
                break
            else:
                break

        elapsed_time = time.time() - start_time
        time.sleep(max(0, (MILLISECONDS_PER_CHECK / 1000) - elapsed_time))

def start_detection():
    if OBS_PASSWORD == "":
        print("No OBS websocket password provided in the config.json file")
        status_label.config(text="Status: Missing OBS websocket password", fg="red")
        return
    if GAME_SCENE == "":
        print("No OBS game scene without overlay name provided in the config.json file")
        status_label.config(text="Status: Missing OBS game scene without overlay name", fg="red")
        return
    if OVERLAY_SCENE == "":
        print("No OBS game scene with overlay name provided in the config.json file")
        status_label.config(text="Status: Missing OBS game scene with overlay name", fg="red")
        return
    if not (isinstance(TIMES_TO_CHECK, int) and 1 <= TIMES_TO_CHECK <= 20):
        print("Times to check per second in the config.json file should be a whole number between 1 and 20")
        status_label.config(text="Status: Invalid times to check per second", fg="red")
        return
    if not (isinstance(THRESHOLD, float) and 0.0 <= THRESHOLD <= 1.0 and round(THRESHOLD, 1) == THRESHOLD):
        print("Similarity accuracy in the config.json file should be a tenths place decimal point between 0.0 and 1.0")
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
    if app.running:
        stop_detection()
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
