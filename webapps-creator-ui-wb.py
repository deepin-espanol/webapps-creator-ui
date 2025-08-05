#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QListWidget, QDialog, QHBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtGui import QIcon, QColor, QPainter
from PyQt5.QtCore import QUrl, Qt, QSize
from PyQt5.QtDBus import QDBusInterface

CONFIG_DIR = os.path.expanduser("~/.wbrowserconfig")
CONFIG_FILE = os.path.join(CONFIG_DIR, "downloads.json")

class SimpleBrowser(QMainWindow): 
    def __init__(self, url, icon_path=None):
        super().__init__()
        self.url = url
        self.icon_path = icon_path
        self.initUI()
        self.load_start_url()

    def initUI(self):

        self.setWindowFlags(Qt.FramelessWindowHint) 

        layout = QVBoxLayout()

        self.browser = QWebEngineView()

        profile = self.browser.page().profile()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.48 Safari/537.36"
        profile.setHttpUserAgent(user_agent)

        if self.icon_path:
            self.setWindowIcon(QIcon(self.icon_path))
        else:
            self.browser.iconChanged.connect(self.update_window_icon)

        # Crear la barra de título personalizada
        self.create_custom_title_bar()

        self.central_widget = QWidget()
        main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        main_layout.addWidget(self.browser)

        self.setLayout(layout)

        self.browser.titleChanged.connect(self.update_window_title)
        self.browser.page().profile().downloadRequested.connect(self.download_requested)

        self.setWindowTitle('WebApp Browser')
        self.setGeometry(300, 300, 1000, 600)

    def load_start_url(self):
        self.browser.setUrl(QUrl(self.url))

    def update_window_title(self, title):
        self.setWindowTitle(title)

    def update_window_icon(self, icon):
        self.setWindowIcon(icon)

    def download_requested(self, download):
        download_path, _ = QFileDialog.getSaveFileName(self, "Save File", download.path())
        if download_path:
            download.setPath(download_path)
            download.accept()
            file_name = download_path.split('/')[-1]
            self.send_notification("Descarga Completa", f"Se descargó '{file_name}'")
            self.save_download(file_name, download_path)

    def send_notification(self, title, message):
        bus = QDBusInterface("org.kde.knotify", "/Notify", "org.kde.KNotify")
        bus.call("event", "notification", ["info", "kde", [], title, message, [], [], 0, 0, 0])

    def save_download(self, file_name, download_path):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)

        downloads = []
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                downloads = json.load(f)

        downloads.append({"file_name": file_name, "download_path": download_path})

        with open(CONFIG_FILE, "w") as f:
            json.dump(downloads, f)

    def show_download_history(self):
        self.dialog = QDialog(self)
        self.dialog.setWindowTitle("Historial de Descargas")
        
        self.dialog.setStyleSheet("""
            QDialog {
                background-color: #2E2E2E;
                color: #FFFFFF;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QListWidget {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #333;
                color: #BEBEBE;
            }
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
            QPushButton:pressed {
                background-color: #3A3A3A;
            }
            QPushButton:disabled {
                background-color: #2A2A2A;
                color: #777777;
            }
        """)
        
        self.dialog.resize(500, 300)
        
        self.layout = QVBoxLayout()
        
        self.download_list = QListWidget()
        self.load_download_history()
        
        button_layout = QHBoxLayout()
        
        self.btnOpenFolder = QPushButton(QIcon("/usr/share/webapps-creator-ui/icons/folder.png"), "Carpeta", self)
        self.btnOpenFolder.clicked.connect(lambda: self.open_selected_download_folder(self.download_list.currentRow(), self.downloads))
        self.btnOpenFolder.setEnabled(False)
        
        self.btnDelete = QPushButton(QIcon("/usr/share/webapps-creator-ui/icons/trash.png"), "Borrar Historial", self)
        self.btnDelete.clicked.connect(self.confirm_delete_download_history)
        
        self.download_list.itemSelectionChanged.connect(lambda: self.btnOpenFolder.setEnabled(self.download_list.currentRow() >= 0))
        
        self.download_list.itemDoubleClicked.connect(lambda item: self.open_selected_download(self.download_list.currentRow(), self.downloads))
        
        button_layout.addWidget(self.btnOpenFolder)
        button_layout.addWidget(self.btnDelete)
        
        self.layout.addWidget(self.download_list)
        self.layout.addLayout(button_layout)
        
        self.dialog.setLayout(self.layout)
        self.dialog.exec()
    
    def load_download_history(self):
        self.downloads = []
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                self.downloads = json.load(f)
        
        self.download_list.clear()
        for download in self.downloads:
            item = download["file_name"]
            self.download_list.addItem(item)
    
    def open_selected_download(self, index, downloads):
        if index >= 0 and index < len(downloads):
            download_path = downloads[index]["download_path"]
            if os.path.exists(download_path):
                os.system(f"xdg-open '{download_path}'") 

    def open_selected_download_folder(self, index, downloads):
        if index >= 0 and index < len(downloads):
            download_path = downloads[index]["download_path"]
            folder_path = os.path.dirname(download_path)
            if os.path.exists(folder_path):
                os.system(f"xdg-open '{folder_path}'") 

    def confirm_delete_download_history(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Confirmar Borrado")
        msg_box.setText("¿Estás seguro de que quieres borrar el historial de descargas?")
        
        # Cambiar los botones a "Confirmar" y "Cancelar"
        confirm_button = msg_box.addButton("Confirmar", QMessageBox.YesRole)
        confirm_button.setStyleSheet("""
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
        cancel_button = msg_box.addButton("Cancelar", QMessageBox.NoRole)
        cancel_button.setStyleSheet("""
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
        
        msg_box.setDefaultButton(cancel_button)  # Establecer "Cancelar" como botón predeterminado
        
        # Aplicar estilo CSS al QMessageBox
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2E2E2E;
                color: #FFFFFF;
            }
            QMessageBox QLabel {
                color: #FFFFFF;
            }
        """)
        
        msg_box.exec()
        
        # Verificar qué botón se presionó
        if msg_box.clickedButton() == confirm_button:  # Si se hizo clic en "Confirmar"
            self.delete_download_history()

    def delete_download_history(self):
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Mensaje de eliminacion")
            msg_box.setText("El historial de descargas ha sido borrado.")
            
            close_button = msg_box.addButton("Cerrar", QMessageBox.AcceptRole)
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
            msg_box.setDefaultButton(close_button)  
            
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #2E2E2E;
                    color: #FFFFFF;
                }
                QMessageBox QLabel {
                    color: #FFFFFF;
                }
            """)
            
            msg_box.exec()
            self.load_download_history()   

    def create_custom_title_bar(self):
        self.title_bar = QWidget(self)
        self.title_bar.setFixedHeight(40)  
        self.title_bar.setObjectName("title_bar")  
        self.title_bar.setStyleSheet("background-color: #262626; border-bottom: 1px solid #333333;")

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(0)

        celeste_color = QColor(0, 184, 255)

        home_icon = QIcon("/usr/share/webapps-creator-ui/icons/home.png") 
        download_icon = QIcon("/usr/share/webapps-creator-ui/icons/downloads.png")  
        
        self.btnInicio = QPushButton(home_icon, "", self)  
        self.btnInicio.setIconSize(QSize(32, 32))  
        self.btnInicio.clicked.connect(self.load_start_url)
        self.btnInicio.setToolTip("Inicio")
        self.btnInicio.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
        """)

        self.btnDescargas = QPushButton(download_icon, "", self)  
        self.btnDescargas.setIconSize(QSize(32, 32))  
        self.btnDescargas.clicked.connect(self.show_download_history)
        self.btnDescargas.setToolTip("Descargas")
        self.btnDescargas.setStyleSheet("""
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

        title_layout.addWidget(self.btnInicio)
        title_layout.addWidget(self.btnDescargas)
        title_layout.addStretch()
        title_layout.addWidget(minimize_button)
        title_layout.addWidget(close_button)

        self.setMenuWidget(self.title_bar) 

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

if __name__ == '__main__':
    app = QApplication(sys.argv)

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = 'https://www.example.com/'

    icon_path = sys.argv[2] if len(sys.argv) > 2 else None

    window = SimpleBrowser(url, icon_path)
    window.show()

    sys.exit(app.exec_())
