# WebUI StartGUI

## Disclaimer
As someone who isn't a professional programmer, I enjoy experimenting and finding ways to simplify my workflow. This GUI was created to make it easier for me to adjust parameters and save them for future use, without constantly modifying the webui.py or managing multiple scripts. While I'm glad to share this script with others, please understand that my expertise in maintaining it might be limited. Nonetheless, I hope it proves helpful to you, and I appreciate your understanding.

## Description
WebUI StartGUI is a Python graphical user interface (GUI) written with PyQT5, that allows users to configure settings and start the oobabooga web user interface (WebUI). It provides a convenient way to adjust various parameters and launch the WebUI with the desired settings.

## Current Features
- Select a model from a dropdown menu or none (with reload button if added while the StartUI is open)
- Choose wbits and groupsize options
- Select the operating mode (chat, cai-chat, notebook)
- Choose between CPU, GPU or Autodevice
- Set CPU RAM/GPU VRAM (Only for Nvidia Right now, will automatically detect if multiple GPU's are Present)
- Adjust pre-layer value
- Choose to run with 8bit, 16bit, trust_remote_code, Quant_attn, Autotune and no-cache flags
- Enable authentication and choose an authentication file
- Choose extensions for the WebUI
- Enable local network mode and specify the listen port
- Automatically open the browser when loading is finished
- Save settings to a profile
- Load profiles via Dropdown menu.
- Run the text-generation-webui Updater
- Character loader.
- deepspeed Settings
- flexgen Settings
- API Settings
- StartUI Update Notification

## How to Use
1. Clone the repository or download the source code.
2. Install the required dependencies listed in the `requirements.txt` file.
3. Run the `StartUI.py` script using Python `python3 StartUI.py`.
4. Configure the desired settings using the GUI elements.
5. Click the "Save Settings" button to save the current settings to a profile.
6. Click the "Load" button to load and apply settings from a saved profile.
7. Click the "Start" button to launch the WebUI with the selected settings.


## Binary Download
Binary releases of this script can be found in the [Releases](https://github.com/Pakobbix/StartUI-oobabooga-webui/releases) section of this repository.
Just put the two files into the root Folder of oobabooga (where the folder with the webui.py and the start script is).
On Linux, you'll need to give StartUI the executable flag (`chmod +x StartUI` or right click -> properties -> make executable).

The WebuiGUI.py must also be there, to handle the flags properly

## Screenshots
V1.4 :\
<details>
  
  <summary>Screenshots</summary>

  ![1 4](https://github.com/Pakobbix/StartUI-oobabooga-webui/assets/6762686/7f252274-b20b-4e52-9789-fc45645faf03)

  ![1 4 deepspeed](https://github.com/Pakobbix/StartUI-oobabooga-webui/assets/6762686/b3c566c3-bfa2-4d38-a1af-cee82bf6f5fa)

  ![1 4 llama options](https://github.com/Pakobbix/StartUI-oobabooga-webui/assets/6762686/8b7bb61d-9ab5-4e54-b4e2-34ec1a36439a)

  ![1 4 flexgen](https://github.com/Pakobbix/StartUI-oobabooga-webui/assets/6762686/def814cb-4f69-4a39-91cd-6731155c12a3)

  ![1 4 multi settings](https://github.com/Pakobbix/StartUI-oobabooga-webui/assets/6762686/f3478ff1-bcba-4935-9e4c-efb1a2e64dcd)

  </details>



## Credits
StartGUI is developed and maintained by [Pakobbix](https://github.com/Pakobbix). 
It is based on the [PyQt5](https://pypi.org/project/PyQt5/) library and uses [gpustat](https://pypi.org/project/gpustat/) for GPU information.
[Oobabooga](https://github.com/oobabooga/text-generation-webui) for his great webui.
