# OBS Overlay Controller

**Note:** This script is currently in open Beta testing. It is available for anyone to try, but please note that it is still being optimized and refined.
The OBS Overlay Controller is a lightweight Python script designed to detect when a specific in-game screen or object is visible and automatically toggle an overlay in OBS. This is particularly useful for streamers who want to prevent stream sniping by covering in-game maps or sensitive screens.
**Disclaimer:** While the script prioritizes accuracy, its main focus is on performance to ensure the overlay appears as quickly as possible. Adjust the parameters for optimal results based on your computer's performance.

## Features

- **Automatic Detection:** Uses OpenCV for real-time detection using custom templates based on your screenshots.
- **OBS Integration:** Automatically toggles an overlay source using OBS WebSocket.
- **User-Friendly Interface:** Simple GUI to start and stop detection.

## Requirements

- OBS Studio (v28 or later recommended)
- OBS WebSocket Plugin (built-in for OBS v28+, or install separately [here](https://github.com/obsproject/obs-websocket))
- Python 3.8+
- Clear, high-quality screenshots of unique in-game screens or objects for detection

## Installation

1. **Download the Repository**
   - Clone or download the project to your computer.

2. **Install Python**
   - Download and install Python from [Python.org](https://www.python.org/downloads/). Ensure **Add to PATH** is selected during installation.

3. **Install Dependencies**
   - Open a terminal or command prompt and run:
   ```bash
   python -m pip install --upgrade pip
   ```
   - Then install the necessary packages:
   ```bash
   python -m pip install opencv-python numpy obs-websocket-py pyscreeze Pillow mss
   ```

4. **Configure OBS**
   - Open OBS Studio.
   - Go to *Tools* → *WebSocket Server Settings*.
   - Enable the WebSocket server and note the **Server Port** (default is 4455).
   - Enable **Authentication** and set your own **Server Password**.
   - Click **Apply** and **Ok**.

5. **Configure the Script**
   - Edit [**config.json**](config.json) with your OBS details:
   ```json
   {
      "highest_scale_of_templates": 1,
      "lowest_scale_of_templates": 0.6,
      "number_of_scaled_templates": 3,
      "obs_overlay_source_name": "",
      "obs_scene_name": "",
      "obs_websocket_password": "",
      "obs_websocket_port": 4455,
      "screenshot_delay": 0.05,
      "similarity_accuracy": 0.8
   }
   ```

6. **Prepare Your Templates**
   - Take clear screenshots of the in-game screens, objects, or UI elements you wish to detect.
   - Save these screenshots in the [**detection_templates**](detection_templates) folder.

## Usage

   - Open a terminal or command prompt in the root folder (where this **README.md** file is located) and run:
   ```bash
   python main.py
   ```
   - Click Start in the GUI to begin detection.
   - The overlay will automatically toggle based on the templates detected.
   - Click Stop in the GUI to end detection.

## Troubleshooting

   - Before troubleshooting, you should properly understand how the script works with the config values [here](#deep-dive-into-the-script).

   - Ensure OBS WebSocket server is enabled and the port/password match the [**config.json**](config.json) file (case sensitive; must be exact).
      - Ensure the password is one you created and it is not an OBS generated one.
   - Ensure both the OBS overlay source name and OBS scene name match the [**config.json**](config.json) file (case sensitive; must be exact).
   - Confirm your template screenshots are clear, accurate, and representative of the in-game sections or objects you wish to detect (screenshot only the section/object that this script should detect).
   - If you have not already, take your own screenshots. Do not use screenshots from someone else, as differences in resolution can affect how the templates are found.
   - If you are experiencing lag while running the script:
      - Adjust the similarity accuracy in the [**config.json**](config.json) file to find a balance between detection accuracy and performance (must be a decimal point between 0.0 and 1.0; where 0.0 is no accuracy and 1.0 is perfect accuracy).
      - Remove unnecessary templates from the [**detection_templates**](detection_templates) folder (the more you have, the more processing the script has to do). Try to find only one or two templates that will work and adjust the similarity accuracy variable for optimization.
      - Adjust the lowest scale of templates and the highest scale of templates in the [**config.json**](config.json) file to minimize scaling. You want these numbers to be as close as possible without it negatively impacting the detection of the templates.
      - Reduce the number of scaled templates in the [**config.json**](config.json) file to minimize scaling. You want this number to be as small as possible without it negatively impacting the detection of the templates.
      - Increasing the screenshot delay in the [**config.json**](config.json) file to reduce CPU load. The higher the number, the slower detection, but can help decrease CPU load.

## Deep Dive into the Script

   - After running the command, a simple GUI interface will populate with a status, a start button, and a stop button. At this point, all the config values have been collected, but no connection to OBS nor any validation of config values has been done.
   - Clicking the start button initiates the verification of all config values to ensure they are properly formatted.
   - The script then processes and scales all the templates to prepare them for fast and efficient detection.
      - Templates are converted to gray scale and normalized for faster matching.
      - Multiple scaled versions of each template are created based on the configuration, increasing the likelihood of detection.
         - It takes in the lowest and highest scale values and the number of scales to create, then equally distributes the scales between the values given for the number of scales you want (i.e., if you have 2 templates and tell it to make 3 scales, then in the end you will have 6 total, 3 for each template).
   - If valid templates exist, the script attempts to establish an OBS connection, ensuring the correct scene is selected and the overlay source is initially hidden.
   - The main detection loop starts:
      - A screenshot of the primary display is taken and processed into gray scale.
      - The script uses multithreading to compare the screenshot to all templates in parallel.
      - If a match is detected above the specified similarity accuracy config value, the overlay is triggered.
      - To avoid redundant actions, the script only sends updates to OBS if the overlay state changes.
   - Clicking the stop button ends detection but leaves the OBS connection intact, allowing for quick restarts.
      - If new templates are added, the script only needs to be stopped and started again using the buttons.
      - If the config values are changed, the whole GUI needs to be closed out and started again using the command in the [usage](#usage) section.

## Contributing

   - Contributions are welcome! Submit issues or pull requests to help improve the script.

## License

   - This project is licensed under the MIT License. See [**LICENSE**](LICENSE) for details.
