import sys
import math
import subprocess
import os
import configparser
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QHBoxLayout, QLabel, QListWidget, QTextEdit, QRadioButton, QGroupBox, QStatusBar, QMessageBox, QFileDialog, QComboBox, QDialog
)
from PyQt5.QtGui import QIcon


class SettingsDialog(QDialog):
    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres")
        self.setGeometry(300, 300, 500, 100)

        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

        houdini_bin = self.config.get(
            "Paths", "HOUDINI_BIN", fallback="C:\\Program Files\\Side Effects Software\\Houdini 20.5.487\\bin"
        )

        layout = QFormLayout()
        self.houdini_bin_input = QLineEdit(houdini_bin)
        browse_button = QPushButton("Parcourir")
        browse_button.clicked.connect(self.browse_houdini_bin)
        bin_layout = QHBoxLayout()
        bin_layout.addWidget(self.houdini_bin_input)
        bin_layout.addWidget(browse_button)
        layout.addRow("Chemin Houdini (bin) :", bin_layout)

        save_button = QPushButton("Sauvegarder")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addRow(buttons_layout)

        self.setLayout(layout)

    def browse_houdini_bin(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Sélectionner le dossier bin de Houdini")
        if folder:
            self.houdini_bin_input.setText(folder)

    def save_settings(self):
        if not self.config.has_section("Paths"):
            self.config.add_section("Paths")
        self.config.set("Paths", "HOUDINI_BIN", self.houdini_bin_input.text())
        with open(self.config_path, "w") as config_file:
            self.config.write(config_file)
        self.accept()


class HuskRenderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Automatisation de Rendus Husk')
        self.setGeometry(200, 200, 600, 600)

        # Ajoute ceci pour trouver l'icône même dans l'exe
        icon_path = os.path.join(
            getattr(sys, '_MEIPASS', os.path.dirname(
                os.path.abspath(__file__))),
            "icon.ico"
        )
        self.setWindowIcon(QIcon(icon_path))

        self.render_queue = []
        self.config_path = "config.ini"
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)
        self.load_environment_paths()

        main_layout = QVBoxLayout()
        self.create_form_layout(main_layout)
        self.create_render_queue_section(main_layout)
        self.create_log_section(main_layout)

        self.status_bar = QStatusBar(self)
        self.status_bar.showMessage('Prêt à lancer le rendu.')
        main_layout.addWidget(self.status_bar)

        launch_button = QPushButton("Lancer")
        launch_button.clicked.connect(self.start_render)
        main_layout.addWidget(launch_button)

        # Ajoute le bouton paramètres en bas
        settings_button = QPushButton("Paramètres")
        settings_button.clicked.connect(self.open_settings_dialog)
        main_layout.addWidget(settings_button)

        self.setLayout(main_layout)

    def load_environment_paths(self):
        houdini_bin = self.config.get(
            "Paths", "HOUDINI_BIN", fallback="C:\\Program Files\\Side Effects Software\\Houdini 20.0.653\\bin"
        )
        os.environ["PATH"] = houdini_bin + ";" + os.environ["PATH"]

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.config_path, self)
        if dialog.exec_():
            self.config.read(self.config_path)
            self.load_environment_paths()

    def create_form_layout(self, layout):
        form_layout = QFormLayout()

        self.scene_path_input = QLineEdit(self)
        browse_button = QPushButton("Parcourir", self)
        browse_button.clicked.connect(self.open_file_dialog)
        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.scene_path_input)
        browse_layout.addWidget(browse_button)
        form_layout.addRow('Chemin de la scène USD :', browse_layout)

        self.start_frame_input = QLineEdit(self)
        form_layout.addRow('Frame de début :', self.start_frame_input)

        self.end_frame_input = QLineEdit(self)
        form_layout.addRow('Frame de fin :', self.end_frame_input)

        self.resolution_input = QLineEdit(self)
        form_layout.addRow('Résolution en pourcentage :',
                           self.resolution_input)

        # Choix du renderer avec deux boutons radio
        renderer_group = QGroupBox("Renderer")
        renderer_layout = QHBoxLayout()
        self.karma_radio = QRadioButton("Karma", self)
        self.karmaxpu_radio = QRadioButton("KarmaXPU", self)
        self.karma_radio.setChecked(True)
        renderer_layout.addWidget(self.karma_radio)
        renderer_layout.addWidget(self.karmaxpu_radio)
        renderer_group.setLayout(renderer_layout)
        form_layout.addRow(renderer_group)

        render_type_group = QGroupBox("Type de rendu")
        render_type_layout = QHBoxLayout()
        self.full_render_radio = QRadioButton("Full Sequence", self)
        self.fml_render_radio = QRadioButton("FML", self)
        self.full_render_radio.setChecked(True)
        render_type_layout.addWidget(self.full_render_radio)
        render_type_layout.addWidget(self.fml_render_radio)
        render_type_group.setLayout(render_type_layout)
        form_layout.addRow(render_type_group)

        add_render_button = QPushButton("Ajouter à la file d'attente")
        add_render_button.clicked.connect(self.add_render_to_queue)
        form_layout.addRow(add_render_button)

        layout.addLayout(form_layout)

    def create_render_queue_section(self, layout):
        self.render_queue_list = QListWidget(self)
        layout.addWidget(QLabel("File d'attente des rendus :"))
        layout.addWidget(self.render_queue_list)

        remove_button = QPushButton("Supprimer le rendu sélectionné")
        remove_button.clicked.connect(self.remove_selected_render)
        layout.addWidget(remove_button)

    def create_log_section(self, layout):
        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

    def open_file_dialog(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir la scène USD", "", "Fichiers USD (*.usd *.usda *.usdc)")
        if filename:
            self.scene_path_input.setText(filename)

    def log_message(self, message):
        self.log_text.append(message)
        self.status_bar.showMessage(message)

    def add_render_to_queue(self):
        scene_path = self.scene_path_input.text()
        start_frame = self.start_frame_input.text()
        end_frame = self.end_frame_input.text()
        resolution = self.resolution_input.text()
        renderer = "Karma" if self.karma_radio.isChecked() else "KarmaXPU"
        render_type = "full" if self.full_render_radio.isChecked() else "fml"

        if not scene_path or not start_frame or not end_frame or not resolution:
            QMessageBox.warning(
                self, "Erreur", "Veuillez remplir tous les champs obligatoires.")
            return

        render_details = {
            "scene_path": scene_path,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "resolution": resolution,
            "renderer": renderer,
            "type": render_type
        }

        # Génération de la commande preview
        if render_type == "full":
            cmd_preview = f'husk --frame {start_frame}-{end_frame} --renderer {renderer} --res-scale {resolution} "{scene_path}"'
        else:
            # Correction du calcul de la frame du milieu
            start = int(start_frame)
            end = int(end_frame)
            mid = start + math.ceil((end - start) / 2)
            frames = [str(start), str(mid), str(end)]
            frame_str = " ".join(frames)
            cmd_preview = f'husk --frame-list {frame_str} --renderer {renderer} --res-scale {resolution} \"{scene_path}\"'

        render_details["cmd_preview"] = cmd_preview

        self.render_queue.append(render_details)
        self.render_queue_list.addItem(
            f"{cmd_preview}"
        )
        self.log_message("Rendu ajouté à la file d'attente.")

    def remove_selected_render(self):
        selected_row = self.render_queue_list.currentRow()
        if selected_row >= 0:
            self.render_queue.pop(selected_row)
            self.render_queue_list.takeItem(selected_row)
            self.log_message("Rendu supprimé de la file d'attente.")

    def start_render(self):
        if self.render_queue:
            self.start_render_queue()
        else:
            self.start_single_render()

    def start_single_render(self):
        scene_path = self.scene_path_input.text()
        start_frame = self.start_frame_input.text()
        end_frame = self.end_frame_input.text()
        resolution = self.resolution_input.text()
        renderer = "Karma" if self.karma_radio.isChecked() else "KarmaXPU"
        render_type = "full" if self.full_render_radio.isChecked() else "fml"

        if not scene_path or not start_frame or not end_frame or not resolution:
            QMessageBox.warning(
                self, "Erreur", "Veuillez remplir tous les champs obligatoires.")
            return

        try:
            if render_type == "full":
                self.render_scene_full(scene_path, int(start_frame), int(
                    end_frame), renderer, int(resolution))
            else:
                self.render_scene_fml(scene_path, int(start_frame), int(
                    end_frame), renderer, int(resolution))
            self.log_message("Rendu unique terminé.")
        except Exception as e:
            self.log_message(f"Erreur lors du rendu unique : {str(e)}")

    def start_render_queue(self):
        for render in self.render_queue:
            if render["type"] == "full":
                self.render_scene_full(
                    render["scene_path"],
                    int(render["start_frame"]),
                    int(render["end_frame"]),
                    render["renderer"],
                    int(render["resolution"])
                )
            else:
                self.render_scene_fml(
                    render["scene_path"],
                    int(render["start_frame"]),
                    int(render["end_frame"]),
                    render["renderer"],
                    int(render["resolution"])
                )
        self.log_message(
            "Tous les rendus dans la file d'attente ont été exécutés.")
        self.render_queue.clear()
        self.render_queue_list.clear()

    def render_scene_full(self, scene_path, start_frame, end_frame, renderer, res_scale):
        self.log_message(
            f"\n=== Lancement du rendu FULL SEQUENCE pour la scène : {scene_path} ===")
        cmd = f'husk --frame {start_frame}-{end_frame} --renderer {renderer} --res-scale {res_scale} "{scene_path}"'
        self.log_message(f"Commande de rendu : {cmd}")
        env = os.environ.copy()
        subprocess.run(cmd, shell=True, env=env)
        self.log_message("\n=== Rendu FULL terminé. ===")

    def render_scene_fml(self, scene_path, start_frame, end_frame, renderer, res_scale):
        self.log_message(
            f"\n=== Lancement du rendu FML pour la scène : {scene_path} ===")
        mid_frame = start_frame + math.ceil((end_frame - start_frame) / 2)
        frames = [start_frame, mid_frame, end_frame]
        frame_str = " ".join(str(f) for f in frames)
        cmd = f'husk --frame-list {frame_str} --renderer {renderer} --res-scale {res_scale} \"{scene_path}\"'
        self.log_message(f"Commande de rendu : {cmd}")
        env = os.environ.copy()
        subprocess.run(cmd, shell=True, env=env)
        self.log_message("\n=== Rendu FML terminé. ===")


if __name__ == "__main__":
    # Même chose ici
    icon_path = os.path.join(
        getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))),
        "icon.ico"
    )
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(icon_path))
    window = HuskRenderApp()
    window.show()
    sys.exit(app.exec_())
