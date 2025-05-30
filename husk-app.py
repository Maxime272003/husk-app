import os
import sys
import configparser
import subprocess

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QHBoxLayout, QLabel, QListWidget, QTextEdit, QRadioButton, QGroupBox, QStatusBar, QMessageBox, QFileDialog, QDialog
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

        # Gestion de l'icône (compatible PyInstaller)
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
            self.log_message("Paramètres mis à jour.")

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
                self, "Erreur", "Veuillez remplir tous les champs.")
            return

        try:
            start_frame_int = int(start_frame)
            end_frame_int = int(end_frame)
            res_scale_int = int(resolution)
        except ValueError:
            QMessageBox.warning(
                self, "Erreur", "Les frames et la résolution doivent être des entiers.")
            return

        renderer_map = {
            "Karma": "BRAY_HdKarma",
            "KarmaXPU": "BRAY_HdKarmaXPU"
        }
        renderer_cmd = renderer_map.get(renderer, renderer)

        if render_type == "full":
            frame_count = end_frame_int - start_frame_int + 1
            cmd_preview = f'husk --frame {start_frame_int} --frame-count {frame_count} --renderer {renderer_cmd} --res-scale {res_scale_int} "{scene_path}"'
        else:
            mid_frame = (start_frame_int + end_frame_int) // 2
            frames = [start_frame_int, mid_frame, end_frame_int]
            frame_str = " ".join(str(f) for f in frames)
            cmd_preview = f'husk --frame-list {frame_str} --renderer {renderer_cmd} --res-scale {res_scale_int} \"{scene_path}\"'

        self.render_queue.append({
            "scene_path": scene_path,
            "start_frame": start_frame_int,
            "end_frame": end_frame_int,
            "renderer": renderer,
            "res_scale": res_scale_int,
            "render_type": render_type
        })
        self.render_queue_list.addItem(cmd_preview)
        self.log_message(f"Ajouté à la file : {cmd_preview}")

    def remove_selected_render(self):
        selected = self.render_queue_list.currentRow()
        if selected >= 0:
            self.render_queue_list.takeItem(selected)
            del self.render_queue[selected]
            self.log_message("Rendu supprimé de la file.")

    def start_render(self):
        if not self.render_queue:
            QMessageBox.information(
                self, "Info", "La file d'attente est vide.")
            return
        self.start_render_queue()

    def start_render_queue(self):
        for render in self.render_queue:
            if render["render_type"] == "full":
                self.render_scene_full(
                    render["scene_path"],
                    render["start_frame"],
                    render["end_frame"],
                    render["renderer"],
                    render["res_scale"]
                )
            else:
                self.render_scene_fml(
                    render["scene_path"],
                    render["start_frame"],
                    render["end_frame"],
                    render["renderer"],
                    render["res_scale"]
                )
        self.log_message("Tous les rendus de la file ont été lancés.")

    def render_scene_full(self, scene_path, start_frame, end_frame, renderer, res_scale):
        renderer_map = {
            "Karma": "BRAY_HdKarma",
            "KarmaXPU": "BRAY_HdKarmaXPU"
        }
        renderer_cmd = renderer_map.get(renderer, renderer)
        frame_count = end_frame - start_frame + 1
        self.log_message(
            f"\n=== Lancement du rendu FULL SEQUENCE pour la scène : {scene_path} ===")
        cmd = f'husk --frame {start_frame} --frame-count {frame_count} --renderer {renderer_cmd} --res-scale {res_scale} "{scene_path}"'
        self.log_message(f"Commande de rendu : {cmd}")
        env = os.environ.copy()
        subprocess.Popen(f'cmd.exe /k {cmd}', env=env)
        self.log_message("\n=== Rendu FULL lancé dans un terminal. ===")

    def render_scene_fml(self, scene_path, start_frame, end_frame, renderer, res_scale):
        renderer_map = {
            "Karma": "BRAY_HdKarma",
            "KarmaXPU": "BRAY_HdKarmaXPU"
        }
        renderer_cmd = renderer_map.get(renderer, renderer)
        mid_frame = (start_frame + end_frame) // 2
        frames = [start_frame, mid_frame, end_frame]
        frame_str = " ".join(str(f) for f in frames)
        self.log_message(
            f"\n=== Lancement du rendu FML pour la scène : {scene_path} ===")
        cmd = f'husk --frame-list {frame_str} --renderer {renderer_cmd} --res-scale {res_scale} \"{scene_path}\"'
        self.log_message(f"Commande de rendu : {cmd}")
        env = os.environ.copy()
        subprocess.Popen(f'cmd.exe /k {cmd}', env=env)
        self.log_message("\n=== Rendu FML lancé dans un terminal. ===")


if __name__ == "__main__":
    # Gestion de l'icône pour l'application (barre des tâches)
    icon_path = os.path.join(
        getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))),
        "icon.ico"
    )
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(icon_path))
    window = HuskRenderApp()
    window.show()
    sys.exit(app.exec_())
