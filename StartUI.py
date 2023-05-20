import sys, os, gpustat, json, subprocess, platform, psutil, re, requests, darkdetect, qdarkstyle
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QToolBar, QMessageBox, QAction, QMainWindow, QSpinBox, QLabel, QVBoxLayout, QComboBox, QSlider, QCheckBox, QLineEdit, QFileDialog, QPushButton, QWidget, QListWidget, QListWidgetItem, QGridLayout, QRadioButton, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator

version = "1.5b"

profiles_folder = "./profiles"
os.makedirs(profiles_folder, exist_ok=True)
model_folder = "./text-generation-webui/models"
extensions_folder = "./text-generation-webui/extensions"
loras_folder = "./text-generation-webui/loras"
characters_folder = "./text-generation-webui/characters"
max_threads = psutil.cpu_count(logical=True)
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
        # ToolBar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Toolbar Label
        toolbar_label = QLabel("Show Advanced Settings:")
        toolbar.addWidget(toolbar_label)

        # Deepspeed checkbox
        self.deepspeed_settings_checkbox = QCheckBox("   DeepSpeed   ")
        self.deepspeed_settings_checkbox.setChecked(False)
        self.deepspeed_settings_checkbox.setToolTip("Enables Deepspeed Settings")
        self.deepspeed_settings_checkbox.stateChanged.connect(self.on_deepspeed_settings_checkbox_stateChanged)
        toolbar.addWidget(self.deepspeed_settings_checkbox)

        # llama.cpp checkbox
        self.llama_settings_checkbox = QCheckBox("   llama.cpp   ")
        self.llama_settings_checkbox.setChecked(False)
        self.llama_settings_checkbox.setToolTip("Enables llama.cpp Settings")
        self.llama_settings_checkbox.stateChanged.connect(self.on_llama_settings_checkbox_stateChanged)
        toolbar.addWidget(self.llama_settings_checkbox)

        # FlexGen Checkbox
        self.flexgen_settings_checkbox = QCheckBox("   FlexGen   ")
        self.flexgen_settings_checkbox.setChecked(False)
        self.flexgen_settings_checkbox.setToolTip("Enables FlexGen Settings")
        self.flexgen_settings_checkbox.stateChanged.connect(self.on_flexgen_settings_checkbox_stateChanged)
        toolbar.addWidget(self.flexgen_settings_checkbox)

        # RWKV Checkbox
        self.rwkv_settings_checkbox = QCheckBox("   RWKV   ")
        self.rwkv_settings_checkbox.setChecked(False)
        self.rwkv_settings_checkbox.setVisible(False)
        self.rwkv_settings_checkbox.setToolTip("Enables RWKV Settings")
        self.rwkv_settings_checkbox.stateChanged.connect(self.on_rwkv_settings_checkbox_stateChanged)
        toolbar.addWidget(self.rwkv_settings_checkbox)

        # API Checkbox
        self.api_settings_checkbox = QCheckBox("   API   ")
        self.api_settings_checkbox.setChecked(False)
        self.api_settings_checkbox.setToolTip("Enables API Settings")
        self.api_settings_checkbox.stateChanged.connect(self.on_api_settings_checkbox_stateChanged)
        toolbar.addWidget(self.api_settings_checkbox)

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
        model_box = QHBoxLayout()
        model_folders = [name for name in os.listdir(model_folder) if os.path.isdir(os.path.join(model_folder, name))]
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItem("none")
        self.model_dropdown.addItems(model_folders)
        self.model_dropdown.setToolTip("Select your prefered Model")
        model_box.addWidget(QLabel("Choose Model:"))
        model_box.addWidget(self.model_dropdown)
        layout.addLayout(model_box, 0, 0)

        # Reload Model Button
        self.reload_model_button = QPushButton("Reload the Model List")
        self.reload_model_button.setToolTip("Reloads the Names in the Models Folder")
        self.reload_model_button.clicked.connect(self.reload_models)
        layout.addWidget(self.reload_model_button, 0, 1, 1, 2)

        # Model Type
        model_type_box = QHBoxLayout()

        # Model Type Label
        self.model_type_text = QLabel("Model Type:")
        model_type_box.addWidget(self.model_type_text)

        # Model Type Dropdown
        self.model_type = QComboBox()
        self.model_type.addItems(["none", "llama", "opt", "gptj"])
        self.model_type.setToolTip("Select the Model Type")
        model_type_box.addWidget(self.model_type)
        layout.addLayout(model_type_box, 1, 0)


        # Character
        character_box = QHBoxLayout()

        # Character Text
        self.character_text = QLabel("Character:")
        character_box.addWidget(self.character_text)

        # Character Dropdown
        self.character_to_load = QComboBox()
        character_jsons = [file for file in os.listdir(characters_folder) if file.endswith(".json")]
        without_suffix = [file.replace(".json", "") for file in character_jsons]
        self.character_to_load.addItem("none")
        self.character_to_load.addItems(without_suffix)
        self.character_to_load.setToolTip("Select the Character you want to load")
        character_box.addWidget(self.character_to_load)
        layout.addLayout(character_box, 1, 1, 1, 2)

        # WBIT Box
        wbit_box = QHBoxLayout()

        # WBIT Label
        self.wbit_text = QLabel("Choose WBITs:")
        wbit_box.addWidget(self.wbit_text)

        # WBIT Dropdown Menu
        self.wbit_dropdown = QComboBox()
        self.wbit_dropdown.addItems(["none", "1", "2", "3", "4","8"])
        self.wbit_dropdown.setToolTip("Select the bits quantization for this model\nExample: vicuna 7b 4bit you should choose 4.\nYou can keep it at none, the webui will determine it automatically if the wbits are mentioned in the name of the model")
        wbit_box.addWidget(self.wbit_dropdown)
        layout.addLayout(wbit_box, 2, 0)

        # Groupsize box
        groupsize_box = QHBoxLayout()

        # Groupsize Label
        self.groupsize_text = QLabel("Choose Groupsize:")
        groupsize_box.addWidget(self.groupsize_text)

        # Groupsize Dropdown Menu
        self.gsize_dropdown = QComboBox()
        self.gsize_dropdown.addItems(["none", "32", "64", "128", "1024"])
        self.gsize_dropdown.setToolTip("Select the groupsize used by the Model.\nExample: vicuna 7b 4bit-128g you should choose 128.\nYou can keep it at none, the webui will determine it automatically if the groupsize is mentioned in the name of the model")
        groupsize_box.addWidget(self.gsize_dropdown)
        layout.addLayout(groupsize_box, 2, 1, 1, 2)

        # Interface Mode Box
        interface_mode_box = QHBoxLayout()

        # Interface mode label
        self.interface_mode_text = QLabel("Interface Mode:")
        interface_mode_box.addWidget(self.interface_mode_text)

        # Interface Mode Dropdown
        self.mode_dropdown = QComboBox()
        self.mode_dropdown.addItems(["chat", "cai_chat", "notebook"])
        self.mode_dropdown.setToolTip("Choose what kind of Interface you want to load.")
        interface_mode_box.addWidget(self.mode_dropdown)
        layout.addLayout(interface_mode_box, 3, 0)

        # WebUI Update
        self.update_button = QPushButton("Update the text-generation-webui")
        self.update_button.setToolTip("Starts the Update Routine for the text-generation-webui")
        self.update_button.clicked.connect(self.on_update_button_clicked)
        layout.addWidget(self.update_button, 3, 1, 1, 2)

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

        # Use sdp_attention
        self.use_sdp_attention_checkbox = QCheckBox("Use sdp-attention")
        self.use_sdp_attention_checkbox.setToolTip("Use torch 2.0's sdp attention.")
        layout.addWidget(self.use_sdp_attention_checkbox, 20 + len(gpu_stats), 0)

        # Use Multimodal Checkbox
        self.use_multimodal_checkbox = QCheckBox("Multimodal")
        self.use_multimodal_checkbox.setToolTip("Use multimodal models.")
        layout.addWidget(self.use_multimodal_checkbox, 20 + len(gpu_stats), 1)

        # Add autogptq checkbox
        self.use_autogptq_checkbox = QCheckBox("AutoGPTQ")
        self.use_autogptq_checkbox.setToolTip("Use AutoGPTQ for loading quantized models instead of the internal GPTQ loader.")
        layout.addWidget(self.use_autogptq_checkbox, 21 + len(gpu_stats), 0)

        # Add Triton checkbox
        self.use_triton_checkbox = QCheckBox("Triton")
        self.use_triton_checkbox.setToolTip("Use Triton for inference.")
        layout.addWidget(self.use_triton_checkbox, 21 + len(gpu_stats), 1)

        # Add horizontal line to seperate the Checkboxes
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line, 22 + len(gpu_stats), 0, 1, 3)

        # New GUI Options based on Toolbox Checkboxes.

        # Deepspeed

        # Deepspeed Header
        self.deepspeed_label_header = QLabel("Deepspeed Options:")
        self.deepspeed_label_header.setToolTip("Deepspeed Options")
        layout.addWidget(self.deepspeed_label_header, 30 + len(gpu_stats), 0)
        self.deepspeed_label_header.setVisible(False)

        # Deepspeed Checkbox
        self.deepspeed_checkbox = QCheckBox("Use Deepspeed")
        self.deepspeed_checkbox.setToolTip("Enable the use of DeepSpeed ZeRO-3 for inference via the Transformers integration.")
        layout.addWidget(self.deepspeed_checkbox, 31 + len(gpu_stats), 0)
        self.deepspeed_checkbox.setVisible(False)

        # Deepspeed Box
        deepspeed_box = QHBoxLayout()

        # Deepspeed GPU num Label
        self.deepspeed_gpu_num_label = QLabel("Deepspeed GPU num:")
        self.deepspeed_gpu_num_label.setVisible(False)
        self.deepspeed_gpu_num_label.setToolTip("The number of GPUs to use for DeepSpeed ZeRO-3.")
        deepspeed_box.addWidget(self.deepspeed_gpu_num_label)

        # Deepspeed GPU num Spinbox
        self.deepspeed_gpu_num_spinbox = QSpinBox()
        self.deepspeed_gpu_num_spinbox.setVisible(False)
        self.deepspeed_gpu_num_spinbox.setToolTip("The number of GPUs to use for DeepSpeed ZeRO-3.")
        self.deepspeed_gpu_num_spinbox.setMinimum(1)
        self.deepspeed_gpu_num_spinbox.setMaximum(16)
        deepspeed_box.addWidget(self.deepspeed_gpu_num_spinbox)
        layout.addLayout(deepspeed_box, 31 + len(gpu_stats), 1, 1, 2)

        # Deepspeed use NVMe Offload Directory Checkbox
        self.deepspeed_nvme_checkbox = QCheckBox("Use Offload Directory")
        self.deepspeed_nvme_checkbox.setVisible(False)
        self.deepspeed_nvme_checkbox.setToolTip("Use an NVMe offload directory for ZeRO-3.")
        layout.addWidget(self.deepspeed_nvme_checkbox, 32 + len(gpu_stats), 0)
        self.deepspeed_nvme_checkbox.stateChanged.connect(self.on_deepspeed_nvme_checkbox_changed)

        # NVMe offload Directory
        self.deepspeed_nvme_label = QLabel("NVMe Offload Directory:")
        self.deepspeed_nvme_label.setVisible(False)
        self.deepspeed_nvme_label.setToolTip("Directory to use for ZeRO-3 NVME offloading.")
        layout.addWidget(self.deepspeed_nvme_label, 33 + len(gpu_stats), 0)

        # NVMe Current Offload Directory
        self.selected_offload_directory = "none"
        self.deepspeed_nvme_current_label = QLabel(f"Current Directory: {self.selected_offload_directory}")
        self.deepspeed_nvme_current_label.setVisible(False)
        self.deepspeed_nvme_current_label.setToolTip("The current NVMe offload directory.")
        layout.addWidget(self.deepspeed_nvme_current_label, 33 + len(gpu_stats), 1)

        # NVMe Offload Directory folder choose
        self.deepspeed_nvme_button = QPushButton("Choose Folder")
        self.deepspeed_nvme_button.setVisible(False)
        self.deepspeed_nvme_button.setToolTip("Choose a folder to use for the NVMe offload.")
        self.deepspeed_nvme_button.clicked.connect(self.on_deepspeed_nvme_button_clicked)
        layout.addWidget(self.deepspeed_nvme_button, 34 + len(gpu_stats), 1)

        # Local Rank
        self.deepspeed_local_rank_label = QLabel("Local Rank:")
        self.deepspeed_local_rank_label.setVisible(False)
        self.deepspeed_local_rank_label.setToolTip("Optional argument for distributed setups.")
        layout.addWidget(self.deepspeed_local_rank_label, 35 + len(gpu_stats), 0)

        # Local Rank SpinBox
        self.deepspeed_local_rank_spinbox = QSpinBox()
        self.deepspeed_local_rank_spinbox.setVisible(False)
        self.deepspeed_local_rank_spinbox.setToolTip("Optional argument for distributed setups.")
        self.deepspeed_local_rank_spinbox.setMinimum(0)
        layout.addWidget(self.deepspeed_local_rank_spinbox, 35 + len(gpu_stats), 1)

        # Add horizontal line to seperate the Checkboxes
        self.deepspeed_line = QFrame()
        self.deepspeed_line.setFrameShape(QFrame.HLine)
        self.deepspeed_line.setFrameShadow(QFrame.Sunken)
        self.deepspeed_line.setVisible(False)
        layout.addWidget(self.deepspeed_line, 36 + len(gpu_stats), 0, 1, 3)

        # llama.cpp

        # llama.cpp Header
        self.llama_label_header = QLabel("llama.cpp Options:")
        self.llama_label_header.setToolTip("llama.cpp Options")
        layout.addWidget(self.llama_label_header, 40 + len(gpu_stats), 0)
        self.llama_label_header.setVisible(False)

        # llama.cpp threads box
        llama_threads_box = QHBoxLayout()

        # llama.cpp threads
        self.llama_threads_label = QLabel("Threads:")
        self.llama_threads_label.setVisible(False)
        self.llama_threads_label.setToolTip("Number of threads to use for llama.cpp.")
        llama_threads_box.addWidget(self.llama_threads_label)

        # llama.cpp threads number
        self.llama_threads_spinbox = QSpinBox()
        self.llama_threads_spinbox.setToolTip("Number of threads to use for llama.cpp.")
        self.llama_threads_spinbox.setRange(0, max_threads)
        self.llama_threads_spinbox.setValue(0)  # Set an initial value
        self.llama_threads_spinbox.setVisible(False)
        llama_threads_box.addWidget(self.llama_threads_spinbox)
        layout.addLayout(llama_threads_box, 42 + len(gpu_stats), 0)

        # llama.cpp batch size box
        llama_batch_size_box = QHBoxLayout()

        # llama.cpp batch size
        self.llama_batch_size_label = QLabel("Batch Size:")
        self.llama_batch_size_label.setVisible(False)
        self.llama_batch_size_label.setToolTip("Maximum number of prompt tokens to batch together when calling llama_eval.")
        llama_batch_size_box.addWidget(self.llama_batch_size_label)

        # llama.cpp batch size number
        self.llama_batch_size_spinbox = QSpinBox()
        self.llama_batch_size_spinbox.setToolTip("Maximum number of prompt tokens to batch together when calling llama_eval.")
        self.llama_batch_size_spinbox.setRange(4, 8192)
        self.llama_batch_size_spinbox.setValue(512)
        self.llama_batch_size_spinbox.setSingleStep(4)
        self.llama_batch_size_spinbox.setVisible(False)
        llama_batch_size_box.addWidget(self.llama_batch_size_spinbox)
        layout.addLayout(llama_batch_size_box, 42 + len(gpu_stats), 1, 1, 2)

        # llama.cpp mmap checkbox
        self.llama_mmap_checkbox = QCheckBox("Use no mmap")
        self.llama_mmap_checkbox.setToolTip("Prevent mmap from being used.")
        layout.addWidget(self.llama_mmap_checkbox, 44 + len(gpu_stats), 0)
        self.llama_mmap_checkbox.setVisible(False)

        # llama mlock checkbox
        self.llama_mlock_checkbox = QCheckBox("Use mlock")
        self.llama_mlock_checkbox.setToolTip("Force the system to keep the model in RAM.")
        layout.addWidget(self.llama_mlock_checkbox, 44 + len(gpu_stats), 1)
        self.llama_mlock_checkbox.setVisible(False)

        # llama.cpp cache capacity box
        llama_cache_capacity_box = QHBoxLayout()

        # llama Cache Capacity Spinbox
        self.llama_cache_capacity_label = QLabel("Cache Capacity:")
        self.llama_cache_capacity_label.setVisible(False)
        self.llama_cache_capacity_label.setToolTip("Maximum number of prompt tokens to cache in RAM.")
        llama_cache_capacity_box.addWidget(self.llama_cache_capacity_label)

        # llama Cache Capacity Spinbox
        self.llama_cache_capacity_spinbox = QSpinBox()
        self.llama_cache_capacity_spinbox.setToolTip("Maximum number of prompt tokens to cache in RAM.")
        self.llama_cache_capacity_spinbox.setRange(0, 8192)
        self.llama_cache_capacity_spinbox.setValue(1024)
        self.llama_cache_capacity_spinbox.setSingleStep(4)
        self.llama_cache_capacity_spinbox.setVisible(False)
        llama_cache_capacity_box.addWidget(self.llama_cache_capacity_spinbox)

        # llama.cpp Cache Capacity Units
        self.llama_cache_capacity_units = QComboBox()
        self.llama_cache_capacity_units.setToolTip("Choose the Units to use")
        self.llama_cache_capacity_units.addItems(["MiB", "GiB"])
        self.llama_cache_capacity_units.setVisible(False)
        llama_cache_capacity_box.addWidget(self.llama_cache_capacity_units)
        layout.addLayout(llama_cache_capacity_box, 45 + len(gpu_stats), 0)

        # GPU Layer Box
        self.llama_gpu_layer_box = QHBoxLayout()

        # llama GPU Layer Label
        self.llama_gpu_layer_label = QLabel("GPU Layer:")
        self.llama_gpu_layer_label.setVisible(False)
        self.llama_gpu_layer_label.setToolTip("Number of layers to offload to the GPU.")
        self.llama_gpu_layer_box.addWidget(self.llama_gpu_layer_label)

        # llama GPU Layer Number
        self.llama_gpu_layer_spinbox = QSpinBox()
        self.llama_gpu_layer_spinbox.setToolTip("Number of layers to offload to the GPU.\nTo Offload all to GPU set it to 200.000 (MAX)")
        self.llama_gpu_layer_spinbox.setRange(0, 200000)
        self.llama_gpu_layer_spinbox.setValue(0)
        self.llama_gpu_layer_spinbox.setSingleStep(1)
        self.llama_gpu_layer_spinbox.setVisible(False)
        self.llama_gpu_layer_box.addWidget(self.llama_gpu_layer_spinbox)
        layout.addLayout(self.llama_gpu_layer_box, 45 + len(gpu_stats), 1, 1, 2)

        # Seperator for the Toolbox Options
        self.llama_line = QFrame()
        self.llama_line.setFrameShape(QFrame.HLine)
        self.llama_line.setFrameShadow(QFrame.Sunken)
        self.llama_line.setVisible(False)
        layout.addWidget(self.llama_line, 46 + len(gpu_stats), 0, 1, 3)

        # FlexGen Options

        # FlexGen Header Label
        self.flexgen_header_label = QLabel("FlexGen Options")
        self.flexgen_header_label.setVisible(False)
        self.flexgen_header_label.setToolTip("Options for FlexGen.")
        layout.addWidget(self.flexgen_header_label, 50 + len(gpu_stats), 0)

        # FlexGen Checkbox 
        self.flexgen_checkbox = QCheckBox("Use FlexGen")
        self.flexgen_checkbox.setToolTip("Enable the use of FlexGen offloading.")
        self.flexgen_checkbox.setVisible(False)
        layout.addWidget(self.flexgen_checkbox, 50 + len(gpu_stats), 0)
        #self.flexgen_checkbox.stateChanged.connect(self.on_flexgen_checkbox_changed)

        # FlexGen Percentage
        inner_layout = QHBoxLayout()
        self.flexgen_percentage_label = QLabel("FlexGen Percentage:")
        #self.flexgen_percentage_label.setVisible(False)
        self.flexgen_percentage_label.setToolTip("FlexGen: allocation percentages. Must be 6 numbers separated by spaces (default: 0, 100, 100, 0, 100, 0).\n\nthe percentage of weight on GPU\nthe percentage of weight on CPU\nthe percentage of attention cache on GPU\nthe percentage of attention cache on CPU\nthe percentage of activations on GPU\nthe percentage of activations on CPU")
        self.flexgen_percentage_label.setVisible(False)
        inner_layout.addWidget(self.flexgen_percentage_label)
        
        # FlexGen Percentage Spinbox 1
        self.flexgen_percentage_spinbox1 = QSpinBox()
        self.flexgen_percentage_spinbox1.setToolTip("Allocation percentages. Default: 0\nthe percentage of weight on GPU")
        self.flexgen_percentage_spinbox1.setRange(0, 100)
        self.flexgen_percentage_spinbox1.setValue(0)
        self.flexgen_percentage_spinbox1.setVisible(False)
        inner_layout.addWidget(self.flexgen_percentage_spinbox1)

        # FlexGen Percentage Spinbox 2
        self.flexgen_percentage_spinbox2 = QSpinBox()
        self.flexgen_percentage_spinbox2.setToolTip("Allocation percentages. Default: 100.\nthe percentage of weight on CPU")
        self.flexgen_percentage_spinbox2.setRange(0, 100)
        self.flexgen_percentage_spinbox2.setValue(100)
        self.flexgen_percentage_spinbox2.setVisible(False)
        inner_layout.addWidget(self.flexgen_percentage_spinbox2)

        # FlexGen Percentage Spinbox 3
        self.flexgen_percentage_spinbox3 = QSpinBox()
        self.flexgen_percentage_spinbox3.setToolTip("Allocation percentages. Default: 100.\nthe percentage of attention cache on GPU")
        self.flexgen_percentage_spinbox3.setRange(0, 100)
        self.flexgen_percentage_spinbox3.setValue(100)
        self.flexgen_percentage_spinbox3.setVisible(False)
        inner_layout.addWidget(self.flexgen_percentage_spinbox3)

        # FlexGen Percentage Spinbox 4
        self.flexgen_percentage_spinbox4 = QSpinBox()
        self.flexgen_percentage_spinbox4.setToolTip("Allocation percentages. Default: 0.\nthe percentage of attention cache on CPU")
        self.flexgen_percentage_spinbox4.setRange(0, 100)
        self.flexgen_percentage_spinbox4.setValue(0)
        self.flexgen_percentage_spinbox4.setVisible(False)
        inner_layout.addWidget(self.flexgen_percentage_spinbox4)

        # FlexGen Percentage Spinbox 5
        self.flexgen_percentage_spinbox5 = QSpinBox()
        self.flexgen_percentage_spinbox5.setToolTip("Allocation percentages. Default: 100.\nthe percentage of activations on GPU")
        self.flexgen_percentage_spinbox5.setRange(0, 100)
        self.flexgen_percentage_spinbox5.setValue(100)
        self.flexgen_percentage_spinbox5.setVisible(False)
        inner_layout.addWidget(self.flexgen_percentage_spinbox5)

        # FlexGen Percentage Spinbox 6
        self.flexgen_percentage_spinbox6 = QSpinBox()
        self.flexgen_percentage_spinbox6.setToolTip("Allocation percentages. Default: 0.\nthe percentage of activations on CPU")
        self.flexgen_percentage_spinbox6.setRange(0, 100)
        self.flexgen_percentage_spinbox6.setValue(0)
        self.flexgen_percentage_spinbox6.setVisible(False)
        inner_layout.addWidget(self.flexgen_percentage_spinbox6)
        layout.addLayout(inner_layout, 51 + len(gpu_stats), 0, 1, 3)

        # FlexGen compression Checkbox
        self.flexgen_compression_checkbox = QCheckBox("Use Compression")
        self.flexgen_compression_checkbox.setToolTip("Enable the use of compression for FlexGen.")
        self.flexgen_compression_checkbox.setVisible(False)
        #self.flexgen_compression_checkbox.stateChanged.connect(self.on_flexgen_compression_checkbox_changed)
        layout.addWidget(self.flexgen_compression_checkbox, 52 + len(gpu_stats), 0)

        # FlexGen pin weight QLabel
        self.flexgen_pin_weight_label = QLabel("FlexGen pin weight:")
        self.flexgen_pin_weight_label.setVisible(False)
        self.flexgen_pin_weight_label.setToolTip("Pin weight for FlexGen. Default: 0.")
        layout.addWidget(self.flexgen_pin_weight_label, 53 + len(gpu_stats), 0)

        # FlexGen pin weight dropdown
        self.flexgen_pin_weight_dropdown = QComboBox()
        self.flexgen_pin_weight_dropdown.setToolTip("Pin weight for FlexGen. Default: 0.")
        self.flexgen_pin_weight_dropdown.setVisible(False)
        self.flexgen_pin_weight_dropdown.addItems(["none", "True", "False"])
        self.flexgen_pin_weight_dropdown.setCurrentIndex(0)
        layout.addWidget(self.flexgen_pin_weight_dropdown, 53 + len(gpu_stats), 1)

        # Seperator for the Toolbox Options
        self.flexline = QFrame()
        self.flexline.setFrameShape(QFrame.HLine)
        self.flexline.setFrameShadow(QFrame.Sunken)
        self.flexline.setVisible(False)
        layout.addWidget(self.flexline, 54 + len(gpu_stats), 0, 1, 3)

        # RWKV Options

        # RWKV Header
        self.rwkv_header = QLabel("RWKV:")
        self.rwkv_header.setVisible(False)
        self.rwkv_header.setToolTip("RWKV: allocation percentages. Must be 6 numbers separated by spaces (default: 0, 100, 100, 0, 100, 0).")
        layout.addWidget(self.rwkv_header, 60 + len(gpu_stats), 0)

        # RWKV Checkbox
        self.rwkv_checkbox = QCheckBox("Enable RWKV")
        self.rwkv_checkbox.setToolTip("Enable RWKV.")
        self.rwkv_checkbox.setVisible(False)
        layout.addWidget(self.rwkv_checkbox, 61 + len(gpu_stats), 0)
        #self.rwkv_checkbox.stateChanged.connect(self.on_rwkv_checkbox_changed)

        # RWKV Strategy Checkbox
        self.rwkv_strategy_checkbox = QCheckBox("Enable RWKV Strategy")
        self.rwkv_strategy_checkbox.setToolTip("Enable RWKV Strategy.")
        self.rwkv_strategy_checkbox.setVisible(False)
        layout.addWidget(self.rwkv_strategy_checkbox, 62 + len(gpu_stats), 0)
        #self.rwkv_strategy_checkbox.stateChanged.connect(self.on_rwkv_strategy_checkbox_changed)

        # RWKV Strategy dropdown
        rwkv_horizontalbox = QHBoxLayout()

        # Dropdown for the Strategy Modes
        self.rwkv_strategy_dropdown = QComboBox()
        self.rwkv_strategy_dropdown.setToolTip("If you want to use a specific RWKV Strategy, you can choose here to enter which mode and the strategy strength\"cpu fp32\" # CPU mode\n\"cuda fp16\" # GPU mode with float16 precision\n\"cuda fp16 *30 -> cpu fp32\" # GPU+CPU offloading. The higher the number after *, the higher the GPU allocation.\n\"cuda fp16i8\" # GPU mode with 8-bit precision")
        self.rwkv_strategy_dropdown.setVisible(False)
        self.rwkv_strategy_dropdown.addItems(["none", "cpu fp32", "cuda fp16", "cuda fp16i8"])
        self.rwkv_strategy_dropdown.setCurrentIndex(0)
        rwkv_horizontalbox.addWidget(self.rwkv_strategy_dropdown)

        # RWKV Allocation Spinbox
        self.rwkv_allocation_spinbox = QSpinBox()
        self.rwkv_allocation_spinbox.setToolTip("If you want to use a specific RWKV Strategy, you can choose here to enter which mode and the strategy strength\"cpu fp32\" # CPU mode\n\"cuda fp16\" # GPU mode with float16 precision\n\"cuda fp16 *30 -> cpu fp32\" # GPU+CPU offloading. The higher the number after *, the higher the GPU allocation.\n\"cuda fp16i8\" # GPU mode with 8-bit precision")
        self.rwkv_allocation_spinbox.setVisible(False)
        self.rwkv_allocation_spinbox.setRange(0, 100)
        self.rwkv_allocation_spinbox.setValue(0)
        rwkv_horizontalbox.addWidget(self.rwkv_allocation_spinbox)
        layout.addLayout(rwkv_horizontalbox, 62 + len(gpu_stats), 1, 1 ,2)

        # RWKV Cuda Checkbox
        self.rwkv_cuda_checkbox = QCheckBox("Enable RWKV Cuda")
        self.rwkv_cuda_checkbox.setToolTip("Enable RWKV Cuda.")
        self.rwkv_cuda_checkbox.setVisible(False)
        layout.addWidget(self.rwkv_cuda_checkbox, 64 + len(gpu_stats), 0)

        # Seperator for the RWKV
        self.rwkv_line = QFrame()
        self.rwkv_line.setFrameShape(QFrame.HLine)
        self.rwkv_line.setFrameShadow(QFrame.Sunken)
        self.rwkv_line.setVisible(False)
        layout.addWidget(self.rwkv_line, 65 + len(gpu_stats), 0, 1, 3)

        # API Options

        # API Header Label
        self.api_header = QLabel("API:")
        self.api_header.setVisible(False)
        self.api_header.setToolTip("API: Choose the API settings to use.")
        layout.addWidget(self.api_header, 70 + len(gpu_stats), 0)

        # API Checkbox
        self.api_checkbox = QCheckBox("Enable API")
        self.api_checkbox.setToolTip("Enable the API extension.")
        self.api_checkbox.setVisible(False)
        layout.addWidget(self.api_checkbox, 71 + len(gpu_stats), 0)
        #self.api_checkbox.stateChanged.connect(self.on_api_checkbox_changed)

        # API blocking Port Checkbox
        self.api_blocking_port_checkbox = QCheckBox("Change API Blocking Port")
        self.api_blocking_port_checkbox.setToolTip("The listening port for the blocking API.\nDefault: 5000")
        self.api_blocking_port_checkbox.setVisible(False)
        layout.addWidget(self.api_blocking_port_checkbox, 72 + len(gpu_stats), 0)
        self.api_blocking_port_checkbox.stateChanged.connect(self.on_api_blocking_port_checkbox_changed)

        # API Blocking Port Spinbox
        self.api_blocking_port_SpinBox = QSpinBox()
        self.api_blocking_port_SpinBox.setToolTip("The listening port for the blocking API.\nDefault: 5000")
        self.api_blocking_port_SpinBox.setVisible(False)
        self.api_blocking_port_SpinBox.setEnabled(False)
        self.api_blocking_port_SpinBox.setRange(0, 65535)
        self.api_blocking_port_SpinBox.setValue(5000)
        layout.addWidget(self.api_blocking_port_SpinBox, 72 + len(gpu_stats), 1)

        # API Streaming Port Checkbox
        self.api_streaming_port_checkbox = QCheckBox("Change API Streaming Port")
        self.api_streaming_port_checkbox.setToolTip("The listening port for the streaming API.\nDefault: 5005")
        self.api_streaming_port_checkbox.setVisible(False)
        layout.addWidget(self.api_streaming_port_checkbox, 73 + len(gpu_stats), 0)
        self.api_streaming_port_checkbox.stateChanged.connect(self.on_api_streaming_port_checkbox_changed)

        # API Streaming Port Textfield
        self.api_streaming_port_SpinBox = QSpinBox()
        self.api_streaming_port_SpinBox.setToolTip("The listening port for the streaming API.\nDefault: 5005")
        self.api_streaming_port_SpinBox.setVisible(False)
        self.api_streaming_port_SpinBox.setEnabled(False)
        self.api_streaming_port_SpinBox.setRange(0, 65535)
        self.api_streaming_port_SpinBox.setValue(5005)
        layout.addWidget(self.api_streaming_port_SpinBox, 73 + len(gpu_stats), 1)

        # Enable Public API
        self.api_public_checkbox = QCheckBox("Enable Public API")
        self.api_public_checkbox.setToolTip("Create a public URL for the API using Cloudfare.")
        self.api_public_checkbox.setVisible(False)
        layout.addWidget(self.api_public_checkbox, 74 + len(gpu_stats), 0)
        self.api_public_checkbox.stateChanged.connect(self.on_api_public_checkbox_changed)

        # Seperator for the Toolbox Options
        self.toolboxendline = QFrame()
        self.toolboxendline.setFrameShape(QFrame.HLine)
        self.toolboxendline.setFrameShadow(QFrame.Sunken)
        self.toolboxendline.setVisible(False)
        layout.addWidget(self.toolboxendline, 75 + len(gpu_stats), 0, 1, 3)

        # Authentication Box
        authentication_box = QHBoxLayout()

        # Authentication Checkbox
        self.authentication_checkbox = QCheckBox("Authentication")
        self.authentication_checkbox.setToolTip("Enable gradio authentication")
        self.authentication_checkbox.stateChanged.connect(self.on_authentication_checkbox_changed)
        authentication_box.addWidget(self.authentication_checkbox)

        # Choose File Field
        self.choose_file_label = QLabel("Choose File:")
        self.choose_file_label.setVisible(False)
        self.choose_file_label.setToolTip("Choose a file to use for the authentication credentials. Credentials should be saved like:\nUSERNAME1:PASSWORD1\nUSERNAME2:PASSWORD2")
        authentication_box.addWidget(self.choose_file_label)

        self.choose_file_button = QPushButton("Browse")
        self.choose_file_button.setVisible(False)
        self.choose_file_button.setToolTip("Choose a file to use for the authentication credentials. Credentials should be saved like:\nUSERNAME1:PASSWORD1\nUSERNAME2:PASSWORD2")
        self.choose_file_button.clicked.connect(self.on_choose_file_button_clicked)
        authentication_box.addWidget(self.choose_file_button)
        layout.addLayout(authentication_box, 80 + len(gpu_stats), 0, 1, 3)

        # Extensions Selection Menu
        self.use_extensions_checkbox = QCheckBox("Use Extensions")
        self.use_extensions_checkbox.setToolTip("Choose the extensions to be loaded.")
        layout.addWidget(self.use_extensions_checkbox, 90 + len(gpu_stats), 0)
        self.use_extensions_checkbox.stateChanged.connect(self.on_use_extensions_checkbox_changed)

        self.extensions_list = QListWidget()
        self.extensions_list.setToolTip("Choose the extensions to be loaded.")
        layout.addWidget(self.extensions_list, 90 + len(gpu_stats), 1, 1, 2)
        self.extensions_list.setFixedHeight(150)
        self.extensions_list.setVisible(False)
        extensions = [name for name in os.listdir(extensions_folder) if os.path.isdir(os.path.join(extensions_folder, name)) and "api" not in name.lower()]
        extensions.sort()

        for extension in extensions:
            item = QListWidgetItem(extension)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.extensions_list.addItem(item)

        # Lora selection menu
        self.use_lora_checkbox = QCheckBox("Use Loras")
        self.use_lora_checkbox.setToolTip("Choose the loras to be loaded.")
        layout.addWidget(self.use_lora_checkbox, 100 + len(gpu_stats), 0)
        self.use_lora_checkbox.stateChanged.connect(self.on_use_lora_checkbox_changed)

        self.lora_list = QListWidget()
        self.lora_list.setToolTip("Choose the loras to be loaded.")
        layout.addWidget(self.lora_list, 100 + len(gpu_stats), 1, 1, 2)
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
        layout.addWidget(self.use_network_checkbox, 110 + len(gpu_stats), 0)

        # Use Automatically opens the Browser when finished loading the webui
        self.use_autolaunch_checkbox = QCheckBox("Auto open Browser")
        self.use_autolaunch_checkbox.setToolTip("Automatically Opens your browser when loading is finished")
        layout.addWidget(self.use_autolaunch_checkbox, 120 + len(gpu_stats), 0)
    
        # Listen Port Checkbox and Text Field
        self.listen_port_checkbox = QCheckBox("Listen Port")
        self.listen_port_checkbox.setToolTip("Choose the Port to use for the WebUI.\nDefault is 7680. If you want to use Stable Diffusion at the same time,\nor got other services running on this Port, you can change it in the textfield.")
        self.listen_port_checkbox.stateChanged.connect(self.on_listen_port_checkbox_changed)
        layout.addWidget(self.listen_port_checkbox, 130 + len(gpu_stats), 1)
    
        # Auto Close the GUI when pressing start.
        self.use_autoclose_checkbox = QCheckBox("Close GUI on Start")
        self.use_autoclose_checkbox.setToolTip("Auto Close the GUI when pressing start button.")
        layout.addWidget(self.use_autoclose_checkbox, 130 + len(gpu_stats), 0)

        self.listen_port_textfield = QLineEdit()
        self.listen_port_textfield.setPlaceholderText("Enter port number")
        self.listen_port_textfield.setEnabled(False)
        layout.addWidget(self.listen_port_textfield, 140 + len(gpu_stats), 1)

        self.start_button = QPushButton("Start")
        self.start_button.setToolTip("Starts the Webui with the settings set by this GUI")
        self.start_button.clicked.connect(self.on_start_button_clicked)
        layout.addWidget(self.start_button, 140 + len(gpu_stats), 0)

        self.save_button = QPushButton("Save Settings")
        self.save_button.setToolTip("You can Save your current Settings. Neat, isn't it?")
        self.save_button.clicked.connect(self.on_save_button_clicked)
        layout.addWidget(self.save_button, 150 + len(gpu_stats), 0)

        # Load Button
        self.load_button = QPushButton("Load")
        self.load_button.setToolTip("It's a button. That loads a selected Profile. Sometimes, I'm just create explaining things.")
        self.load_button.clicked.connect(self.on_load_button_clicked)
        layout.addWidget(self.load_button, 150 + len(gpu_stats), 1)

        # Show if Update is available
        self.update_button_ui = QPushButton("Update\nAvailable")
        self.update_button_ui.setToolTip("Shows if an update is available")
        self.update_button_ui.setStyleSheet("QPushButton { color: #ff9999; font-weight: bold; }")
        self.update_button_ui.clicked.connect(self.on_update_button_ui_clicked)
        layout.addWidget(self.update_button_ui, 150 + len(gpu_stats), 2, 2, 2)
        self.update_button_ui.setVisible(False)

        # Textfield for the Profile Name
        self.profile_name_textfield = QLineEdit()
        self.profile_name_textfield.setPlaceholderText("Enter Name for the Profile, keep empty to overwrite default")
        self.profile_name_textfield.setToolTip("You can leave this blank, then only the default profile will be overwritten. If you want to get some organizing done, you can name it. For example:\nProfile for RP\nProfile for Chat\nProfile for coding\nProfile for Superbooga\nERROR: 404 no limits found")
        layout.addWidget(self.profile_name_textfield, 151 + len(gpu_stats), 0)

        # Profiles Dropdown
        self.profiles_dropdown = QComboBox()
        self.populate_profiles_dropdown()
        #self.profiles_dropdown.setPlaceholderText("Choose Profile to load")
        self.profiles_dropdown.setToolTip("Here you can choose which profile you want to load. Choose, Load, Profit.")
        #layout.addWidget(QLabel("Choose Profile:"), 84 + len(gpu_stats), 1)
        layout.addWidget(self.profiles_dropdown, 151 + len(gpu_stats), 1)
    
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


    def on_api_public_checkbox_changed(self, state):
        self.api_streaming_port_SpinBox.setEnabled(False)
        self.api_blocking_port_SpinBox.setEnabled(False)

    def on_api_streaming_port_checkbox_changed(self, state):
        if not self.api_public_checkbox.isChecked() and self.api_checkbox.isChecked():
            self.api_streaming_port_SpinBox.setEnabled(state == Qt.Checked)

    def on_api_blocking_port_checkbox_changed(self, state):
        if not self.api_public_checkbox.isChecked() and self.api_checkbox.isChecked():
            self.api_blocking_port_SpinBox.setEnabled(state == Qt.Checked)

    def on_api_settings_checkbox_stateChanged(self, state):
        self.api_header.setVisible(state == Qt.Checked)
        self.api_checkbox.setVisible(state == Qt.Checked)
        self.api_blocking_port_checkbox.setVisible(state == Qt.Checked)
        self.api_blocking_port_SpinBox.setVisible(state == Qt.Checked)
        self.api_streaming_port_checkbox.setVisible(state == Qt.Checked)
        self.api_streaming_port_SpinBox.setVisible(state == Qt.Checked)
        self.api_public_checkbox.setVisible(state == Qt.Checked)
        self.toolboxendline.setVisible(state == Qt.Checked)

    def on_rwkv_settings_checkbox_stateChanged(self, state):
        self.rwkv_header.setVisible(state == Qt.Checked)
        self.rwkv_checkbox.setVisible(state == Qt.Checked)
        self.rwkv_strategy_checkbox.setVisible(state == Qt.Checked)
        self.rwkv_strategy_dropdown.setVisible(state == Qt.Checked)
        self.rwkv_allocation_spinbox.setVisible(state == Qt.Checked)
        self.rwkv_cuda_checkbox.setVisible(state == Qt.Checked)
        self.rwkv_line.setVisible(state == Qt.Checked)

    def on_flexgen_settings_checkbox_stateChanged(self, state):
        self.flexgen_header_label.setVisible(state == Qt.Checked)
        self.flexgen_checkbox.setVisible(state == Qt.Checked)
        self.flexgen_percentage_label.setVisible(state == Qt.Checked)
        self.flexgen_percentage_spinbox1.setVisible(state == Qt.Checked)
        self.flexgen_percentage_spinbox2.setVisible(state == Qt.Checked)
        self.flexgen_percentage_spinbox3.setVisible(state == Qt.Checked)
        self.flexgen_percentage_spinbox4.setVisible(state == Qt.Checked)
        self.flexgen_percentage_spinbox5.setVisible(state == Qt.Checked)
        self.flexgen_percentage_spinbox6.setVisible(state == Qt.Checked)
        self.flexgen_compression_checkbox.setVisible(state == Qt.Checked)
        self.flexgen_pin_weight_label.setVisible(state == Qt.Checked)
        self.flexgen_pin_weight_dropdown.setVisible(state == Qt.Checked)
        self.flexline.setVisible(state == Qt.Checked)
        #self.flexgen_line.setVisible(state == Qt.Checked)
        #self.flexgen_line.setVisible(state == Qt.Checked)

    def on_llama_settings_checkbox_stateChanged(self, state):
        self.llama_label_header.setVisible(state == Qt.Checked)
        self.llama_threads_spinbox.setVisible(state == Qt.Checked)
        self.llama_threads_label.setVisible(state == Qt.Checked)
        self.llama_batch_size_label.setVisible(state == Qt.Checked)
        self.llama_batch_size_spinbox.setVisible(state == Qt.Checked)
        self.llama_mmap_checkbox.setVisible(state == Qt.Checked)
        self.llama_mlock_checkbox.setVisible(state == Qt.Checked)
        self.llama_cache_capacity_label.setVisible(state == Qt.Checked)
        self.llama_cache_capacity_spinbox.setVisible(state == Qt.Checked)
        self.llama_line.setVisible(state == Qt.Checked)
        self.llama_gpu_layer_label.setVisible(state == Qt.Checked)
        self.llama_gpu_layer_spinbox.setVisible(state == Qt.Checked)
        self.llama_cache_capacity_units.setVisible(state == Qt.Checked)

    def on_deepspeed_nvme_button_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, "Offload Directory")
        if folder:
            self.selected_offload_directory = folder
            self.deepspeed_nvme_current_label.setText(f"Current Directory Folder: {self.selected_offload_directory}")
        else:
            self.selected_offload_directory = none

