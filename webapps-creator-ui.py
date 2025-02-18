#!/usr/bin/env python3

import os
import sys
import configparser
import json
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog, QMessageBox,
    QDialog, QTextBrowser, QVBoxLayout, QWidget, QStackedWidget, QListWidget, QListWidgetItem, QHBoxLayout
)
from PyQt5.QtGui import QIcon, QColor, QPainter
from PyQt5.QtCore import Qt, QTranslator, QLocale, QPoint, QSettings, QSize

LOG_FILE = os.path.expanduser('~/.webapps-creator-ui/webapp_log.txt')
CONFIG_FILE = os.path.expanduser('~/.webapps-creator-ui/config.json')

def get_installed_browsers():
    try:
        result = subprocess.run(["python3", "/usr/share/webapps-creator-ui/checkbrowsers.py"], capture_output=True, text=True)
        if result.returncode == 0:
            browsers = []
            for line in result.stdout.splitlines():
                parts = line.split('"')
                if len(parts) >= 5:
                    browser_type = parts[0].strip()
                    browser_name = parts[1]
                    browser_command = parts[3]
                    browsers.append((browser_type, browser_name, browser_command))
            return browsers
        else:
            print("Error al ejecutar checkbrowser.py:", result.stderr)
            return []
    except Exception as e:
        print("Excepción al ejecutar checkbrowser.py:", str(e))
        return []

class BrowserSelectionWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Navegador")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        # Lista de navegadores
        self.browser_list = QListWidget()
        self.browser_list.setStyleSheet("""
            QListWidget {
                background-color: #2D2D2D;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                color: #BEBEBE;
                font-size: 14px;
            }
            QListWidget::item {
                background-color: #3A3A3A;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
            QListWidget::item:hover {
                background-color: #4A4A4A;
            }
            QListWidget::item:selected {
                background-color: #0081FF;
                color: #FFFFFF;
            }
        """)
        layout.addWidget(self.browser_list)

        save_button = QPushButton("Guardar")
        save_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #444;
                color: #BEBEBE;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        save_button.clicked.connect(self.save_selection)
        layout.addWidget(save_button)

        self.setLayout(layout)

        # Cargar la lista de navegadores
        self.load_browsers()

    def load_browsers(self):
        # Obtener la lista de navegadores instalados
        browsers = get_installed_browsers()

        webapps_browser = None
        other_browsers = []
        for browser in browsers:
            if browser[1] == "WebApps Browser":
                webapps_browser = browser
            else:
                other_browsers.append(browser)

        other_browsers.sort(key=lambda x: x[1])

        if webapps_browser:
            self.add_browser_item(webapps_browser, recommended=True)

        # Añadir los demás navegadores
        for browser in other_browsers:
            self.add_browser_item(browser)

    def add_browser_item(self, browser, recommended=False):
        browser_type, browser_name, browser_command = browser

        # Crear un ítem personalizado
        item = QListWidgetItem(f"{browser_name} ({browser_type})")
        item.setData(Qt.UserRole, (browser_name, browser_command))

        if browser_type == "system":
            item.setIcon(QIcon("/usr/share/webapps-creator-ui/icons/system.png"))  # Ruta al ícono para system
        elif browser_type == "flatpak":
            item.setIcon(QIcon("/usr/share/webapps-creator-ui/icons/flatpak.png"))  # Ruta al ícono para flatpak
        elif browser_type == "linyaps":
            item.setIcon(QIcon("/usr/share/webapps-creator-ui/icons/linyaps.png"))  # Ruta al ícono para linglong

        if recommended:
            item.setIcon(QIcon("/usr/share/webapps-creator-ui/icons/recommended.png"))  # Ruta al ícono recomendado

        self.browser_list.addItem(item)

    def save_selection(self):
        selected_item = self.browser_list.currentItem()
        if selected_item:
            browser_name, browser_command = selected_item.data(Qt.UserRole)

            config_path = CONFIG_FILE
            config = {}
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                except json.JSONDecodeError:
                    print("Error: El archivo config.json está corrupto o vacío.")
                    config = {}

            config['bwname'] = browser_name
            config['bwcommand'] = browser_command

            # Guardar la configuración actualizada
            try:
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)  
                print(f"Configuración guardada: {config}")
            except Exception as e:
                print(f"Error al guardar la configuración: {e}")

            self.accept()

    def save_browser(self):
        selected_browser = self.browser_combo_box.currentText()
        selected_command = self.browser_combo_box.currentData()

        # Guardar en config.json
        config_path = os.path.expanduser('~/.webapps-creator-ui/config.json')
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        config['bwname'] = selected_browser
        with open(config_path, 'w') as f:
            json.dump(config, f)

        self.accept()

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

        self.dragging = False 

        self.setWindowFlags(Qt.FramelessWindowHint)  

        if not self.config.get('language'):
            self.first_time_setup()

        # Cargar la traducción
        self.translator = QTranslator(self)
        if self.config.get('language'):
            lang = self.config['language']
        else:
            lang = QLocale.system().name()

        if self.translator.load("/usr/share/webapps-creator-ui/languages/lg_" + lang):
            QApplication.instance().installTranslator(self.translator)

        self.init_ui()
        self.load_webapps_from_log()

    def load_config(self):
        self.config_path = CONFIG_FILE
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            except json.JSONDecodeError:
                print("Error: El archivo config.json está corrupto o vacío.")
                self.config = {'bwname': 'WebApps Browser', 'bwcommand': 'python3 /usr/share/webapps-creator-ui/webapps-creator-ui-wb.py'}
        else:
            self.config = {'bwname': 'WebApps Browser', 'bwcommand': 'python3 /usr/share/webapps-creator-ui/webapps-creator-ui-wb.py'}

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

        # Crear la barra de título
        self.create_custom_title_bar()

        self.central_widget = QWidget()
        main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.create_page = QWidget()
        create_layout = QVBoxLayout(self.create_page)

        icon_and_fields_widget = QWidget()
        icon_and_fields_layout = QHBoxLayout(icon_and_fields_widget)
        icon_and_fields_layout.setContentsMargins(0, 0, 0, 0)
        icon_and_fields_layout.setSpacing(10)

        self.icon_widget = IconWidget(self) 
        self.icon_widget.setFixedSize(100, 100)
        self.icon_widget.setMouseTracking(True)
        self.icon_widget.setFocusPolicy(Qt.StrongFocus)
        icon_and_fields_layout.addWidget(self.icon_widget)

        fields_widget = QWidget()
        fields_layout = QVBoxLayout(fields_widget)
        fields_layout.setContentsMargins(0, 0, 0, 0)
        fields_layout.setSpacing(10)

        self.app_name_label = QLabel(self.tr("Nombre para la WebApp:"))
        fields_layout.addWidget(self.app_name_label)

        self.app_name_input = QLineEdit()
        self.app_name_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #333;
                color: #BEBEBE;
            }
        """)
        fields_layout.addWidget(self.app_name_input)

        self.app_url_label = QLabel(self.tr("URL (formato https://):"))
        fields_layout.addWidget(self.app_url_label)

        self.app_url_input = QLineEdit()
        self.app_url_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #333;
                color: #BEBEBE;
            }
        """)
        fields_layout.addWidget(self.app_url_input)

        icon_and_fields_layout.addWidget(fields_widget)
        create_layout.addWidget(icon_and_fields_widget)

        self.category_label = QLabel(self.tr("Categoría a usar:"))
        create_layout.addWidget(self.category_label)

        self.category_combo_box = QComboBox()
        categories = ["Network", "Development", "Education", "Game", "Graphics", "Application", "Utility", "Video", "Audio", "AudioVideo", "Office", "System", "Utility", "Science"]
        self.category_combo_box.addItems(categories)
        self.category_combo_box.setCurrentIndex(0)
        self.category_combo_box.setStyleSheet("""
            QComboBox {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #333;
                color: #BEBEBE;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        create_layout.addWidget(self.category_combo_box)

        # Añadir el texto "Navegador seleccionado:"
        self.browser_selected_label = QLabel(self.tr("Navegador a usar:"))
        self.browser_selected_label.setStyleSheet("""
            QLabel {
                color: #BEBEBE;
                font-size: 14px;
            }
        """)
        create_layout.addWidget(self.browser_selected_label)

        # Crear el botón de selección de navegador
        self.browser_button = QPushButton(self.config.get('bwname', 'WebApps Browser'))
        self.browser_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #444;
                color:rgb(190, 190, 190);
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.browser_button.clicked.connect(self.open_browser_selection_window)
        create_layout.addWidget(self.browser_button)

        self.create_button = QPushButton(self.tr("Crear WebApp"))
        self.create_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #444;
                color: #BEBEBE;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.create_button.clicked.connect(self.create_webapp)
        create_layout.addWidget(self.create_button)

        self.create_page.setLayout(create_layout)
        self.stacked_widget.addWidget(self.create_page)

        # Página de lista
        self.list_page = QWidget()
        list_layout = QVBoxLayout(self.list_page)

        self.webapp_list = QListWidget()
        self.webapp_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #333;
                color: #BEBEBE;
            }
        """)
        list_layout.addWidget(self.webapp_list)

        self.list_page.setLayout(list_layout)
        self.stacked_widget.addWidget(self.list_page)

    def open_browser_selection_window(self):
        # Abrir la ventana de selección de navegador
        window = BrowserSelectionWindow(self)
        if window.exec_() == QDialog.Accepted:
            # Actualizar el texto del botón con el nuevo navegador seleccionado
            self.load_config()
            self.browser_button.setText(self.config.get('bwname', 'WebApps Browser'))

    def create_custom_title_bar(self):
        self.title_bar = QWidget(self)
        self.title_bar.setFixedHeight(40)  
        self.title_bar.setObjectName("title_bar") 
        self.title_bar.setStyleSheet("background-color: #262626; border-bottom: 1px solid #333333;")

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(0)

        celeste_color = QColor(0, 184, 255)

        create_icon = QIcon("/usr/share/webapps-creator-ui/icons/add.png")  
        list_icon = QIcon("/usr/share/webapps-creator-ui/icons/list.png")  
        help_icon = QIcon("/usr/share/webapps-creator-ui/icons/help.png")  
        about_icon = QIcon("/usr/share/webapps-creator-ui/icons/about.png") 

        create_button = QPushButton()
        create_button.setIcon(create_icon)
        create_button.setIconSize(QSize(30, 30))  
        create_button.setToolTip(self.tr("Crear una nueva WebApp"))
        create_button.clicked.connect(self.show_create_page)
        create_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
        """)

        list_button = QPushButton()
        list_button.setIcon(list_icon)
        list_button.setIconSize(QSize(30, 30))  
        list_button.setToolTip(self.tr("Listar WebApps existentes"))
        list_button.clicked.connect(self.show_list_page)
        list_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
        """)

        help_button = QPushButton()
        help_button.setIcon(help_icon)
        help_button.setIconSize(QSize(30, 30))  
        help_button.setToolTip(self.tr("Ver la ayuda del programa"))
        help_button.clicked.connect(self.show_help)
        help_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
        """)

        about_button = QPushButton()
        about_button.setIcon(about_icon)
        about_button.setIconSize(QSize(30, 30))  
        about_button.setToolTip(self.tr("Acerca de WebApps Creator UI"))
        about_button.clicked.connect(self.show_about)
        about_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
        """)

        minimize_button = QPushButton("─")
        minimize_button.setFixedSize(40, 40)
        minimize_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #BEBEBE;
                font-size: 16px;
                border: none; /* Eliminar borde */
                border-radius: 0px; /* Eliminar bordes redondeados */
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
            QPushButton:pressed {
                background-color: #323232;
            }
        """)
        minimize_button.clicked.connect(self.showMinimized)

        close_button = QPushButton("✕")
        close_button.setFixedSize(40, 40)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #BEBEBE;
                font-size: 16px;
                border: none; /* Eliminar borde */
                border-radius: 0px; /* Eliminar bordes redondeados */
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
            QPushButton:pressed {
                background-color: #323232;
            }
        """)
        close_button.clicked.connect(self.close)

        title_layout.addWidget(create_button)
        title_layout.addWidget(list_button)
        title_layout.addStretch()
        title_layout.addWidget(help_button)
        title_layout.addWidget(about_button)
        title_layout.addWidget(minimize_button)
        title_layout.addWidget(close_button)

        self.setMenuWidget(self.title_bar)

    def get_stylesheet(self):
        """Devuelve una hoja de estilo QSS que imita el estilo Deepin."""
        return """
            QMainWindow {
                background-color: #252525;
                color: #BEBEBE;
                font-family: "Noto Sans Mono";
                font-size: 13px;
            }
            QLabel {
                color: #BEBEBE;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #2D2D2D;
                color: #BEBEBE;
                border: 1px solid #444444;
                border-radius: 8px;
                padding: 8px;
                selection-background-color: #0081FF;
                selection-color: #FFFFFF;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #0081FF;
            }
            QPushButton {
                background-color: #3A3A3A;
                color: #BEBEBE;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
            QPushButton:pressed {
                background-color: #0081FF;
            }
            QComboBox::drop-down {
                border: none;
            }
            QTextEdit {
                background-color: #2D2D2D;
                color: #BEBEBE;
                border-radius: 8px;
            }
            #title_bar {
                background-color: #262626;
                border-bottom: 1px solid #333333;
            }
            #main_content {
                border-top: 1px solid #444444;
            }
            #shadow_frame {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #333333, stop: 0.5 #444444, stop: 1 #333333);
                height: 10px;
            }
        """

    def load_webapps_from_log(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as log_file:
                desktop_files = log_file.readlines()

            for desktop_file in desktop_files:
                desktop_file = desktop_file.strip()

                config = configparser.ConfigParser()
                config.read(desktop_file)

                app_name = config.get("Desktop Entry", "Name", fallback="Unknown")
                icon_path = config.get("Desktop Entry", "Icon", fallback=None)

                item = QListWidgetItem()
                item.setData(Qt.UserRole, desktop_file)

                if icon_path and os.path.exists(icon_path):
                    item.setIcon(QIcon(icon_path))
                    self.icon_widget.set_icon(icon_path)  

                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(5, 5, 5, 5)  
                layout.setSpacing(10)  

                label = QLabel(app_name)
                label.setStyleSheet("""
                    QLabel {
                        color: #BEBEBE;
                        font-size: 14px;
                    }
                """)
                layout.addWidget(label, stretch=1)  

                delete_button = QPushButton()
                delete_button.setIcon(QIcon("/usr/share/webapps-creator-ui/icons/delete.png"))
                delete_button.setIconSize(QSize(16, 16))  
                delete_button.setFixedSize(30, 30)  
                delete_button.setToolTip(self.tr("Eliminar WebApp"))
                delete_button.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        padding: 5px;
                    }
                    QPushButton:hover {
                        background-color: #4A4A4A;
                    }
                """)
                delete_button.clicked.connect(lambda _, item=item: self.delete_webapp(item))
                layout.addWidget(delete_button)

                widget.setLayout(layout)
                item.setSizeHint(widget.sizeHint())

                self.webapp_list.addItem(item)
                self.webapp_list.setItemWidget(item, widget)

    def create_webapp(self):
        app_name = self.app_name_input.text()
        app_category = self.category_combo_box.currentText()
        app_url = self.app_url_input.text()
        app_icon = self.icon_widget.selected_icon_path  

        # Obtener el comando del navegador desde config.json
        browser_exec = self.config.get('bwcommand', 'python3 /usr/share/webapps-creator-ui/webapps-creator-ui-wb.py')

        if not app_name or not app_url or not app_icon:
            QMessageBox.warning(self, self.tr("Campos faltantes"), self.tr("Por favor, asegúrese de ingresar el nombre, la URL y seleccionar un ícono para la WebApp."))
            return

        # Añadir la URL al comando del navegador
        browser_exec = f"{browser_exec}{app_url}"

        # Crear el archivo .desktop
        config = configparser.ConfigParser()
        config.optionxform = str
        config["Desktop Entry"] = {
            "Type": "Application",
            "Name": app_name + " (Wa)",
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

        QMessageBox.information(self, self.tr("WebApp creada con éxito"), self.tr("WebApp creada y guardada en {0}").format(desktop_file_path))

        # Registrar la WebApp en el archivo de log
        with open(LOG_FILE, "a") as log_file:
            log_file.write(desktop_file_path + "\n")

        # Añadir la WebApp a la lista
        item = QListWidgetItem()
        item.setData(Qt.UserRole, desktop_file_path)

        if app_icon and os.path.exists(app_icon):
            item.setIcon(QIcon(app_icon))

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)  
        layout.setSpacing(10)  

        label = QLabel(app_name)
        label.setStyleSheet("""
            QLabel {
                color: #BEBEBE;
                font-size: 14px;
            }
        """)
        layout.addWidget(label, stretch=1)  

        delete_button = QPushButton()
        delete_button.setIcon(QIcon("/usr/share/webapps-creator-ui/icons/delete.png"))
        delete_button.setIconSize(QSize(16, 16))  
        delete_button.setFixedSize(30, 30)  
        delete_button.setToolTip(self.tr("Eliminar WebApp"))
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
        """)
        delete_button.clicked.connect(lambda _, item=item: self.delete_webapp(item))
        layout.addWidget(delete_button)

        widget.setLayout(layout)
        item.setSizeHint(widget.sizeHint())

        self.webapp_list.addItem(item)
        self.webapp_list.setItemWidget(item, widget)

    def show_create_page(self):
        self.stacked_widget.setCurrentWidget(self.create_page)

    def show_list_page(self):
        self.stacked_widget.setCurrentWidget(self.list_page)

    def delete_webapp(self, item):
        desktop_file_path = item.data(Qt.UserRole)

        if os.path.exists(desktop_file_path):
            os.remove(desktop_file_path)

            with open(LOG_FILE, "r") as log_file:
                lines = log_file.readlines()
            with open(LOG_FILE, "w") as log_file:
                for line in lines:
                    if line.strip() != desktop_file_path:
                        log_file.write(line)

            self.webapp_list.takeItem(self.webapp_list.row(item))
            QMessageBox.information(self, "WebApp eliminada", "WebApp eliminada con éxito")
        else:
            QMessageBox.warning(self, "Error al eliminar", "No se pudo encontrar el archivo .desktop para eliminar.")

    def show_help(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("WebApps Creator UI - Ayuda"))
        dialog.setFixedSize(400, 300)  
        dialog.setStyleSheet(self.get_stylesheet()) 

        layout = QVBoxLayout(dialog)

        text_browser = QTextBrowser()
        text_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #333;
                color: #BEBEBE;
                font-size: 14px;
            }
            a {
                color: #0081FF;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        """)
        text_browser.setOpenExternalLinks(True)

        help_text = f"""
        <h2>{self.tr('Como usar el programa:')}</h2>

        <h3>1. {self.tr('Crear una WebApp:')}</h3>
        <ul>
        <li>{self.tr('Ingresa el nombre de la WebApp en su respectivo apartado.')}</li>
        <li>{self.tr('Proporciona la URL completa (asegúrate de que comience con "https://").')}</li>
        <li>{self.tr('Selecciona un ícono para tu WebApp haciendo click sobre el icono actual mostrado en ventana,')}</li>
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
        <li>{self.tr('Haz clic en el boton al lado del nombre de la WebApp para eliminarla.')}</li>
        <li>{self.tr('Se eliminará el acceso directo de la WebApp.')}</li>
        </ul>
        """
        text_browser.setHtml(help_text)
        layout.addWidget(text_browser)

        close_button = QPushButton(self.tr("Cerrar"))
        close_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #444;
                color: #BEBEBE;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def show_about(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Acerca de Webapps Creator UI"))
        dialog.setFixedSize(400, 200)  
        dialog.setStyleSheet(self.get_stylesheet())  

        layout = QVBoxLayout(dialog)

        text_browser = QTextBrowser()
        text_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #333;
                color: #BEBEBE;
                font-size: 14px;
            }
            a {
                color: #0081FF;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        """)
        text_browser.setOpenExternalLinks(True)

        about_text = self.tr(
            "Webapps Creator UI v1.5.4\n"
            "Desarrollado por krafairus - Equipo Deepines\n"
            "Más información en:\n"
            "https://github.com/deepin-espanol/webapps-creator-ui"
        )
        text_browser.setPlainText(about_text)
        layout.addWidget(text_browser)

        close_button = QPushButton(self.tr("Cerrar"))
        close_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #444;
                color: #BEBEBE;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.dragging = True
            self.offset = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()

class IconWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.selected_icon_path = None  

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(100, 100)  
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 5px;
            }
            QLabel:hover {
                background-color: #444;
            }
        """)
        self.layout.addWidget(self.icon_label)

        default_icon_path = "/usr/share/webapps-creator-ui/icons/dafault.png"  
        if os.path.exists(default_icon_path):
            self.set_icon(default_icon_path)
        else:
            print(f"Advertencia: No se encontró el ícono predeterminado en {default_icon_path}")

        self.setLayout(self.layout)

    def set_icon(self, icon_path):
        if icon_path and os.path.exists(icon_path):
            self.icon_label.setPixmap(QIcon(icon_path).pixmap(64, 64))
            self.selected_icon_path = icon_path  
        else:
            self.icon_label.clear()
            self.selected_icon_path = None 

    def select_icon(self):
        print("Método select_icon llamado") 
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
            self.set_icon(file_name)  
            self.selected_icon_path = file_name  

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            print("Clic en IconWidget detectado")  
            self.select_icon() 

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget {
            color: #BEBEBE;
            background-color: #262626;
        }
    """)
    creator = WebAppCreator()
    creator.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()