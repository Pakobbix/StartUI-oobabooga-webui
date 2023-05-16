import sys, gpustat, os, json, subprocess, platform, psutil, re, requests, darkdetect, qdarkstyle
from PyQt5.QtWidgets import QApplication, QToolBar, QMessageBox, QAction, QMainWindow, QLabel, QVBoxLayout, QComboBox, QSlider, QCheckBox, QLineEdit, QFileDialog, QPushButton, QWidget, QListWidget, QListWidgetItem, QGridLayout, QRadioButton, QFrame
from PyQt5.QtCore import Qt

version = "1.3.1"

profiles_folder = "./profiles"
os.makedirs(profiles_folder, exist_ok=True)
model_folder = "./text-generation-webui/models"
extensions_folder = "./text-generation-webui/extensions"
loras_folder = "./text-generation-webui/loras"
try:
    output = subprocess.check_output(['nvidia-smi'])
    nvidia_gpu = True
except:
    nvidia_gpu = False
    pass


# # Get the absolute path of the script file
script_path = os.path.abspath(__file__)

# Define the path of the settings file relative to the script file
settings_file = os.path.join(os.path.dirname(script_path), "gui-config.json")

# Define the conda environment path
if platform.system() == 'Windows':
    # Sets the Conda Environment based on Windows
    conda_binary = r".\installer_files\conda\condabin\conda.bat"
    conda_env_path = r".\installer_files\env"
if platform.system() == 'Linux':
    # Sets the Conda Environment based on Linux
    conda_binary = "./installer_files/conda/condabin/conda"
    conda_env_path = "./installer_files/env"