#    def on_deepspeed_nvme_button_clicked(self):
 #       folder = QFileDialog.getExistingDirectory(self, "Offload Directory")
   #     if folder:
  #          self.offload_directory = folder
    #        self.deepspeed_nvme_current_label.setText(f"Current Directory Folder: {self.offload_directory}")

    def on_deepspeed_nvme_checkbox_changed(self, state):
        self.deepspeed_nvme_label.setVisible(state == Qt.Checked)
        self.deepspeed_nvme_current_label.setVisible(state == Qt.Checked)
        self.deepspeed_nvme_button.setVisible(state == Qt.Checked)

    def on_deepspeed_settings_checkbox_stateChanged(self, state):
        self.deepspeed_label_header.setVisible(state == Qt.Checked)
        self.deepspeed_checkbox.setVisible(state == Qt.Checked)
        self.deepspeed_local_rank_label.setVisible(state == Qt.Checked)
        self.deepspeed_local_rank_spinbox.setVisible(state == Qt.Checked)
        self.deepspeed_line.setVisible(state == Qt.Checked)
        self.deepspeed_gpu_num_label.setVisible(state == Qt.Checked)
        self.deepspeed_gpu_num_spinbox.setVisible(state == Qt.Checked)
        self.deepspeed_nvme_checkbox.setVisible(state == Qt.Checked)

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
        release_url = f"https://github.com/Pakobbix/StartUI-oobabself.offload_directoryooga-webui/releases/tag/{latest_version}"
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

        if not self.use_disk_checkbox.isChecked():
            self.choose_disk_folder_label.setVisible(False)
            self.choose_disk_folder_button.setVisible(False)

        if self.use_disk_checkbox.isChecked() and self.change_disk_cache_checkbox.isChecked():
            self.choose_disk_folder_label.setVisible(True)
            self.choose_disk_folder_button.setVisible(True)

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
            "multimodal": self.use_multimodal_checkbox.isChecked(), # Saves the state of the multimodal checkbox
            "sdp_attention": self.use_sdp_attention_checkbox.isChecked(), # Saves the state of the sdp_attention checkbox
            "autogptq": self.use_autogptq_checkbox.isChecked(), # Saves the state of the autogptq checkbox
            "triton": self.use_triton_checkbox.isChecked(), # Saves the state of the triton checkbox
            "deepspeed": self.deepspeed_settings_checkbox.isChecked(), # Saves the state of the deepspeed checkbox
            "deepspeed_enabled": self.deepspeed_checkbox.isChecked(), # Saves the state of the deepspeed checkbox
            "deepspeed_gpu_num": self.deepspeed_gpu_num_spinbox.value(), # Saves the state of the deepspeed_gpu_num_spinbox
            "deepspeed_nvme_enabled": self.deepspeed_nvme_checkbox.isChecked(), # Saves the state of the deepspeed_nvme_checkbox
            "deepspeed_nvme_path": self.selected_offload_directory, # Saves the state of the offload_directory
            "deepspeed_local_rank": self.deepspeed_local_rank_spinbox.value(), # Saves the state of the deepspeed_local_rank_spinbox
            "llama_settings": self.llama_settings_checkbox.isChecked(), # Saves the state of the llama_settings_checkbox
            "llama_threads": self.llama_threads_spinbox.value(), # Saves the state of the llama_threads_spinbox
            "llama_batch_size": self.llama_batch_size_spinbox.value(), # Saves the state of the llama_batch_size_spinbox
            "llama_no_map": self.llama_mmap_checkbox.isChecked(), # Saves the state of the llama_no_map_checkbox
            "llama_use_mlock": self.llama_mlock_checkbox.isChecked(), # Saves the state of the llama_mlock_checkbox
            "llama_cache_capacity": self.llama_cache_capacity_spinbox.value(), # Saves the state of the llama_cache_capacity_spinbox
            "llama_cache_units": self.llama_cache_capacity_units.currentText(), # Saves the state of the llama_cache_capacity_units
            "llama_gpu_layer": self.llama_gpu_layer_spinbox.value(), # Saves the state of the llama_gpu_layer_spinbox
            "flexgen_settings": self.flexgen_settings_checkbox.isChecked(), # Saves the state of the flexgen_settings_checkbox
            "use_flexgen": self.flexgen_checkbox.isChecked(), # Saves the state of the flexgen_checkbox
            "flexgen_precentage_1": self.flexgen_percentage_spinbox1.value(), # Saves the state of the flexgen_percentage_spinbox1
            "flexgen_precentage_2": self.flexgen_percentage_spinbox2.value(), # Saves the state of the flexgen_percentage_spinbox2
            "flexgen_precentage_3": self.flexgen_percentage_spinbox3.value(), # Saves the state of the flexgen_percentage_spinbox3
            "flexgen_precentage_4": self.flexgen_percentage_spinbox4.value(), # Saves the state of the flexgen_percentage_spinbox4
            "flexgen_precentage_5": self.flexgen_percentage_spinbox5.value(), # Saves the state of the flexgen_percentage_spinbox5
            "flexgen_precentage_6": self.flexgen_percentage_spinbox6.value(), # Saves the state of the flexgen_percentage_spinbox6
            "flexgen_compression": self.flexgen_compression_checkbox.isChecked(), # Saves the state of the flexgen_compression_checkbox
            "flexgen_pin_weight": self.flexgen_pin_weight_dropdown.currentText(), # Saves the state of the flexgen_pin_weight_dropdown
            "rwkv_settings": self.rwkv_settings_checkbox.isChecked(), # Saves the state of the rwkv_settings_checkbox
            "use_rwkv": self.rwkv_checkbox.isChecked(), # Saves the state of the rwkv_checkbox
            "rwkv_strategy": self.rwkv_strategy_checkbox.isChecked(), # Saves the state of the rwkv_strategy_checkbox
            "rwkv_strategy_dropdown": self.rwkv_strategy_dropdown.currentText(), # Saves the state of the rwkv_strategy_dropdown
            "rwkv_allocation": self.rwkv_allocation_spinbox.value(), # Saves the state of the rwkv_allocation_spinbox
            "rwkv_cuda": self.rwkv_cuda_checkbox.isChecked(), # Saves the state of the rwkv_cuda_checkbox
            "api_settings": self.api_settings_checkbox.isChecked(), # Saves the state of the api_settings_checkbox
            "use_api": self.api_checkbox.isChecked(), # Saves the state of the api_checkbox
            "api_blocking_port_enabled": self.api_blocking_port_checkbox.isChecked(), # Saves the state of the api_blocking_port_checkbox
            "api_blocking_port": self.api_blocking_port_SpinBox.value(), # Saves the state of the api_blocking_port_SpinBox
            "api_streaming_port_enabled": self.api_streaming_port_checkbox.isChecked(), # Saves the state of the api_streaming_port_checkbox
            "api_streaming_port": self.api_streaming_port_SpinBox.value(), # Saves the state of the api_streaming_port_SpinBox
            "public_api": self.api_public_checkbox.isChecked(), # Saves the state of the api_public_checkbox
            "autotune": self.use_autotune_checkbox.isChecked(), # Saves the state of the autotune checkbox
            "autolaunch": self.use_autolaunch_checkbox.isChecked(), # Saves the state of the autotune checkbox
            "autoclose": self.use_autoclose_checkbox.isChecked(), # Saves the state of the autotune checkbox
            "nocache": self.use_nocache_checkbox.isChecked(), # Saves the state of the autotune checkbox
            "listen": self.use_network_checkbox.isChecked(), # Saves the state of the Local Network Checkbox
            "listen_port": self.listen_port_checkbox.isChecked(), # Saves the state of the Listen Port Checkbox
            "port_number": self.listen_port_textfield.text(), # Saves the Port given in the Textbox
            "authentication": self.authentication_checkbox.isChecked(), # Saves the state of the Authentication
            "authentication_file": self.choose_file_label.text(),  # Save the authentication file path
            "character": self.character_to_load.currentText(), # Saves the Characters given in the Textbox
            "use_extension": self.use_extensions_checkbox.isChecked(), # Saves the state of the Extension Checkbox
            "extensions": [self.extensions_list.item(i).text() for i in range(self.extensions_list.count()) if self.extensions_list.item(i).checkState() == Qt.Checked], # Saves the chosen Extensions
            "use_lora": self.use_lora_checkbox.isChecked(), # Saves the state of the Lora Checkbox
            "loras": [self.lora_list.item(i).text() for i in range(self.lora_list.count()) if self.lora_list.item(i).checkState() == Qt.Checked] # Saves the chosen loras
        }

        if nvidia_gpu:
            settings["gpu_vram"] = [slider.value() for slider in self.gpu_vram_sliders]

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

        # LLama Stuff

        # llama.cpp threads

        if self.llama_threads_spinbox.value() != 0:
            command += f" --threads {self.llama_threads_spinbox.value()}"
            command += f" --n_batch {self.llama_batch_size_spinbox.value()}"
            command += f" --cache-capacity {self.llama_cache_capacity_spinbox.value()}{self.llama_cache_capacity_units.currentText()}"

        if self.llama_gpu_layer_spinbox.value() != 0:
            command += f" --n-gpu-layers {self.llama_gpu_layer_spinbox.value()}"

        if self.llama_mmap_checkbox.isChecked():
            command += " --no-map"

        if self.llama_mlock_checkbox.isChecked():
            command += " --mlock"

        # FlexGen Commands

        if self.flexgen_checkbox.isChecked():
            command += " --flexgen"
            command += f" --percent {self.flexgen_percentage_spinbox1.value()} {self.flexgen_percentage_spinbox2.value()} {self.flexgen_percentage_spinbox3.value()} {self.flexgen_percentage_spinbox4.value()} {self.flexgen_percentage_spinbox5.value()} {self.flexgen_percentage_spinbox6.value()}"
            if self.flexgen_compression_checkbox.isChecked():
                command += " --compression-weight"
            if self.flexgen_pin_weight_dropdown.currentText() != "none":
                command += f" --pin-weight {self.flexgen_pin_weight_dropdown.currentText()}"

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

        # Add Characters to the command
        chosen_characters = self.character_to_load.currentText()
        if self.character_to_load.currentText() != "none":
            command += f" --character {chosen_characters}"
            print(chosen_characters)

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

        # Auto Device is Activated:
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

        # Multimodal Mode
        if self.use_multimodal_checkbox.isChecked():
            command += " --multimodal-pipeline"

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

        # IF sdp_attention is checked
        if self.use_sdp_attention_checkbox.isChecked():
            command += " --sdp-attention"

        # If AutoGPTQ is checked
        if self.use_autogptq_checkbox.isChecked():
            command += " --autogptq"

        # If triton is checked
        if self.use_triton_checkbox.isChecked():
            command += " --triton"

        # Adds the chosen extensions to the list of the command.
        extensions = [self.extensions_list.item(i).text() for i in range(self.extensions_list.count()) if self.extensions_list.item(i).checkState() == Qt.Checked]
        if self.use_extensions_checkbox.isChecked():
            if extensions:
                command += f" --extensions {' '.join(extensions)}"

        if self.api_checkbox.isChecked():
            command += " --api"
            if self.api_public_checkbox.isChecked():
                command += " --public-api"
        if self.api_checkbox.isChecked() and not self.api_public_checkbox.isChecked():
            if self.api_blocking_port_checkbox.isChecked():
                command += f" --api-blocking-port {self.api_blocking_port_SpinBox.text()}"
            if self.api_streaming_port_checkbox.isChecked():
                command += f" --api-streaming-port {self.api_streaming_port_SpinBox.text()}"

        # Just for debugging.
        #print(f"Command generated: python webuiGUI.py {command}")

        # Based on the Model that's chosen, we will take care of some necessary stuff.
        # Starts the webui in the conda env with the user given Options
        if self.deepspeed_checkbox.isChecked():
            if platform.system() == "Linux":
                gpu_number = self.deepspeed_gpu_num_spinbox.text()

                deepspeed_command = f"deepspeed --num_gpus={gpu_number} ./text-generation-webui/server.py --deepspeed"
                if self.deepspeed_nvme_checkbox.isChecked():
                    deepspeed_command += f" --nvme-offload-dir {self.offload_directory}"
                if self.deepspeed_local_rank_spinbox.text() != "0":
                    deepspeed_command += f" --local_rank {self.deepspeed_local_rank_spinbox.text()}"
                run_cmd_with_conda(f"pip install deepspeed ; clear && {deepspeed_command} {command}")
            elif platform.system() == "Windows":
                message = "DeepSpeed is currently not supported on Windows"
                QMessageBox.critical(self, "Error", message)

        if not self.deepspeed_checkbox.isChecked():
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
        self.use_multimodal_checkbox.setChecked(settings.get("multimodal", False))
        self.use_sdp_attention_checkbox.setChecked(settings.get("sdp_attention", False))
        self.use_autogptq_checkbox.setChecked(settings.get("autogptq", False))
        self.use_triton_checkbox.setChecked(settings.get("triton", False))
        self.deepspeed_settings_checkbox.setChecked(settings.get("deepspeed", False))
        self.deepspeed_checkbox.setChecked(settings.get("deepspeed_enabled", False))
        self.deepspeed_gpu_num_spinbox.setValue(int(settings.get("deepspeed_gpu_num", 0)))
        self.selected_offload_directory = settings.get("deepspeed_nvme_path", "")
        self.deepspeed_nvme_current_label.setText(f"Current Directory Folder: {self.selected_offload_directory}")
        self.deepspeed_nvme_checkbox.setChecked(settings.get("deepspeed_nvme_enabled", False))
        self.deepspeed_local_rank_spinbox.setValue(int(settings.get("deepspeed_local_rank", 0)))
        self.llama_settings_checkbox.setChecked(settings.get("llama_settings", False))
        self.llama_threads_spinbox.setValue(int(settings.get("llama_threads", 0)))
        self.llama_batch_size_spinbox.setValue(int(settings.get("llama_batch_size", 0)))
        self.llama_mmap_checkbox.setChecked(settings.get("llama_no_map", False))
        self.llama_mlock_checkbox.setChecked(settings.get("llama_use_mlock", False))
        self.llama_cache_capacity_spinbox.setValue(int(settings.get("llama_cache_capacity", 0)))
        self.llama_cache_capacity_units.setCurrentText(settings.get("llama_cache_units", ""))
        self.llama_gpu_layer_spinbox.setValue(int(settings.get("llama_gpu_layer", 0)))
        self.flexgen_settings_checkbox.setChecked(settings.get("flexgen_settings", False))
        self.flexgen_checkbox.setChecked(settings.get("use_flexgen", False))
        self.flexgen_percentage_spinbox1.setValue(int(settings.get("flexgen_precentage_1", 0)))
        self.flexgen_percentage_spinbox2.setValue(int(settings.get("flexgen_precentage_2", 100)))
        self.flexgen_percentage_spinbox3.setValue(int(settings.get("flexgen_precentage_3", 100)))
        self.flexgen_percentage_spinbox4.setValue(int(settings.get("flexgen_precentage_4", 0)))
        self.flexgen_percentage_spinbox5.setValue(int(settings.get("flexgen_precentage_5", 100)))
        self.flexgen_percentage_spinbox6.setValue(int(settings.get("flexgen_precentage_6", 0)))
        self.flexgen_compression_checkbox.setChecked(settings.get("flexgen_compression", False))
        self.flexgen_pin_weight_dropdown.setCurrentText(settings.get("flexgen_pin_weight", ""))
        self.rwkv_settings_checkbox.setChecked(settings.get("rwkv_settings", False))
        self.rwkv_checkbox.setChecked(settings.get("use_rwkv", False))
        self.rwkv_strategy_checkbox.setChecked(settings.get("rwkv_strategy", False))
        self.rwkv_strategy_dropdown.setCurrentText(settings.get("rwkv_strategy_dropdown", ""))
        self.rwkv_allocation_spinbox.setValue(int(settings.get("rwkv_allocation", 0)))
        self.rwkv_cuda_checkbox.setChecked(settings.get("rwkv_cuda", False))
        self.api_settings_checkbox.setChecked(settings.get("api_settings", False))
        self.api_checkbox.setChecked(settings.get("use_api", False))
        self.api_blocking_port_checkbox.setChecked(settings.get("api_blocking_port_enabled", False))
        self.api_blocking_port_SpinBox.setValue(int(settings.get("api_blocking_port", 5000)))
        self.api_streaming_port_checkbox.setChecked(settings.get("api_streaming_port_enabled", False))
        self.api_streaming_port_SpinBox.setValue(int(settings.get("api_streaming_port", 5005)))
        self.api_public_checkbox.setChecked(settings.get("public_api", False))
        self.use_autotune_checkbox.setChecked(settings.get("autotune", False))
        self.use_autolaunch_checkbox.setChecked(settings.get("autolaunch", False))
        self.use_autoclose_checkbox.setChecked(settings.get("autoclose", False))
        self.use_nocache_checkbox.setChecked(settings.get("nocache", False))
        self.authentication_checkbox.setChecked(settings.get("authentication", False))
        self.choose_file_label.setText(settings.get("authentication_file", ""))
        self.character_to_load.setCurrentText(settings.get("character", ""))
        self.pre_layer_slider.setValue(int(settings.get("prelayer", 0)))
        self.use_autolaunch_checkbox.setChecked(settings.get("autolaunch", False))
        self.use_network_checkbox.setChecked(settings.get("listen", False))
        
        if nvidia_gpu:
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
