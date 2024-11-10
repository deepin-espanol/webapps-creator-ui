#!/usr/bin/env python3

import os
import sys
import configparser
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox, QDialog, QTextBrowser, QVBoxLayout, QWidget, QToolBar, QAction, QStackedWidget, QListWidget, QListWidgetItem)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QTranslator, QLocale
from PyQt5.QtGui import QPixmap, QPainter, QColor

LOG_FILE = os.path.expanduser('~/.webapps-creator-ui/webapp_log.txt')
CONFIG_FILE = os.path.expanduser('~/.webapps-creator-ui/config.json')

class WebAppCreator(QMainWindow):
    def center_on_screen(self, window):
        resolution = QApplication.desktop().screenGeometry()
        window.move(int((resolution.width() / 2) - (window.frameSize().width() / 2)),
                    int((resolution.height() / 2) - (window.frameSize().height() / 2)))

    def colorize_icon(self, icon: QIcon, color: QColor) -> QIcon:
        pixmap = icon.pixmap(32, 32)
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()
        return QIcon(pixmap)

    def __init__(self):
        super().__init__()

        self.load_config()

        # Si no hay una configuración de idioma guardada, mostrar el selector de idioma
        if not self.config.get('language'):
            self.first_time_setup()

        # Cargar la traducción
        self.translator = QTranslator(self)
        if self.config.get('language'):
            lang = self.config['language']
        else:
            lang = QLocale.system().name()

        if self.translator.load("/usr/bin/webapps-creator-ui/languages/lg_" + lang):
            QApplication.instance().installTranslator(self.translator)

        self.init_ui()
        self.load_webapps_from_log()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {}

    def save_config(self):
        if not os.path.exists(os.path.dirname(CONFIG_FILE)):
            os.makedirs(os.path.dirname(CONFIG_FILE))
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)

    def first_time_setup(self):
        dialog = QDialog(self)

        dialog.setFixedSize(300, 120)

        layout = QVBoxLayout(dialog)
        dialog.setWindowTitle(self.tr("¡Bienvenido a WebApps Creator!"))

        label = QLabel(self.tr("Selecciona tu idioma:"))
        layout.addWidget(label)

        combo = QComboBox()
        combo.addItem("Español", "es")
        combo.addItem("English", "en")
        combo.addItem("Português", "pt")
        layout.addWidget(combo)

        def save_and_continue():
            self.config['language'] = combo.currentData()
            self.save_config()
            dialog.accept()

        button = QPushButton(self.tr("Guardar y continuar"))
        button.clicked.connect(save_and_continue)
        layout.addWidget(button)

        self.center_on_screen(dialog)
        dialog.exec_()

    def init_ui(self):
        self.setWindowTitle(self.tr("Creador de WebApps"))
        self.setWindowIcon(QIcon("/usr/share/icons/hicolor/scalable/apps/webapps-creator-ui.svg"))
        self.resize(400, 400)

        self.toolbar = QToolBar(self)
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        celeste_color = QColor(0, 184, 255)

        create_icon_colored = self.colorize_icon(QIcon.fromTheme("document-new"), celeste_color)
        create_action = QAction(create_icon_colored, self.tr("Crear"), self)
        create_action.setToolTip(self.tr("Crear una nueva WebApp"))
        create_action.triggered.connect(self.show_create_page)
        self.toolbar.addAction(create_action)

        list_icon_colored = self.colorize_icon(QIcon.fromTheme("document-open"), celeste_color)
        list_action = QAction(list_icon_colored, self.tr("Listar"), self)
        list_action.setToolTip(self.tr("Listar WebApps existentes"))
        list_action.triggered.connect(self.show_list_page)
        self.toolbar.addAction(list_action)

        help_icon_colored = self.colorize_icon(QIcon.fromTheme("help-contents"), celeste_color)
        help_action = QAction(help_icon_colored, self.tr("Ayuda"), self)
        help_action.setToolTip(self.tr("Ver la ayuda del programa"))
        help_action.triggered.connect(self.show_help)
        self.toolbar.addAction(help_action)

        about_icon_colored = self.colorize_icon(QIcon.fromTheme("help-about"), celeste_color)
        about_action = QAction(about_icon_colored, self.tr("Acerca de"), self)
        about_action.setToolTip(self.tr("Acerca de WebApps Creator UI"))
        about_action.triggered.connect(self.show_about)
        self.toolbar.addAction(about_action)

        self.central_widget = QWidget()
        main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.create_page = QWidget()
        create_layout = QVBoxLayout(self.create_page)

        self.app_name_label = QLabel(self.tr("Nombre de la WebApp:"))
        create_layout.addWidget(self.app_name_label)

        self.app_name_input = QLineEdit()
        create_layout.addWidget(self.app_name_input)

        self.app_url_label = QLabel(self.tr("URL de la WebApp ( formato https:// ):"))
        create_layout.addWidget(self.app_url_label)

        self.app_url_input = QLineEdit()
        create_layout.addWidget(self.app_url_input)

        self.category_label = QLabel(self.tr("Categoría de la WebApp:"))
        create_layout.addWidget(self.category_label)

        self.category_combo_box = QComboBox()
        categories = ["Network", "Development", "Education", "Game", "Graphics", "Application", "Utility", "Video", "Audio", "AudioVideo", "Office", "System", "Utility", "Science"]
        self.category_combo_box.addItems(categories)
        self.category_combo_box.setCurrentIndex(0)
        create_layout.addWidget(self.category_combo_box)

        self.app_icon_label = QLabel(self.tr("Ícono de la WebApp:"))
        create_layout.addWidget(self.app_icon_label)

        self.app_icon_input = QLineEdit()
        create_layout.addWidget(self.app_icon_input)

        self.select_icon_button = QPushButton(self.tr("Seleccionar ícono"))
        self.select_icon_button.clicked.connect(self.select_icon)
        create_layout.addWidget(self.select_icon_button)

        self.browser_label = QLabel(self.tr("Navegador a utilizar:"))
        create_layout.addWidget(self.browser_label)

        self.browser_combo_box = QComboBox()
        self.browser_combo_box.addItem("Google Chrome", "/usr/bin/google-chrome-stable --app=")
        self.browser_combo_box.addItem("WebApps Browser (Less compatibility with WebSites)", "python3 /usr/bin/webapps-creator-ui/webapps-creator-ui-wb.py ")
        self.browser_combo_box.addItem("Microsoft Edge", "/usr/bin/microsoft-edge-stable --app=")
        self.browser_combo_box.addItem("Brave Browser", "/usr/bin/brave-browser-stable --app=")
        self.browser_combo_box.addItem("Deepin Browser", "/usr/bin/browser --no-fuser --app=")
        self.browser_combo_box.addItem("Deepin Browser - LingLong App", "/usr/bin/ll-cli run org.deepin.browser -- browser --app=")
        self.browser_combo_box.addItem("Opera Web Browser", "/usr/bin/opera --app=")
        self.browser_combo_box.addItem("Vivaldi", "/usr/bin/vivaldi-stable --app=")
        create_layout.addWidget(self.browser_combo_box)
        self.browser_combo_box.setCurrentIndex(0)

        self.create_button = QPushButton(self.tr("Crear WebApp"))
        self.create_button.clicked.connect(self.create_webapp)
        create_layout.addWidget(self.create_button)

        self.create_page.setLayout(create_layout)
        self.stacked_widget.addWidget(self.create_page)

        self.list_page = QWidget()
        list_layout = QVBoxLayout(self.list_page)

        self.webapp_list = QListWidget()
        list_layout.addWidget(self.webapp_list)

        self.delete_button = QPushButton(self.tr("Eliminar WebApp seleccionada"))
        self.delete_button.clicked.connect(self.delete_webapp)
        list_layout.addWidget(self.delete_button)

        self.list_page.setLayout(list_layout)
        self.stacked_widget.addWidget(self.list_page)

    def select_icon(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Seleccionar ícono"),
            "",
            self.tr("Imágenes (*.png *.xpm *.jpg *.bmp);;Todos los archivos (*)"),
            options=options
        )
        if file_name:
            self.app_icon_input.setText(file_name)

    def load_webapps_from_log(self):
        # Cargar las WebApps desde la lista
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as log_file:
                desktop_files = log_file.readlines()

            for desktop_file in desktop_files:
                desktop_file = desktop_file.strip()

                config = configparser.ConfigParser()
                config.read(desktop_file)

                app_name = config.get("Desktop Entry", "Name", fallback="Unknown")
                icon_path = config.get("Desktop Entry", "Icon", fallback=None)

                item = QListWidgetItem(app_name)
                item.setData(Qt.UserRole, desktop_file)

                if icon_path and os.path.exists(icon_path):
                    item.setIcon(QIcon(icon_path))

                self.webapp_list.addItem(item)

    def create_webapp(self):
        app_name = self.app_name_input.text()
        app_category = self.category_combo_box.currentText()
        app_url = self.app_url_input.text()
        app_icon = self.app_icon_input.text()
        browser_exec = self.browser_combo_box.currentData()

        # Verificar si los campos requeridos están vacíos Nota recordar verificar esto
        if not app_name or not app_url or not app_icon:
            QMessageBox.warning(self, self.tr("Campos faltantes"), self.tr("Por favor, asegúrese de ingresar el nombre, la URL y seleccionar un ícono para la WebApp."))
            return

        browser_exec = f"{browser_exec}{app_url}"

        config = configparser.ConfigParser()
        config.optionxform = str
        config["Desktop Entry"] = {
            "Type": "Application",
            "Name": app_name,
            "Categories": app_category + ";",
            "Comment": f"{app_name} WebApp",
            "Exec": browser_exec,
            "Icon": app_icon,
            "Terminal": "false"
        }

        desktop_file_path = os.path.join(os.path.expanduser("~"), ".local", "share", "applications", f"{app_name}.desktop")
        with open(desktop_file_path, "w") as desktop_file:
            config.write(desktop_file, space_around_delimiters=False)

        os.chmod(desktop_file_path, 0o755)

        QMessageBox.information(self, self.tr("WebApp creada con exito"), self.tr("WebApp creada y guardada en {0}").format(desktop_file_path))

        # Despues de guardar el archivo desktop
        with open(LOG_FILE, "a") as log_file:
            log_file.write(desktop_file_path + "\n")

        # Actualizar la lista de WebApps creadas
        item = QListWidgetItem(app_name)
        item.setData(Qt.UserRole, desktop_file_path)
        if app_icon and os.path.exists(app_icon):
            item.setIcon(QIcon(app_icon))
        self.webapp_list.addItem(item)

    def show_create_page(self):
        self.stacked_widget.setCurrentWidget(self.create_page)

    def show_list_page(self):
        self.stacked_widget.setCurrentWidget(self.list_page)

    def delete_webapp(self):
        current_item = self.webapp_list.currentItem()
        if current_item:
            desktop_file_path = current_item.data(Qt.UserRole)

            if os.path.exists(desktop_file_path):
                os.remove(desktop_file_path)

                # Actualizar el registro de las webapps
                with open(LOG_FILE, "r") as log_file:
                    lines = log_file.readlines()
                with open(LOG_FILE, "w") as log_file:
                    for line in lines:
                        if line.strip() != desktop_file_path:
                            log_file.write(line)

                self.webapp_list.takeItem(self.webapp_list.row(current_item))
                QMessageBox.information(self, "WebApp eliminada", "WebApp eliminada con éxito")
            else:
                QMessageBox.warning(self, "Error al eliminar", "No se pudo encontrar el archivo .desktop para eliminar.")

    def show_help(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("WebApps Creator UI - Ayuda"))
        layout = QVBoxLayout()
        dialog.setFixedSize(400, 300)

        text_browser = QTextBrowser()
        help_text = (f"""
        <h2>{self.tr('Como usar el programa:')}</h2>

        <h3>1. {self.tr('Crear una WebApp:')}</h3>
        <ul>
        <li>{self.tr('Ingresa el nombre de la WebApp en "Nombre de la WebApp".')}</li>
        <li>{self.tr('Proporciona la URL completa (asegúrate de que comience con "https://").')}</li>
        <li>{self.tr('Selecciona un ícono para tu WebApp usando el botón "Seleccionar ícono".')}</li>
        <li>{self.tr('Elige el navegador que deseas utilizar desde el menú desplegable.')}</li>
        <li>{self.tr('Haz clic en "Crear WebApp" para generar el acceso directo de la WebApp.')}</li>
        </ul>

        <h3>2. {self.tr('Listar WebApps existentes:')}</h3>
        <ul>
        <li>{self.tr('Haz clic en el botón "Listar" en la barra de herramientas.')}</li>
        <li>{self.tr('Verás una lista de todas las WebApps que has creado anteriormente.')}</li>
        </ul>

        <h3>3. {self.tr('Eliminar una WebApp:')}</h3>
        <ul>
        <li>{self.tr('En la página "Listar", selecciona una WebApp de la lista.')}</li>
        <li>{self.tr('Haz clic en "Eliminar WebApp seleccionada" para eliminarla.')}</li>
        <li>{self.tr('Se eliminará el acceso directo de la WebApp.')}</li>
        </ul>

        {self.tr('Si experimentas algún problema o tienes alguna pregunta, visita <a href="#">(Próximamente web)</a> o contacta a krafairuspc@gmail.com o reporta el problema en <a href="https://github.com/krafairus/webapps-creator-ui">GitHub</a>.')}
        """)

        text_browser.setHtml(help_text)
        text_browser.setOpenExternalLinks(True)

        layout.addWidget(text_browser)

        close_button = QPushButton(self.tr("Cerrar"))
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def show_about(self):
        about_text = self.tr(
            "Webapps Creator UI v1.4.0\n"
            "Desarrollado por krafairus - Equipo Deepines\n"
            "Más información en:\n"
            "https://github.com/deepin-espanol/webapps-creator-ui"
        )
        QMessageBox.information(self, self.tr("Acerca de Webapps Creator UI"), about_text)

def main():
    app = QApplication(sys.argv)
    creator = WebAppCreator()
    creator.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
