import sys
import time  # Добавлен импорт модуля time
from PyQt5 import QtWidgets
from gui import ModeSelectionWindow, ServerWindow, ClientWindow
from network import Server, Client
import pyautogui
import threading


class App(QtWidgets.QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)

        self.mode_selection_window = ModeSelectionWindow()
        self.mode_selection_window.show()
        self.mode_selection_window.server_button.clicked.connect(self.start_server_mode)
        self.mode_selection_window.client_button.clicked.connect(self.start_client_mode)

        self.server_window = None
        self.client_window = None
        self.server = None
        self.client = None

    def start_server_mode(self):
        self.server_window = ServerWindow()
        self.server = Server()

        self.server.client_connected.connect(self.on_client_connected)
        self.server.message_received.connect(self.on_server_message_received)

        self.server.start_server()

        self.mode_selection_window.close()
        self.server_window.show()

    def start_client_mode(self):
        self.client_window = ClientWindow()
        self.client = Client()

        self.client.connected.connect(self.on_client_connected_to_server)
        self.client.message_received.connect(self.on_client_message_received)
        self.client.error_occurred.connect(self.on_client_error)

        self.client_window.connect_button.clicked.connect(self.manual_connect_to_server)

        self.client.start_broadcast_listener()

        self.mode_selection_window.close()
        self.client_window.show()

        self.start_sending_cursor_position()

    def manual_connect_to_server(self):
        ip = self.client_window.ip_input.text()
        if ip:
            self.client.connect_to_server(ip)

    def on_client_connected(self, client_socket):
        self.server_window.info_label.setText("Клиент подключен.")
        self.server.send_data("Привет от сервера!")

    def on_server_message_received(self, message):
        print(f"Сервер получил сообщение: {message}")

    def on_client_connected_to_server(self):
        self.client_window.info_label.setText("Подключено к серверу.")
        self.client.send_data("Привет от клиента!")

    def on_client_message_received(self, message):
        print(f"Клиент получил сообщение: {message}")

    def on_client_error(self, error_message):
        self.client_window.info_label.setText(f"Ошибка: {error_message}")

    def start_sending_cursor_position(self):
        def send_cursor_position():
            while True:
                x, y = pyautogui.position()
                self.client.send_data(x, y)
                time.sleep(0.1)

        threading.Thread(target=send_cursor_position, daemon=True).start()


if __name__ == "__main__":
    app = App(sys.argv)
    sys.exit(app.exec_())
