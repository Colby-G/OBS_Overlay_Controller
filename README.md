# OBS Overlay Controller

This script is currently in open Beta testing. It is open to anyone, but realize it is still being optimized and worked on.

The OBS Overlay Controller is a simple Python script designed to detect when a template provided is visible in your game and automatically toggle an overlay in OBS. This is useful for streamers who want to prevent stream sniping by covering their in-game map(s) or other in-game screens. Disclaimer: this script, while focused on accuracy, is more largely focused on performance. This is to ensure the overlay can show as quickly as possible to cover any of the details you want it to. However, timing may not be perfect. Adjust the parameters to get maximum performance based on the load your computer can handle.

## Features

- **Automatic Detection:** Uses OpenCV for real-time detection of your current in-game screen based on templates you provide through simple screenshots.
- **OBS Integration:** Seamlessly switches between scenes automatically for you by using OBS WebSocket.
- **User-Friendly Interface:** Start and stop detection with a simple GUI.

## Requirements

- OBS Studio (v28 or later recommended)
- OBS WebSocket Plugin (built-in for OBS v28+, otherwise install separately [here](https://github.com/obsproject/obs-websocket))
- Python 3.8+
- Screenshots of **unique** in-game screens or objects for detection

## Installation

1. **Download the Repository**
   - Clone or download the project to your computer.

2. **Install Python**
   - Download and install Python from [Python.org](https://www.python.org/downloads/). Ensure you select **Add to PATH** during installation (this is on the first screen, before you click any buttons).

3. **Install Dependencies**
   - Open a terminal or command prompt and run:
   ```bash
   python -m pip install --upgrade pip
   ```
      - This ensures you have the latest version of pip.
   - Now run:
   ```bash
   python -m pip install opencv-python numpy obs-websocket-py pyscreeze Pillow mss
   ```
      - This downloads all the dependencies needed to run this script.

4. **Configure OBS**
   - Open OBS Studio.
   - Go to *Tools* → *WebSocket Server Settings*.
   - *Enable WebSocket server* and note the *Server Port* (default is 4455; leave this).
   - *Enable Authentication* if it is not already.
   - Type in your own *Server Password* (copy this).
   - Click *Apply* (confirm you are creating your own password) and then click *Ok*.

5. **Configure the Script**
   - Edit [**config.json**](config.json) with your OBS details and OBS scene names:
   ```json
   {
      "game_scene_without_overlay_name": "",
      "game_scene_with_overlay_name": "",
      "obs_websocket_password": "",
      "obs_websocket_port": 4455,
      "similarity_accuracy": 0.8,
      "times_to_check_per_second": 5
   }
   ```

6. **Prepare Your Map Templates**
   - Take screenshots of **unique** in-game screens/parts of screens/objects on specific screens, of which, when these display you wish to show an overlay.
   - Save the screenshots in the [**detection_templates**](detection_templates) folder.

## Usage

   - To run the script, open a terminal or command prompt in the repository's root folder (where the **main.py** file is located) and run:
   ```bash
   python main.py
   ```
   - Click Start in the GUI to begin detection.
      - The script will watch for your screenshots to appear on your desktop, then switch scenes automatically for you.
   - Click Stop in the GUI to end detection.

## Troubleshooting

   - Ensure OBS WebSocket server is enabled and the port/password are correct in the [**config.json**](config.json) file (case sensitive; must be exact).
      - Ensure the password is one you created and it is not an OBS generated one.
   - Ensure the OBS scene names are correct in the [**config.json**](config.json) file (case sensitive; must be exact).
   - Verify the template screenshots are clear and accurately represents your in-game screens/objects you wish to detect (screenshot only the section/object that this script should detect).
   - Adjust the similarity accuracy in the [**config.json**](config.json) file (must be a tenths place decimal point between 0.0 and 1.0; where 0.0 is no accuracy and 1.0 is perfect accuracy).
   - Adjust the times to check per second in the [**config.json**](config.json) file (must be a whole number between 1 and 20).
   - If the scene is taking awhile to transition, check your transition type in OBS. Adjust this to have a "cut" type, this will instantly switch rather than having a transition effect.
   - If you are experiencing lag while running the script, ensure the similarity accuracy and times to check per second in the [**config.json**](config.json) file are the lowest they can be while still properly detecting. Also, make sure to only have the templates needed in the [**detection_templates**](detection_templates) folder (the more you have, the more processing the script has to do). Try to find one or two templates that will work and adjust the similarity accuracy variable for optimization.

## Contributing

   - Feel free to submit issues or pull requests to improve the script.

## License

   - This project is licensed under the MIT License. See [**LICENSE**](LICENSE) for details.