def run_cmd_with_conda(cmd, env=None):
    if platform.system() == 'Windows':
        # For Windows, activate the Conda environment using the activate.bat script
        activate_cmd = f"{conda_binary} activate {conda_env_path} && "
        full_cmd = activate_cmd + cmd

        # Open a separate terminal window and execute the command
        subprocess.Popen(['start', 'cmd', '/k', full_cmd], shell=True, env=env)
    elif platform.system() == 'Linux':
        # Define the necessary variables from the bash script
        install_dir = os.path.dirname(os.path.abspath(__file__))
        conda_root_prefix = os.path.join(install_dir, "installer_files", "conda")
        install_env_dir = os.path.join(install_dir, "installer_files", "env")

        # For Linux, activate the Conda environment
        activate_cmd = f"source {os.path.join(conda_root_prefix, 'etc', 'profile.d', 'conda.sh')} && conda activate {install_env_dir}"

        # Check for available terminal emulators
        terminal_emulators = ['xdg-terminal', 'gnome-terminal', 'konsole', 'xfce4-terminal', 'mate-terminal', 'lxterminal', 'termite', 'tilix', 'xterm']
        terminal_cmd = None

        for emulator in terminal_emulators:
            try:
                subprocess.run([emulator, '--version'], check=True)
                terminal_cmd = emulator
                break
            except FileNotFoundError:
                continue

        if terminal_cmd is None:
            raise RuntimeError("No compatible terminal emulator found.")

        # Execute the command within the Conda environment in a separate terminal
        print(cmd)
        subprocess.Popen([terminal_cmd, '--', 'bash', '-c', f"{activate_cmd} && {cmd}"], env=env)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.load_settings()
        self.set_ram_slider_max()
        self.update_check()

    def init_ui(self):
        self.setWindowTitle(f'StartUI for oobabooga webui v{version}')
        # Menu Bar
        menu = self.menuBar()

        # Main menu
        main_menu = menu.addMenu("StartUI")
        main_menu.addAction("Exit", self.close)

        # help menu
        help_menu = menu.addMenu("Help")

        # Help menu actions
        # Github action
        github_action = QAction("Github", self)
        github_action.setStatusTip("Opens the Github Page")
        github_action.triggered.connect(self.on_Github_clicked)
        help_menu.addAction(github_action)

        # Oobabooga action
        oobabooga_action = QAction("oobabooga", self)
        oobabooga_action.setStatusTip("Opens the oobabooga Github Page")
        oobabooga_action.triggered.connect(self.on_oobabooga_clicked)
        help_menu.addAction(oobabooga_action)

        # Version action
        version_action = QAction(f"Version: {version}", self)
        version_action.setStatusTip("Shows the Version of StartUI")
        help_menu.addAction(version_action)
        version_action.triggered.connect(self.show_version_window)

        # About Action
        about_action = QAction("About", self)
        about_action.setToolTip("Opens the About Page")
        about_action.triggered.connect(self.show_about_window)
        help_menu.addAction(about_action)

        # seperator
        help_menu.addSeparator()

        # Report Bug
        report_bug_action = QAction("Report Bug", self)
        report_bug_action.setToolTip("Opens the Github Issue Page with creating a new issue")
        report_bug_action.triggered.connect(self.on_report_bug_clicked)
        help_menu.addAction(report_bug_action)

        layout = QGridLayout()
        layout.setColumnMinimumWidth(0, 350)
        layout.setColumnMinimumWidth(3, 30)

        # Model Dropdown
        # Get the list of model folders
        model_folders = [name for name in os.listdir(model_folder) if os.path.isdir(os.path.join(model_folder, name))]
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItem("none")
        self.model_dropdown.addItems(model_folders)
        layout.addWidget(QLabel("Choose Model:"))
        self.model_dropdown.setToolTip("Select your prefered Model")
        layout.addWidget(self.model_dropdown, 1, 0)

        self.model_type = QComboBox()
        self.model_type.addItems(["none", "llama", "opt", "gptj"])
        layout.addWidget(QLabel("Choose Model Type:"), 3, 0)
        self.model_type.setToolTip("Select the Model Type")
        layout.addWidget(self.model_type, 4, 0)

        self.reload_model_button = QPushButton("Reload")
        self.reload_model_button.setToolTip("Reloads the Names in the Models Folder")
        self.reload_model_button.clicked.connect(self.reload_models)
        layout.addWidget(QLabel("Reload the Model list:"),0, 1)
        layout.addWidget(self.reload_model_button, 1, 1, 1 , 2)

        # WBIT Dropdown Menu
        self.wbit_dropdown = QComboBox()
        self.wbit_dropdown.addItems(["none", "1", "2", "3", "4","8"])
        layout.addWidget(QLabel("Choose Wbits:"),5, 0)
        self.wbit_dropdown.setToolTip("Select the bits quantization for this model\nExample: vicuna 7b 4bit you should choose 4.\nYou can keep it at none, the webui will determine it automatically if the wbits are mentioned in the name of the model")
        layout.addWidget(self.wbit_dropdown, 6, 0)

        # Groupsize Dropdown Menu
        self.gsize_dropdown = QComboBox()
        self.gsize_dropdown.addItems(["none", "32", "64", "128", "1024"])
        layout.addWidget(QLabel("Choose Groupsize:"), 5, 1)
        self.gsize_dropdown.setToolTip("Select the groupsize used by the Model.\nExample: vicuna 7b 4bit-128g you should choose 128.\nYou can keep it at none, the webui will determine it automatically if the groupsize is mentioned in the name of the model")
        layout.addWidget(self.gsize_dropdown, 6, 1, 1, 2)

        # Mode Dropdown
        self.mode_dropdown = QComboBox()
        self.mode_dropdown.addItems(["chat", "cai_chat", "notebook"])
        layout.addWidget(QLabel("Choose Mode:"), 7, 0)
        self.mode_dropdown.setToolTip("Choose what kind of UI you want to load.")
        layout.addWidget(self.mode_dropdown, 8, 0)

        self.update_button = QPushButton("Update oobabooga")
        self.update_button.setToolTip("Starts the Update Routine for the text-generation-webui")
        self.update_button.clicked.connect(self.on_update_button_clicked)
        layout.addWidget(self.update_button, 8, 1, 1, 2)
        layout.addWidget(QLabel("Update the text-generation-webui:"), 7, 1)

        # Add horizontal line to seperate the CPU/GPU Settings
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line, 9, 0, 1, 3)

        # GPU Checkbox and Sliders
        self.gpu_radio_button = QRadioButton("Use GPU")
        if nvidia_gpu:
            self.gpu_radio_button.setChecked(True)
            self.gpu_radio_button.setToolTip("Choose if you want to use your GPU")
        else:
            self.gpu_radio_button.setToolTip("AMD or Intel GPU's are currently not supported.")
            self.gpu_radio_button.setChecked(False)
            self.gpu_radio_button.setEnabled(False)
        layout.addWidget(self.gpu_radio_button, 10, 0)
    
        self.cpu_radio_button = QRadioButton("Use CPU")
        self.cpu_radio_button.setToolTip("Choose if you want to use your CPU")
        self.cpu_radio_button.setChecked(False)
        layout.addWidget(self.cpu_radio_button, 10, 1)

        self.auto_radio_button = QRadioButton("Autodevice")
        self.auto_radio_button.setToolTip("Let the webui decide whats best for you!")
        if nvidia_gpu:
            self.auto_radio_button.setChecked(False)
        else:
            self.auto_radio_button.setChecked(True)
        layout.addWidget(self.auto_radio_button, 10, 2)
    
        self.gpu_radio_button.toggled.connect(self.on_gpu_radio_button_toggled)
        self.cpu_radio_button.toggled.connect(self.on_cpu_radio_button_toggled)
        self.auto_radio_button.toggled.connect(self.on_auto_radio_button_toggled)
    
        if nvidia_gpu:
            self.gpu_vram_sliders = []
            self.gpu_vram_labels = []
            self.gpu_labels = []
            gpu_stats = gpustat.GPUStatCollection.new_query()
    
            for i, gpu in enumerate(gpu_stats):
                gpu_label = QLabel(f"{gpu.name} VRAM:")
                gpu_label.setToolTip(f"Total VRAM: {gpu.memory_total} MiB\nUsed VRAM: {gpu.memory_used} MiB\nFree VRAM: {gpu.memory_free} MiB")
                layout.addWidget(gpu_label, 11 + i, 0)
                self.gpu_labels.append(gpu_label)
        
                vram_slider = QSlider(Qt.Horizontal)
                vram_slider.setMaximum(int(gpu.memory_total / 1024))
                vram_slider.valueChanged.connect(lambda value, idx=i: self.on_vram_slider_changed(value, idx))
                layout.addWidget(vram_slider, 11 + i, 1)
        
                vram_value_label = QLabel("0 GiB")
                layout.addWidget(vram_value_label, 11 + i, 2)
                self.gpu_vram_labels.append(vram_value_label)
        
                self.gpu_vram_sliders.append(vram_slider)
        else:
            gpu_stats = [""]

        # Create the "Built-in RAM" label, slider, and value label
        self.ram_label = QLabel("Built-in RAM:")
        ram_info = psutil.virtual_memory()
        total_ram = ram_info.total // (1024 ** 2)  # Convert to MiB
        used_ram = ram_info.used // (1024 ** 2)  # Convert to MiB
        free_ram = ram_info.available // (1024 ** 2)  # Convert to MiB
        self.ram_label.setToolTip(f"Total RAM: {total_ram} MiB\nUsed RAM: {used_ram} MiB\nFree RAM: {free_ram} MiB")
        self.ram_label.hide()
        layout.addWidget(self.ram_label, 11, 0)
    
        self.ram_slider = QSlider(Qt.Horizontal)
        self.ram_slider.setMinimum(0)
        self.ram_slider.setMaximum(100)
        self.ram_slider.setTickInterval(1)
        self.ram_slider.setSingleStep(1)
        self.ram_slider.hide()
        layout.addWidget(self.ram_slider, 11, 1)
    
        self.ram_value_label = QLabel("0 GiB")
        self.ram_value_label.hide()
        layout.addWidget(self.ram_value_label, 11, 2)

        # Pre-layer Slider
        self.pre_layer_slider = QSlider(Qt.Horizontal)
        self.pre_layer_slider.setMinimum(0)
        self.pre_layer_slider.setMaximum(100)
        self.pre_layer_slider.setTickInterval(1)
        self.pre_layer_slider.setSingleStep(1)
        layout.addWidget(QLabel("Pre-layer:"), 11 + len(gpu_stats), 0)
        self.pre_layer_slider.setToolTip("The number of layers to allocate to the GPU. Setting this parameter enables CPU offloading for 4-bit models.")
        layout.addWidget(self.pre_layer_slider, 11 + len(gpu_stats), 1)
        self.pre_layer_slider.valueChanged.connect(self.on_pre_layer_slider_changed)

        self.pre_layer_value_label = QLabel("0")
        layout.addWidget(self.pre_layer_value_label, 11 + len(gpu_stats), 2)

        # Connect the valueChanged signal of the RAM slider to update the value label
        self.ram_slider.valueChanged.connect(self.on_ram_slider_changed)

        # Add horizontal line to seperate the Checkboxes
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line, 12 + len(gpu_stats), 0, 1, 3)

        # Load in 8 Bit Mode
        self.use_8bit_checkbox = QCheckBox("Load in 8bit")
        self.use_8bit_checkbox.setToolTip("VRAM Reducing!\nReduces memory usage and computational complexity at the cost of lower precision compared to higher precision representations.")
        layout.addWidget(self.use_8bit_checkbox, 13 + len(gpu_stats), 0)

        # Deactivate Streaming Output
        self.use_nostream_checkbox = QCheckBox("No Stream")
        self.use_nostream_checkbox.setToolTip("Don't stream the text output in real time. Increases Token/s by ~ 50%")
        layout.addWidget(self.use_nostream_checkbox, 13 + len(gpu_stats), 1)

        # Load in full 16bit precision
        self.use_16bit_checkbox = QCheckBox("Load in 16bit")
        self.use_16bit_checkbox.setToolTip("Load the model with bfloat16 precision. Requires NVIDIA Ampere GPU.")
        layout.addWidget(self.use_16bit_checkbox, 14 + len(gpu_stats), 0)

        # Use xformers
        self.use_xformers_checkbox = QCheckBox("xformers")
        self.use_xformers_checkbox.setToolTip("Use xformer's memory efficient attention. This should increase your tokens/s.")
        layout.addWidget(self.use_xformers_checkbox, 14 + len(gpu_stats), 1)

        # Make use of Remote Code Execution (MPT-7B)
        self.use_trc_checkbox = QCheckBox("trust-remote-code")
        self.use_trc_checkbox.setToolTip("Set trust_remote_code=True while loading a model. Necessary for ChatGLM and MPT-7B.")
        layout.addWidget(self.use_trc_checkbox, 15 + len(gpu_stats), 0)

        # Load with Monkey-Patch enabled
        self.use_monkey_checkbox = QCheckBox("Monkey Patch")
        self.use_monkey_checkbox.setToolTip("Apply the monkey patch for using LoRAs with quantized models.")
        layout.addWidget(self.use_monkey_checkbox, 15 + len(gpu_stats), 1)

        # Use Triton Quant-ATTN
        self.use_quant_checkbox = QCheckBox("Quant_attn")
        self.use_quant_checkbox.setToolTip("(triton) Enable quant attention.")
        layout.addWidget(self.use_quant_checkbox, 16 + len(gpu_stats), 0)

        # Use Triton Warmup & Autotune
        self.use_autotune_checkbox = QCheckBox("Warmup-Autotune")
        self.use_autotune_checkbox.setToolTip("(triton) Enable warmup autotune.")
        layout.addWidget(self.use_autotune_checkbox, 16 + len(gpu_stats), 1)

        # Disable Cache for better VRAM
        self.use_nocache_checkbox = QCheckBox("No Cache")
        self.use_nocache_checkbox.setToolTip("VRAM Reducing!\nSet use_cache to False while generating text. This reduces the VRAM usage a bit with a performance cost.")
        layout.addWidget(self.use_nocache_checkbox, 17 + len(gpu_stats), 1)

        # Use DISK to load part of the model
        self.use_disk_checkbox = QCheckBox("Use DISK")
        self.use_disk_checkbox.setToolTip("If the model is too large for your GPU(s) and CPU combined, send the remaining layers to the disk.")
        layout.addWidget(self.use_disk_checkbox, 17 + len(gpu_stats), 0)
        self.use_disk_checkbox.stateChanged.connect(self.on_use_disk_checkbox_changed)

        # Use DISK to load part of the model
        self.change_disk_cache_checkbox = QCheckBox("Change Disk Cache")
        self.change_disk_cache_checkbox.setVisible(False)
        self.change_disk_cache_checkbox.setToolTip("OPTIONAL: Change the disk cache directory.")
        layout.addWidget(self.change_disk_cache_checkbox, 18 + len(gpu_stats), 0)
        self.change_disk_cache_checkbox.stateChanged.connect(self.on_change_disk_cache_checkbox_changed)

        # Current Cache Folder
        self.disk_cache_path = ""
        self.current_disk_cache_label = QLabel("Current Cache Folder:")
        self.current_disk_cache_label.setVisible(False)
        self.current_disk_cache_label.setToolTip("The current disk cache folder.")
        layout.addWidget(self.current_disk_cache_label, 18 + len(gpu_stats), 1)

        # Choose Folder Field
        self.choose_disk_folder_label = QLabel("Choose Folder:")
        self.choose_disk_folder_label.setVisible(False)
        self.choose_disk_folder_label.setToolTip("Choose a folder to use for the disk cache.")
        layout.addWidget(self.choose_disk_folder_label, 19 + len(gpu_stats), 0)

        # Choose Folder button
        self.choose_disk_folder_button = QPushButton("Choose Folder")
        self.choose_disk_folder_button.setVisible(False)
        self.disk_cache_textfield = QLineEdit()
        self.choose_disk_folder_button.setToolTip("Choose a folder to use for the disk cache.")
        self.choose_disk_folder_button.clicked.connect(self.on_choose_disk_folder_button_clicked)
        layout.addWidget(self.choose_disk_folder_button, 19 + len(gpu_stats), 1)

        # Add horizontal line to seperate the Checkboxes
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line, 21 + len(gpu_stats), 0, 1, 3)

        # Authentication Checkbox
        self.authentication_checkbox = QCheckBox("Authentication")
        self.authentication_checkbox.setToolTip("Enable gradio authentication")
        layout.addWidget(self.authentication_checkbox, 22 + len(gpu_stats), 0)
        self.authentication_checkbox.stateChanged.connect(self.on_authentication_checkbox_changed)

        # Choose File Field
        self.choose_file_label = QLabel("Choose File:")
        self.choose_file_label.setVisible(False)
        self.choose_file_label.setToolTip("Choose a file to use for the authentication credentials. Credentials should be saved like:\nUSERNAME1:PASSWORD1\nUSERNAME2:PASSWORD2")
        layout.addWidget(self.choose_file_label, 23 + len(gpu_stats), 0)

        self.choose_file_button = QPushButton("Browse")
        self.choose_file_button.setVisible(False)
        self.choose_file_button.setToolTip("Choose a file to use for the authentication credentials. Credentials should be saved like:\nUSERNAME1:PASSWORD1\nUSERNAME2:PASSWORD2")
        self.choose_file_button.clicked.connect(self.on_choose_file_button_clicked)
        layout.addWidget(self.choose_file_button, 24 + len(gpu_stats), 0)

        # Extensions Selection Menu
        self.use_extensions_checkbox = QCheckBox("Use Extensions")
        self.use_extensions_checkbox.setToolTip("Choose the extensions to be loaded.")
        layout.addWidget(self.use_extensions_checkbox, 25 + len(gpu_stats), 0)
        self.use_extensions_checkbox.stateChanged.connect(self.on_use_extensions_checkbox_changed)

        self.extensions_list = QListWidget()
        self.extensions_list.setToolTip("Choose the extensions to be loaded.")
        layout.addWidget(self.extensions_list, 25 + len(gpu_stats), 1, 1, 2)
        self.extensions_list.setVisible(False)
        extensions = [name for name in os.listdir(extensions_folder) if os.path.isdir(os.path.join(extensions_folder, name))]

        for extension in extensions:
            item = QListWidgetItem(extension)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.extensions_list.addItem(item)

        # Lora selection menu
        self.use_lora_checkbox = QCheckBox("Use Loras")
        self.use_lora_checkbox.setToolTip("Choose the loras to be loaded.")
        layout.addWidget(self.use_lora_checkbox, 26 + len(gpu_stats), 0)
        self.use_lora_checkbox.stateChanged.connect(self.on_use_lora_checkbox_changed)

        self.lora_list = QListWidget()
        self.lora_list.setToolTip("Choose the loras to be loaded.")
        layout.addWidget(self.lora_list, 26 + len(gpu_stats), 1, 1, 2)
        self.lora_list.setVisible(False)
        
        loras = [name for name in os.listdir(loras_folder) if os.path.isdir(os.path.join(loras_folder, name))]
        for lora in loras:
            item = QListWidgetItem(lora)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.lora_list.addItem(item)

        # Use Whole Local Network
        self.use_network_checkbox = QCheckBox("Local Network Mode")
        self.use_network_checkbox.setToolTip("By default, the WebUI will only be reachable by the PC running it.\nIf you want to use it also on other devices, check this")
        layout.addWidget(self.use_network_checkbox, 30 + len(gpu_stats), 0)
    
        # Listen Port Checkbox and Text Field
        self.listen_port_checkbox = QCheckBox("Listen Port")
        self.listen_port_checkbox.setToolTip("Choose the Port to use for the WebUI.\nDefault is 7680. If you want to use Stable Diffusion at the same time,\nor got other services running on this Port, you can change it in the textfield.")
        self.listen_port_checkbox.stateChanged.connect(self.on_listen_port_checkbox_changed)
        layout.addWidget(self.listen_port_checkbox, 30 + len(gpu_stats), 1)
    
        self.listen_port_textfield = QLineEdit()
        self.listen_port_textfield.setPlaceholderText("Enter port number")
        self.listen_port_textfield.setEnabled(False)
        layout.addWidget(self.listen_port_textfield, 31 + len(gpu_stats), 1)
    
        # Use Automatically opens the Browser when finished loading the webui
        self.use_autolaunch_checkbox = QCheckBox("Auto open Browser")
        self.use_autolaunch_checkbox.setToolTip("Automatically Opens your browser when loading is finished")
        layout.addWidget(self.use_autolaunch_checkbox, 32 + len(gpu_stats), 0)

        # Auto Close the GUI when pressing start.
        self.use_autoclose_checkbox = QCheckBox("Close GUI on Start")
        self.use_autoclose_checkbox.setToolTip("Auto Close the GUI when pressing start button.")
        layout.addWidget(self.use_autoclose_checkbox, 32 + len(gpu_stats), 1)
    
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.start_button = QPushButton("Start")
        self.start_button.setToolTip("Starts the Webui with the settings set by this GUI")
        self.start_button.clicked.connect(self.on_start_button_clicked)
        layout.addWidget(self.start_button, 33 + len(gpu_stats), 0)

        self.save_button = QPushButton("Save Settings")
        self.save_button.setToolTip("You can Save your current Settings. Neat, isn't it?")
        self.save_button.clicked.connect(self.on_save_button_clicked)
        layout.addWidget(self.save_button, 34 + len(gpu_stats), 0)

        # Textfield for the Profile Name
        self.profile_name_textfield = QLineEdit()
        self.profile_name_textfield.setPlaceholderText("Enter Name for the Profile, keep empty to overwrite default")
        self.profile_name_textfield.setToolTip("You can leave this blank, then only the default profile will be overwritten. If you want to get some organizing done, you can name it. For example:\nProfile for RP\nProfile for Chat\nProfile for coding\nProfile for Superbooga\nERROR: 404 no limits found")
        layout.addWidget(self.profile_name_textfield, 35 + len(gpu_stats), 0)

        # Profiles Dropdown
        self.profiles_dropdown = QComboBox()
        self.populate_profiles_dropdown()
        self.profiles_dropdown.setToolTip("Here you can choose which profile you want to load. Choose, Load, Profit.")
        layout.addWidget(QLabel("Choose Profile:"), 33 + len(gpu_stats), 1)
        layout.addWidget(self.profiles_dropdown, 35 + len(gpu_stats), 1)
    
        # Load Button
        self.load_button = QPushButton("Load")
        self.load_button.setToolTip("It's a button. That loads a selected Profile. Sometimes, I'm just create explaining things.")
        self.load_button.clicked.connect(self.on_load_button_clicked)
        layout.addWidget(self.load_button, 34 + len(gpu_stats), 1)

        # Show if Update is available
        self.update_button_ui = QPushButton("Update\nAvailable")
        self.update_button_ui.setToolTip("Shows if an update is available")
        self.update_button_ui.setStyleSheet("QPushButton { color: #ff9999; font-weight: bold; }")
        self.update_button_ui.clicked.connect(self.on_update_button_ui_clicked)
        layout.addWidget(self.update_button_ui, 34 + len(gpu_stats), 2, 2, 2)
        self.update_button_ui.setVisible(False)

    def on_update_button_ui_clicked(self):
        self.show_version_window()

    def update_check(self):
        latest_version = self.get_latest_version()
        if latest_version and latest_version > version:
            self.update_button_ui.setVisible(True)

    def show_version_window(self):
        latest_version = self.get_latest_version()
        if latest_version and latest_version > version:
            release_notes = self.get_release_notes()
            update_text = f"A new version ({latest_version}) is available! Do you want to update?\n\n\n{release_notes}"
            reply = QMessageBox.question(self, "Update Available", update_text, QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                release_url = f"https://github.com/Pakobbix/StartUI-oobabooga-webui/releases/tag/{latest_version}"
                if sys.platform == "win32":
                    os.startfile(release_url)
                else:
                    try:
                        subprocess.Popen(["xdg-open", release_url])
                    except OSError:
                        self.show_error_message("Error", f"Could not open the link. Please open it manually.\n{release_url}")

    def on_report_bug_clicked(self):
        github_new_issue = "https://github.com/Pakobbix/StartUI-oobabooga-webui/issues/new"
        if sys.platform == "win32":
            os.startfile(github_new_issue)
        else:
            try:
                subprocess.Popen(["xdg-open", github_new_issue])
            except OSError:
                self.show_error_message("Error", f"Could not open the link. Please open it manually.\n{github_new_issue}")

    def on_Github_clicked(self):
        startui_url = "https://github.com/Pakobbix/StartUI-oobabooga-webui/"
        if sys.platform == "win32":
            os.startfile(startui_url)
        else:
            try:
                subprocess.Popen(["xdg-open", startui_url])
            except OSError:
                self.show_error_message("Error", f"Could not open the link. Please open it manually.\n{startui_url}")

    def on_oobabooga_clicked(self):
        oobabooga_url = "https://github.com/oobabooga/text-generation-webui"
        if sys.platform == "win32":
            os.startfile(oobabooga_url)
        else:
            try:
                subprocess.Popen(["xdg-open", oobabooga_url])
            except OSError:
                self.show_error_message("Error", f"Could not open the link. Please open it manually.\n{oobabooga_url}")

    def get_latest_version(self):
        try:
            url = "https://api.github.com/repos/Pakobbix/StartUI-oobabooga-webui/releases/latest"
            response = requests.get(url)
            if response.status_code == 200:
                latest_release = response.json()
                tag_name = latest_release["tag_name"]
                return tag_name
            else:
                return None
        except Exception as e:
            print(f"Error fetching latest version: {str(e)}")
            return None

    def get_release_notes(self):
        try:
            url = "https://api.github.com/repos/Pakobbix/StartUI-oobabooga-webui/releases/latest"
            response = requests.get(url)
            if response.status_code == 200:
                latest_release = response.json()
                release_notes = latest_release["body"]
                return release_notes
            else:
                return None
        except Exception as e:
            print(f"Error fetching release notes: {str(e)}")
            return None

    def show_about_window(self, action):
        latest_version = self.get_latest_version()
        release_url = f"https://github.com/Pakobbix/StartUI-oobabooga-webui/releases/tag/{latest_version}"
        if latest_version and latest_version > version:
            about_text = f"A new version ({latest_version}) is available! Please <a href='{release_url}'>update.</a> <br><br>StartUI for oobabooga's webui.<br><br> Current Version: {version}<br><br>This is an GUI (Graphical User Interface), to set flags depending on the user selection."
        else:
            about_text = f"StartUI for oobabooga's webui.\n\nVersion: {version}\n\nThis is an GUI (Graphical User Interface), to set flags depending on the user selection."
        QMessageBox.about(self, "About", about_text)

    def on_use_extensions_checkbox_changed(self, state):
        self.extensions_list.setVisible(state == Qt.Checked)

    def on_use_lora_checkbox_changed(self, state):
        self.lora_list.setVisible(state == Qt.Checked)

    
    def on_use_disk_checkbox_changed(self, state):
        self.change_disk_cache_checkbox.setVisible(state == Qt.Checked)
        self.current_disk_cache_label.setVisible(state == Qt.Checked)
    
        if state == Qt.Checked:
            # Check if disk cache path is empty
            if not self.disk_cache_path:
                # Set default disk cache path
                self.disk_cache_path = "/cache"
                # Update the label text
                self.current_disk_cache_label.setText(f"Current Cache Folder: {self.disk_cache_path}")

    def on_change_disk_cache_checkbox_changed(self, state):
        self.choose_disk_folder_label.setVisible(state == Qt.Checked)
        self.choose_disk_folder_button.setVisible(state == Qt.Checked)

    def on_choose_disk_folder_button_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Disk Cache Folder")
        if folder:
            self.disk_cache_textfield.setText(folder)
            self.disk_cache_path = folder
            self.current_disk_cache_label.setText(f"Current Cache Folder: {self.disk_cache_path}")

    def show_error_message(self, message):
        QMessageBox.critical(self, "Error", message)

    def reload_models(self):
        model_folders = [name for name in os.listdir(model_folder) if os.path.isdir(os.path.join(model_folder, name))]
        self.model_dropdown.clear()  # Clear the existing items
        self.model_dropdown.addItems(model_folders)  # Add the updated items

    def set_ram_slider_max(self):
        ram_size = psutil.virtual_memory().available
        ram_size_gb = ram_size // (1024 ** 3)
        self.ram_slider.setMaximum(ram_size_gb)

    def on_ram_slider_changed(self, value):
        self.ram_value_label.setText(f"{value} GiB")

    def on_pre_layer_slider_changed(self, value):
        # Update the value label with the current value of the pre-layer slider
        self.pre_layer_value_label.setText(str(value))

    def on_vram_slider_changed(self, value, gpu_idx):
        self.gpu_vram_labels[gpu_idx].setText(f"{value} GiB")
        #print(f"GPU {gpu_idx} VRAM usage: {value} GiB")

    def on_gpu_radio_button_toggled(self, checked):
        # Hide/show GPU-related widgets
        for slider, label_vram, label_gpu in zip(self.gpu_vram_sliders, self.gpu_vram_labels, self.gpu_labels):
            slider.setVisible(checked)
            label_vram.setVisible(checked)
            label_gpu.setVisible(checked)
    
        # Hide RAM slider and value label
        self.ram_label.hide()
        self.ram_slider.hide()
        self.ram_value_label.hide()
    
        # Uncheck CPU and Autodevice radio buttons
        if checked:
            self.cpu_radio_button.setChecked(False)
            self.auto_radio_button.setChecked(False)
    
    def on_cpu_radio_button_toggled(self, checked):
        # Hide/show GPU-related widgets
        if nvidia_gpu:
            for slider, label_vram, label_gpu in zip(self.gpu_vram_sliders, self.gpu_vram_labels, self.gpu_labels):
                slider.hide()
                label_vram.hide()
                label_gpu.hide()
    
        # Show RAM slider and value label
        self.ram_label.setVisible(checked)
        self.ram_slider.setVisible(checked)
        self.ram_value_label.setVisible(checked)
    
        # Uncheck GPU and Autodevice radio buttons
        if checked and nvidia_gpu:
            self.gpu_radio_button.setChecked(False)
            self.auto_radio_button.setChecked(False)
        elif checked and not nvidia_gpu:
            self.auto_radio_button.setChecked(False)
    
    def on_auto_radio_button_toggled(self, checked):
        # Hide/show GPU-related widgets
        if nvidia_gpu:
            for slider, label_vram, label_gpu in zip(self.gpu_vram_sliders, self.gpu_vram_labels, self.gpu_labels):
                slider.hide()
                label_vram.hide()
                label_gpu.hide()
    
        # Hide RAM slider and value label
        self.ram_label.hide()
        self.ram_slider.hide()
        self.ram_value_label.hide()
    
        # Uncheck GPU and CPU radio buttons
        if checked and nvidia_gpu:
            self.gpu_radio_button.setChecked(False)
            self.cpu_radio_button.setChecked(False)
        elif checked and not nvidia_gpu:
            self.cpu_radio_button.setChecked(False)

    def on_listen_port_checkbox_changed(self, state):
        self.listen_port_textfield.setEnabled(state == Qt.Checked)

    def on_authentication_checkbox_changed(self, state):
        self.choose_file_label.setVisible(state == Qt.Checked)
        self.choose_file_button.setVisible(state == Qt.Checked)

    def on_choose_file_button_clicked(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setWindowTitle("Choose Authentication File")
        file_dialog.setNameFilter("All Files (*)")
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                self.choose_file_label.setText(file_path)

    def on_save_button_clicked(self):
        settings = {
            "model": self.model_dropdown.currentText(), # Saves the Current selected Model
            "model_type": self.model_type.currentText(), # Saves the Current selected Model Type
            "wbits": self.wbit_dropdown.currentText(), # Saves the WBIT Setting
            "groupsize": self.gsize_dropdown.currentText(), # Saves the Groupsize
            "mode": self.mode_dropdown.currentText(), # Saves the selected interaction mode (Chat,cai_chat,Notebook)
            "use_gpu": self.gpu_radio_button.isChecked(),  # Save the state of the GPU radio button
            "use_cpu": self.cpu_radio_button.isChecked(),  # Save the state of the CPU radio button
            "use_auto": self.auto_radio_button.isChecked(),  # Save the state of the auto device radio button
            "built_in_ram": self.ram_slider.value(),  # Save the value of the built-in RAM slider
            "prelayer": self.pre_layer_value_label.text(), # Saves the Prelayer value
            "use_8bit": self.use_8bit_checkbox.isChecked(), # Saves the state of the 8bit checkbox
            "no_stream": self.use_nostream_checkbox.isChecked(), # Saves the state of the no_stream checkbox
            "use_16bit": self.use_16bit_checkbox.isChecked(), # Saves the state of the use_16bit checkbox
            "use_disk": self.use_disk_checkbox.isChecked(), # Saves the state of the use_disk checkbox
            "disk_cache": self.disk_cache_textfield.text(), # Saves the state of the disk_cache textfield
            "xformers": self.use_xformers_checkbox.isChecked(), # Saves the state of the xformers checkbox
            "trust_remote_code": self.use_trc_checkbox.isChecked(), # Saves the state of the trust_remote_code checkbox
            "monkeypatch": self.use_monkey_checkbox.isChecked(), # Saves the state of the monkeypatch checkbox
            "quant_attn": self.use_quant_checkbox.isChecked(), # Saves the state of the quant_attn checkbox
            "autotune": self.use_autotune_checkbox.isChecked(), # Saves the state of the autotune checkbox
            "autolaunch": self.use_autolaunch_checkbox.isChecked(), # Saves the state of the autotune checkbox
            "autoclose": self.use_autoclose_checkbox.isChecked(), # Saves the state of the autotune checkbox
            "nocache": self.use_nocache_checkbox.isChecked(), # Saves the state of the autotune checkbox
            "listen": self.use_network_checkbox.isChecked(), # Saves the state of the Local Network Checkbox
            "listen_port": self.listen_port_checkbox.isChecked(), # Saves the state of the Listen Port Checkbox
            "port_number": self.listen_port_textfield.text(), # Saves the Port given in the Textbox
            "authentication": self.authentication_checkbox.isChecked(), # Saves the state of the Authentication
            "authentication_file": self.choose_file_label.text(),  # Save the authentication file path
            "gpu_vram": [slider.value() for slider in self.gpu_vram_sliders], # Saves the VRAM Values
            "use_extension": self.use_extensions_checkbox.isChecked(), # Saves the state of the Extension Checkbox
            "extensions": [self.extensions_list.item(i).text() for i in range(self.extensions_list.count()) if self.extensions_list.item(i).checkState() == Qt.Checked], # Saves the chosen Extensions
            "use_lora": self.use_lora_checkbox.isChecked(), # Saves the state of the Lora Checkbox
            "loras": [self.lora_list.item(i).text() for i in range(self.lora_list.count()) if self.lora_list.item(i).checkState() == Qt.Checked] # Saves the chosen loras
        }

        # Get the text entered in the text field
        profile_name = self.profile_name_textfield.text()
        if not profile_name:
            profile_name = "default"
        file_path = os.path.join(profiles_folder, f"{profile_name}.json")
        with open(file_path, "w") as file:
            json.dump(settings, file, indent=4)

    def expression_check(self, command):
        selected_model = self.model_dropdown.currentText()
        #print(f"Selected model: {selected_model}")
        
        # Use a regular expression to check if the selected model matches the pattern
        if re.search(r".*mpt.*7b", selected_model, re.IGNORECASE):
            # Run the additional commands
            run_cmd_with_conda("pip install einops && exit")
        elif re.search(r".*vicuna.*7b", selected_model, re.IGNORECASE):
            pass

    def on_start_button_clicked(self):
        command = ""

        # Add the chosen model to the command
        chosen_model = self.model_dropdown.currentText()
        if self.model_dropdown.currentText() != "none":
            command += f" --model {chosen_model}"

        # Add the chosen model type to the command
        chosen_model_type = self.model_type.currentText()
        if self.model_type.currentText() != "none" and self.model_dropdown.currentText() != "none":
            command += f" --model_type {chosen_model_type}"

        # Add loras to the command
        loras = [self.lora_list.item(i).text() for i in range(self.lora_list.count()) if self.lora_list.item(i).checkState() == Qt.Checked]
        if self.use_lora_checkbox.isChecked() and self.model_dropdown.currentText() != "none":
            if loras:
                command += f" --lora {' '.join(loras)}"

        # Adds wbits to the command, if not "none"
        chosen_wbits = self.wbit_dropdown.currentText()
        if self.wbit_dropdown.currentText() != "none":
            if not self.cpu_radio_button.isChecked() and self.model_dropdown.currentText() != "none":
                command += f" --wbits {chosen_wbits}"

        # Adds Groupsize to the command, if not "none"
        chosen_gsize = self.gsize_dropdown.currentText()
        if self.gsize_dropdown.currentText() != "none":
            if not self.cpu_radio_button.isChecked() and self.model_dropdown.currentText() != "none":
                command += f" --groupsize {chosen_gsize}"

        # Add the chosen mode to the command (Chat, cai-chat, notebook)
        chosen_mode = self.mode_dropdown.currentText()
        command += f" --{chosen_mode}"

        # Handle GPU or CPU selection
        if self.gpu_radio_button.isChecked():
            # GPU radio button is selected
            total_vram = sum(slider.value() for slider in self.gpu_vram_sliders)
            if total_vram == 0:
                error_message = "Error:\nAt least one VRAM value must be greater than 0 for GPU execution."
                self.show_error_message(error_message)
            else:
                command += " --gpu-memory"
                for vram in [slider.value() for slider in self.gpu_vram_sliders]:
                    if vram > 0:
                        command += f" {vram}"
        elif self.cpu_radio_button.isChecked():
            # CPU radio button is selected
            command += " --cpu-memory"
            ram_value = self.ram_slider.value()
            if ram_value > 0:
                command += f" {ram_value}"
            else:
                # Display an error message in a dialog box when RAM value is 0
                error_message = "Error:\nRAM value cannot be 0 for CPU execution."
                self.show_error_message(error_message)
                return
        elif self.auto_radio_button.isChecked():
            command += " --auto-device"

        # Add 8bit loading
        if self.use_8bit_checkbox.isChecked():
            command += " --load-in-8bit"

        # Add no-stream
        if self.use_nostream_checkbox.isChecked():
            command += " --no-stream"

        # Add 16bit full precision loading
        if self.use_16bit_checkbox.isChecked():
            command += " --bf16"

        # Add xformers loading
        if self.use_xformers_checkbox.isChecked():
            command += " --xformers"

        # Use "Trust Remote Code=TRUE" for ex. MPT-7B
        if self.use_trc_checkbox.isChecked():
            command += " --trust-remote-code"
        if re.search(r"mpt.*7b", chosen_model):
            if not self.use_trc_checkbox.isChecked():
                command += " --trust-remote-code"

        # Use Triton Warmup & Autotune
        if self.use_autotune_checkbox.isChecked():
            command += " --warmup_autotune"

        # Add loading with Monkey Patch 
        if self.use_monkey_checkbox.isChecked():
            command += " --monkey-patch"

        # Enable quant attention
        if self.use_quant_checkbox.isChecked():
            command += " --quant_attn"

        # Disable Cache
        if self.use_nocache_checkbox.isChecked():
            command += " --no-cache"

        # Add --auto-launch
        if self.use_autolaunch_checkbox.isChecked():
            command += " --auto-launch"

        # Local Network Mode
        if self.use_network_checkbox.isChecked():
            command += " --listen"

        # Use Disk to store part of the Model
        if self.use_disk_checkbox.isChecked():
            command += " --disk"
            if self.change_disk_cache_checkbox.isChecked():
                if self.disk_cache_textfield.text():
                    command += f" --disk-cache-dir {self.disk_cache_textfield.text()}"

        # Add listen port if the checkbox is checked and a port number is provided
        if self.listen_port_checkbox.isChecked():
            listen_port = self.listen_port_textfield.text()
            if listen_port.isdigit():
                command += f" --listen-port {listen_port}"

        # Adds the authentication to the command, if active
        if self.authentication_checkbox.isChecked():
            if self.choose_file_label.text():
                command += f" --gradio-auth-path {self.choose_file_label.text()}"

        # Adds the Prelayer selection
        if int(self.pre_layer_value_label.text()) > 0:
            command += f" --pre_layer {self.pre_layer_value_label.text()}"

        # Adds the chosen extensions to the list of the command.
        extensions = [self.extensions_list.item(i).text() for i in range(self.extensions_list.count()) if self.extensions_list.item(i).checkState() == Qt.Checked]
        if self.use_extensions_checkbox.isChecked():
            if extensions:
                command += f" --extensions {' '.join(extensions)}"

        # Just for debugging.
        #print(f"Command generated: python webuiGUI.py {command}")

        # Based on the Model that's chosen, we will take care of some necessary stuff.
        # Starts the webui in the conda env with the user given Options
        run_cmd_with_conda(f"python webuiGUI.py {command}")

        if self.use_autoclose_checkbox.isChecked():
            sys.exit()
            
    def on_update_button_clicked(self):
        run_cmd_with_conda("python webuiGUI.py --update && exit")

    def load_profile(self, profile_file):
        with open(profile_file, "r") as file:
            try:
                settings = json.load(file)
                # Set the GUI elements based on the loaded settings...
            except json.JSONDecodeError:
                # Handle the case when the file is empty or not in valid JSON format
                pass
    
    def populate_profiles_dropdown(self):
        self.profiles_dropdown.clear()
        profiles = [name for name in os.listdir(profiles_folder) if name.endswith(".json")]
        self.profiles_dropdown.addItems(profiles)
    
    def on_load_button_clicked(self):
        selected_profile = self.profiles_dropdown.currentText()
        profile_file = os.path.join(profiles_folder, selected_profile)
        self.load_profile(profile_file)
    
        # Populate the profile name text field with the loaded profile name
        profile_name = selected_profile.replace(".json", "")
        self.profile_name_textfield.setText(profile_name)

    def apply_load_settings(self, settings):
        self.model_dropdown.setCurrentText(settings.get("model", ""))
        self.model_type.setCurrentText(settings.get("model_type", ""))
        self.wbit_dropdown.setCurrentText(settings.get("wbits", ""))
        self.gsize_dropdown.setCurrentText(settings.get("groupsize", ""))
        self.mode_dropdown.setCurrentText(settings.get("mode", ""))
        use_gpu = settings.get("use_gpu", False)
        use_cpu = settings.get("use_cpu", False)
        self.gpu_radio_button.setChecked(use_gpu)
        self.cpu_radio_button.setChecked(use_cpu)
        built_in_ram = settings.get("built_in_ram", 0)
        self.ram_slider.setValue(built_in_ram)
        self.listen_port_checkbox.setChecked(settings.get("listen_port", False))
        self.listen_port_textfield.setText(settings.get("port_number", ""))
        self.use_8bit_checkbox.setChecked(settings.get("use_8bit", False))
        self.use_nostream_checkbox.setChecked(settings.get("no_stream", False))
        self.use_16bit_checkbox.setChecked(settings.get("use_16bit", False))
        self.use_disk_checkbox.setChecked(settings.get("use_disk", False))
        self.disk_cache_textfield.setText(settings.get("disk_cache", ""))
        self.current_disk_cache_label.setText(f"Current folder: {settings.get('disk_cache', '')}")
        self.use_xformers_checkbox.setChecked(settings.get("xformers", False))
        self.use_trc_checkbox.setChecked(settings.get("trust_remote_code", False))
        self.use_monkey_checkbox.setChecked(settings.get("monkeypatch", False))
        self.use_quant_checkbox.setChecked(settings.get("quant_attn", False))
        self.use_autotune_checkbox.setChecked(settings.get("autotune", False))
        self.use_autolaunch_checkbox.setChecked(settings.get("autolaunch", False))
        self.use_autoclose_checkbox.setChecked(settings.get("autoclose", False))
        self.use_nocache_checkbox.setChecked(settings.get("nocache", False))
        self.authentication_checkbox.setChecked(settings.get("authentication", False))
        self.choose_file_label.setText(settings.get("authentication_file", ""))
        self.pre_layer_slider.setValue(int(settings.get("prelayer", 0)))
        self.use_autolaunch_checkbox.setChecked(settings.get("autolaunch", False))
        self.use_network_checkbox.setChecked(settings.get("listen", False))
        gpu_vram_settings = settings.get("gpu_vram", [])
        for idx, slider in enumerate(self.gpu_vram_sliders):
            if idx < len(gpu_vram_settings):
                slider.setValue(gpu_vram_settings[idx])
        self.use_extensions_checkbox.setChecked(settings.get("use_extension", False))
        extensions_settings = settings.get("extensions", [])
        for i in range(self.extensions_list.count()):
            extension = self.extensions_list.item(i).text()
            if extension in extensions_settings:
                self.extensions_list.item(i).setCheckState(Qt.Checked)
            else:
                self.extensions_list.item(i).setCheckState(Qt.Unchecked)
        self.use_lora_checkbox.setChecked(settings.get("use_lora", False))
        lora_settings = settings.get("loras", [])
        for i in range(self.lora_list.count()):
            lora = self.lora_list.item(i).text()
            if lora in lora_settings:
                self.lora_list.item(i).setCheckState(Qt.Checked)
            else:
                self.lora_list.item(i).setCheckState(Qt.Unchecked)


    def load_settings(self):
        default_profile = os.path.join(profiles_folder, "default.json")
        if os.path.exists(default_profile):
            with open(default_profile, "r") as file:
                try:
                    settings = json.load(file)
                    self.apply_load_settings(settings)                
                except json.JSONDecodeError:
                    # Handle the case when the file is empty or not in valid JSON format
                    pass

    def load_profile(self, profile_file):
        with open(profile_file, "r") as file:
            try:
                settings = json.load(file)
                self.apply_load_settings(settings)
            except json.JSONDecodeError:
                # Handle the case when the file is empty or not in valid JSON format
                pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    if darkdetect.isDark():
        dark_stylesheet = qdarkstyle.load_stylesheet_pyqt5()
        app.setStyleSheet(dark_stylesheet)
    sys.exit(app.exec_())
