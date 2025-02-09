from PyQt5.QtCore import QObject, pyqtSignal, QByteArray
from PyQt5.QtNetwork import QTcpServer, QTcpSocket, QHostAddress, QAbstractSocket
import threading
import socket
import pyautogui
import json
import time


class Server(QObject):
    client_connected = pyqtSignal(QTcpSocket)
    message_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.server = QTcpServer()
        self.server.newConnection.connect(self.handle_new_connection)
        self.client_socket = None

        # Параметры для широковещательной рассылки
        self.broadcast_port = 37020
        self.broadcast_message = "SyncServerAvailable"

    def start_server(self, port=8765):
        if not self.server.listen(QHostAddress.Any, port):
            print(f"Не удалось запустить сервер: {self.server.errorString()}")
        else:
            print(f"Сервер запущен на порту {port}")
            # Запускаем поток для широковещательной рассылки
            self.broadcast_thread = threading.Thread(
                target=self.broadcast_server_presence, args=(port,), daemon=True
            )
            self.broadcast_thread.start()

    def broadcast_server_presence(self, port):
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f"{self.broadcast_message}:{port}"
        broadcast_address = "255.255.255.255"
        while True:
            udp_sock.sendto(
                message.encode("utf-8"), (broadcast_address, self.broadcast_port)
            )
            time.sleep(2)

    def handle_new_connection(self):
        self.client_socket = self.server.nextPendingConnection()
        self.client_socket.readyRead.connect(self.read_data)
        self.client_connected.emit(self.client_socket)
        print("Клиент подключился")

    def read_data(self):
        data = self.client_socket.readAll()
        message = data.data().decode("utf-8")
        self.message_received.emit(message)
        try:
            data = json.loads(message)
            if "x" in data and "y" in data:
                pyautogui.moveTo(data["x"], data["y"])
        except json.JSONDecodeError:
            print(f"Ошибка декодирования JSON: {message}")

    def send_data(self, message):
        if self.client_socket:
            data = QByteArray()
            data.append(message)
            self.client_socket.write(data)
            print(f"Отправлено сообщение: {message}")


class Client(QObject):
    connected = pyqtSignal()
    message_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.socket = QTcpSocket()
        self.socket.connected.connect(self.on_connected)
        self.socket.readyRead.connect(self.read_data)
        self.socket.errorOccurred.connect(self.on_error)
        self.is_connecting = False

        # Параметры для прослушивания широковещательных сообщений
        self.broadcast_port = 37020
        self.broadcast_message = "SyncServerAvailable"

    def start_broadcast_listener(self):
        self.broadcast_listener_thread = threading.Thread(
            target=self.listen_for_server_broadcast, daemon=True
        )
        self.broadcast_listener_thread.start()

    def listen_for_server_broadcast(self):
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_sock.bind(("", self.broadcast_port))

        while True:
            data, addr = udp_sock.recvfrom(1024)
            message = data.decode("utf-8")
            if message.startswith(self.broadcast_message):
                _, port = message.split(":")
                server_ip = addr[0]
                server_port = int(port)
                print(f"Найден сервер: {server_ip}:{server_port}")
                self.connect_to_server(server_ip, server_port)
                break

    def connect_to_server(self, ip, port=8765):
        if (
            not self.is_connecting
            and self.socket.state() != QAbstractSocket.ConnectedState
        ):
            self.is_connecting = True
            print(f"Попытка подключиться к серверу {ip}:{port}")
            self.socket.connectToHost(ip, port)
        else:
            print("Уже выполняется попытка подключения или уже подключено")

    def on_connected(self):
        self.is_connecting = False
        self.connected.emit()
        print("Подключено к серверу")

    def read_data(self):
        data = self.socket.readAll()
        message = data.data().decode("utf-8")
        self.message_received.emit(message)
        print(f"Получено сообщение: {message}")

    def send_data(self, x, y):
        data = {"x": x, "y": y}
        message = json.dumps(data)
        self.socket.write(message.encode("utf-8"))
        print(f"Отправлено сообщение: {message}")

    def on_error(self, socket_error):
        self.is_connecting = False
        error_message = self.socket.errorString()
        self.error_occurred.emit(error_message)
        print(f"Ошибка сокета: {error_message}")

        # Дополнительный вывод для отладки
        state = self.socket.state()
        print(f"Состояние сокета: {state}")
