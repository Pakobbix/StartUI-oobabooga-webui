import sys
import gpustat
import os
import json
import subprocess
import platform
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QComboBox, QSlider, QCheckBox, QLineEdit, QFileDialog, QPushButton, QWidget, QListWidget, QListWidgetItem, QToolTip
from PyQt5.QtCore import Qt

profiles_folder = "./profiles"
os.makedirs(profiles_folder, exist_ok=True)
model_folder = "./text-generation-webui/models"
extensions_folder = "./text-generation-webui/extensions"

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
        # For Linux, activate the Conda environment using the conda command
        activate_cmd = f"conda activate {conda_env_path} && "
        full_cmd = f"source ./installer_files/conda/etc/profile.d/conda.sh && conda run -p {conda_env_path} {cmd}"

        # Open a separate terminal window and execute the command
        process = subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', full_cmd], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle('StartUI for oobabooga webui')
        layout = QVBoxLayout()

        # Model Dropdown
        # Get the list of model folders
        model_folders = [name for name in os.listdir(model_folder) if os.path.isdir(os.path.join(model_folder, name))]

        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(model_folders)
        layout.addWidget(QLabel("Choose Model:"))
        self.model_dropdown.setToolTip("Select your prefered Model")
        layout.addWidget(self.model_dropdown)

        # WBIT Dropdown Menu
        self.wbit_dropdown = QComboBox()
        self.wbit_dropdown.addItems(["1", "2", "3", "4","8", "none"])
        layout.addWidget(QLabel("Choose Wbits:"))
        self.wbit_dropdown.setToolTip("Select the bits quantization for this model\nExample: vicuna 7b 4bit you should choose 4.\nYou can keep it at none, the webui will determine it automatically if the wbits are mentioned in the name of the model")
        layout.addWidget(self.wbit_dropdown)

        # Groupsize Dropdown Menu
        self.gsize_dropdown = QComboBox()
        self.gsize_dropdown.addItems(["32", "64", "128", "1024", "none"])
        layout.addWidget(QLabel("Choose Groupsize:"))
        self.gsize_dropdown.setToolTip("Select the groupsize used by the Model.\nExample: vicuna 7b 4bit-128g you should choose 128.\nYou can keep it at none, the webui will determine it automatically if the groupsize is mentioned in the name of the model")
        layout.addWidget(self.gsize_dropdown)

        # Mode Dropdown
        self.mode_dropdown = QComboBox()
        self.mode_dropdown.addItems(["chat", "cai_chat", "notebook"])
        layout.addWidget(QLabel("Choose Mode:"))
        self.mode_dropdown.setToolTip("Choose what kind of UI you want to load.")
        layout.addWidget(self.mode_dropdown)

        # GPU Checkbox and Sliders
        self.use_gpu_checkbox = QCheckBox("Use GPU")
        self.use_gpu_checkbox.setToolTip("Choose if you want to use your GPU\nNecessary if you set GPU VRAM Slider")
        layout.addWidget(self.use_gpu_checkbox)

        self.gpu_vram_sliders = []
        self.gpu_vram_labels = []

        gpu_stats = gpustat.GPUStatCollection.new_query()

        for i, gpu in enumerate(gpu_stats):
            gpu_label = QLabel(f"GPU {i} VRAM:")
            layout.addWidget(gpu_label)

            vram_slider = QSlider(Qt.Horizontal)
            vram_slider.setMaximum(int(gpu.memory_total / 1024))
            vram_slider.valueChanged.connect(lambda value, idx=i: self.on_vram_slider_changed(value, idx))
            layout.addWidget(vram_slider)

            vram_value_label = QLabel("0 GiB")
            layout.addWidget(vram_value_label)
            self.gpu_vram_labels.append(vram_value_label)

            self.gpu_vram_sliders.append(vram_slider)

        # Pre-layer Slider
        self.pre_layer_slider = QSlider(Qt.Horizontal)
        self.pre_layer_slider.setMinimum(0)
        self.pre_layer_slider.setMaximum(100)
        self.pre_layer_slider.setTickInterval(1)
        self.pre_layer_slider.setSingleStep(1)
        layout.addWidget(QLabel("Pre-layer:"))
        self.pre_layer_slider.setToolTip("The number of layers to allocate to the GPU. Setting this parameter enables CPU offloading for 4-bit models.")
        layout.addWidget(self.pre_layer_slider)

        self.pre_layer_value_label = QLabel("0")
        layout.addWidget(self.pre_layer_value_label)

        # Connect the valueChanged signal of the pre-layer slider to update the value label
        self.pre_layer_slider.valueChanged.connect(self.on_pre_layer_slider_changed)

        # Load in 8 Bit Mode
        self.use_8bit_checkbox = QCheckBox("Load in 8bit")
        self.use_8bit_checkbox.setToolTip("Load the model with 8-bit precision. Reduces the amount of VRAM running native Models")
        layout.addWidget(self.use_8bit_checkbox)

        # Authentication Checkbox
        self.authentication_checkbox = QCheckBox("Authentication")
        self.authentication_checkbox.setToolTip("Enable gradio authentication")
        layout.addWidget(self.authentication_checkbox)
        self.authentication_checkbox.stateChanged.connect(self.on_authentication_checkbox_changed)

        # Choose File Field
        self.choose_file_label = QLabel("Choose File:")
        self.choose_file_label.setVisible(False)
        self.choose_file_label.setToolTip("Choose a file to use for the authentication credentials. Credentials should be saved like:\nUSERNAME1:PASSWORD1\nUSERNAME2:PASSWORD2")
        layout.addWidget(self.choose_file_label)

        self.choose_file_button = QPushButton("Browse")
        self.choose_file_button.setVisible(False)
        self.choose_file_button.setToolTip("Choose a file to use for the authentication credentials. Credentials should be saved like:\nUSERNAME1:PASSWORD1\nUSERNAME2:PASSWORD2")
        self.choose_file_button.clicked.connect(self.on_choose_file_button_clicked)
        layout.addWidget(self.choose_file_button)


        # Extensions List
        self.extensions_list = QListWidget()
        self.extensions_list.setToolTip("Choose the extensions to be loaded.")
        layout.addWidget(QLabel("Choose Extensions:"))
        layout.addWidget(self.extensions_list)
        extensions = [name for name in os.listdir(extensions_folder) if os.path.isdir(os.path.join(extensions_folder, name))]

        for extension in extensions:
            item = QListWidgetItem(extension)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.extensions_list.addItem(item)

        # Use Whole Local Network
        self.use_network_checkbox = QCheckBox("Local Network Mode")
        self.use_network_checkbox.setToolTip("By default, the WebUI will only be reachable by the PC running it.\nIf you want to use it also on other devices, check this")
        layout.addWidget(self.use_network_checkbox)

        # Listen Port Checkbox and Text Field
        self.listen_port_checkbox = QCheckBox("Listen Port")
        self.listen_port_checkbox.setToolTip("Choose the Port to use for the WebUI.\nDefault is 7680. If you want to use Stable Diffusion at the same time,\nor got other services running on this Port, you can change it in the textfield.")
        self.listen_port_checkbox.stateChanged.connect(self.on_listen_port_checkbox_changed)
        layout.addWidget(self.listen_port_checkbox)

        self.listen_port_textfield = QLineEdit()
        self.listen_port_textfield.setPlaceholderText("Enter port number")
        self.listen_port_textfield.setEnabled(False)
        layout.addWidget(self.listen_port_textfield)

        # Use Whole Local Network
        self.use_autolaunch_checkbox = QCheckBox("Auto open Browser")
        self.use_autolaunch_checkbox.setToolTip("Automatically Opens your browser when loading is finished")
        layout.addWidget(self.use_autolaunch_checkbox)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.start_button = QPushButton("Start")
        self.start_button.setToolTip("Starts the Webui with the settings set by this GUI")
        self.start_button.clicked.connect(self.on_start_button_clicked)
        layout.addWidget(self.start_button)

        self.save_button = QPushButton("Save Settings")
        self.save_button.setToolTip("You can Save your current Settings. Neat, isn't it?")
        self.save_button.clicked.connect(self.on_save_button_clicked)
        layout.addWidget(self.save_button)

        # Textfield for the Profile Name
        self.profile_name_textfield = QLineEdit()
        self.profile_name_textfield.setPlaceholderText("Enter Name for the Profile, keep empty to overwrite default")
        self.profile_name_textfield.setToolTip("You can leave this blank, then only the default profile will be overwritten. If you want to get some organizing done, you can name it. For example:\nProfile for RP\nProfile for Chat\nProfile for coding\nProfile for Superbooga\nERROR: 404 no limits found")
        layout.addWidget(self.profile_name_textfield)

        # Save current Settings
        self.destroyed.connect(self.save_settings)

        # Profiles Dropdown
        self.profiles_dropdown = QComboBox()
        self.populate_profiles_dropdown()
        self.profiles_dropdown.setToolTip("Here you can choose which profile you want to load. Choose, Load, Profit.")
        layout.addWidget(QLabel("Choose Profile:"))
        layout.addWidget(self.profiles_dropdown)
    
        # Load Button
        self.load_button = QPushButton("Load")
        self.load_button.setToolTip("It's a button. That loads a selected Profile. Sometimes, I'm just create explaining things.")
        self.load_button.clicked.connect(self.on_load_button_clicked)
        layout.addWidget(self.load_button)
    

    def on_pre_layer_slider_changed(self, value):
        # Update the value label with the current value of the pre-layer slider
        self.pre_layer_value_label.setText(str(value))

    def on_vram_slider_changed(self, value, gpu_idx):
        self.gpu_vram_labels[gpu_idx].setText(f"{value} GiB")
        #print(f"GPU {gpu_idx} VRAM usage: {value} GiB")

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
            "model": self.model_dropdown.currentText(),
            "wbits": self.wbit_dropdown.currentText(),
            "groupsize": self.gsize_dropdown.currentText(),
            "mode": self.mode_dropdown.currentText(),
            "use_gpu": self.use_gpu_checkbox.isChecked(),
            "prelayer": self.pre_layer_value_label.text(),
            "use_8bit": self.use_8bit_checkbox.isChecked(),
            "autolaunch": self.use_autolaunch_checkbox.isChecked(),
            "listen": self.use_network_checkbox.isChecked(),
            "listen_port": self.listen_port_checkbox.isChecked(),
            "port_number": self.listen_port_textfield.text(),
            "authentication": self.authentication_checkbox.isChecked(),
            "authentication_file": self.choose_file_label.text(),  # Save the authentication file path
            "gpu_vram": [slider.value() for slider in self.gpu_vram_sliders],
            "extensions": [self.extensions_list.item(i).text() for i in range(self.extensions_list.count()) if self.extensions_list.item(i).checkState() == Qt.Checked]
        }

        # Get the text entered in the text field
        profile_name = self.profile_name_textfield.text()
    
        if not profile_name:
            profile_name = "default"
    
        file_path = os.path.join(profiles_folder, f"{profile_name}.json")
    
        with open(file_path, "w") as file:
            json.dump(settings, file, indent=4)
      
    def on_start_button_clicked(self):
        command = ""

        # Add the chosen model to the command
        chosen_model = self.model_dropdown.currentText()
        command += f" --model {chosen_model}"

        # Adds wbits to the command, if not "none"
        chosen_wbits = self.wbit_dropdown.currentText()
        if self.wbit_dropdown.currentText() != "none":
            command += f" --wbits {chosen_wbits}"

        # Adds Groupsize to the command, if not "none"
        chosen_gsize = self.gsize_dropdown.currentText()
        if self.gsize_dropdown.currentText() != "none":
            command += f" --groupsize {chosen_gsize}"

        # Add the chosen mode to the command (Chat, cai-chat, notebook)
        chosen_mode = self.mode_dropdown.currentText()
        command += f" --{chosen_mode}"

        # Add GPU-related options if the "Use GPU" checkbox is checked
        if self.use_gpu_checkbox.isChecked():
            command += " --gpu-memory"
            for idx, slider in enumerate(self.gpu_vram_sliders):
                vram = slider.value()
                if vram > 0:
                    command += f" {vram}"

        # Add 8bit loading
        if self.use_8bit_checkbox.isChecked():
            command += " --load-in-8bit"

        # Add --auto-launch
        if self.use_autolaunch_checkbox.isChecked():
            command += " --auto-launch"

        # Local Network Mode
        if self.use_network_checkbox.isChecked():
            command += " --listen"

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
        if extensions:
            command += f" --extensions {' '.join(extensions)}"

        # Runs the WebuiGUI.py with the commands that were chosen by the User in the GUI.
        run_cmd_with_conda(f"python webuiGUI.py {command}")
        # print(f"Command generate: python webuiGUI.py {command}")
        exit()

    def save_settings(self):
        settings = {
            "model": self.model_dropdown.currentText(),
            "wbits": self.wbit_dropdown.currentText(),
            "groupsize": self.gsize_dropdown.currentText(),
            "mode": self.mode_dropdown.currentText(),
            "use_gpu": self.use_gpu_checkbox.isChecked(),
            "prelayer": self.pre_layer_value_label.text(),
            "use_8bit": self.use_8bit_checkbox.isChecked(),
            "listen": self.use_network_checkbox.isChecked(),
            "listen_port": self.listen_port_checkbox.isChecked(),
            "port_number": self.listen_port_textfield.text(),
            "authentication": self.authentication_checkbox.isChecked(),
            "authentication_file": self.choose_file_label.text(),  # Save the authentication file path
            "gpu_vram": [slider.value() for slider in self.gpu_vram_sliders],
            "extensions": [self.extensions_list.item(i).text() for i in range(self.extensions_list.count()) if self.extensions_list.item(i).checkState() == Qt.Checked]
        }

        with open(settings_file, "w") as file:
            json.dump(settings, file, indent=4)

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

    def load_settings(self):
        default_profile = os.path.join(profiles_folder, "default.json")
        if os.path.exists(default_profile):
            with open(default_profile, "r") as file:
                try:
                    settings = json.load(file)

                    self.model_dropdown.setCurrentText(settings.get("model", ""))
                    self.wbit_dropdown.setCurrentText(settings.get("wbits", ""))
                    self.gsize_dropdown.setCurrentText(settings.get("groupsize", ""))
                    self.mode_dropdown.setCurrentText(settings.get("mode", ""))
                    self.use_gpu_checkbox.setChecked(settings.get("use_gpu", False))
                    self.listen_port_checkbox.setChecked(settings.get("listen_port", False))
                    self.listen_port_textfield.setText(settings.get("port_number", ""))
                    self.use_8bit_checkbox.setChecked(settings.get("use_8bit", False))
                    self.authentication_checkbox.setChecked(settings.get("authentication", False))
                    self.choose_file_label.setText(settings.get("authentication_file", ""))
                    self.pre_layer_slider.setValue(int(settings.get("prelayer", 0)))
                    self.use_autolaunch_checkbox.setChecked(settings.get("autolaunch", False))
                    self.use_network_checkbox.setChecked(settings.get("listen", False))

                    gpu_vram_settings = settings.get("gpu_vram", [])
                    for idx, slider in enumerate(self.gpu_vram_sliders):
                        if idx < len(gpu_vram_settings):
                            slider.setValue(gpu_vram_settings[idx])
                    extensions_settings = settings.get("extensions", [])
                    for i in range(self.extensions_list.count()):
                        extension = self.extensions_list.item(i).text()
                        if extension in extensions_settings:
                            self.extensions_list.item(i).setCheckState(Qt.Checked)
                        else:
                            self.extensions_list.item(i).setCheckState(Qt.Unchecked)
                
                except json.JSONDecodeError:
                    # Handle the case when the file is empty or not in valid JSON format
                    pass

    def load_profile(self, profile_file):
        with open(profile_file, "r") as file:
            try:
                settings = json.load(file)
                
                # Apply the loaded settings to the GUI elements
                self.model_dropdown.setCurrentText(settings.get("model", ""))
                self.wbit_dropdown.setCurrentText(settings.get("wbits", ""))
                self.gsize_dropdown.setCurrentText(settings.get("groupsize", ""))
                self.mode_dropdown.setCurrentText(settings.get("mode", ""))
                self.use_gpu_checkbox.setChecked(settings.get("use_gpu", False))
                self.listen_port_checkbox.setChecked(settings.get("listen_port", False))
                self.listen_port_textfield.setText(settings.get("port_number", ""))
                self.use_8bit_checkbox.setChecked(settings.get("use_8bit", False))
                self.authentication_checkbox.setChecked(settings.get("authentication", False))
                self.choose_file_label.setText(settings.get("authentication_file", ""))
                self.pre_layer_slider.setValue(int(settings.get("prelayer", 0)))
                self.use_autolaunch_checkbox.setChecked(settings.get("autolaunch", False))
                self.use_network_checkbox.setChecked(settings.get("listen", False))
    
                gpu_vram_settings = settings.get("gpu_vram", [])
                for idx, slider in enumerate(self.gpu_vram_sliders):
                    if idx < len(gpu_vram_settings):
                        slider.setValue(gpu_vram_settings[idx])
                
                extensions_settings = settings.get("extensions", [])
                for i in range(self.extensions_list.count()):
                    extension = self.extensions_list.item(i).text()
                    if extension in extensions_settings:
                        self.extensions_list.item(i).setCheckState(Qt.Checked)
                    else:
                        self.extensions_list.item(i).setCheckState(Qt.Unchecked)
            
            except json.JSONDecodeError:
                # Handle the case when the file is empty or not in valid JSON format
                pass


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())

