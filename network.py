from PyQt5.QtCore import QObject, pyqtSignal, QByteArray
from PyQt5.QtNetwork import QTcpServer, QTcpSocket, QHostAddress
import threading
import socket
import time


class Server(QObject):
    client_connected = pyqtSignal(QTcpSocket)
    message_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.server = QTcpServer()
        self.server.newConnection.connect(self.handle_new_connection)

        # Параметры для широковещательной рассылки
        self.broadcast_port = 37020  # Произвольный порт для broadcast
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
        broadcast_address = "192.168.1.255"  # Замените на ваш широковещательный адрес
        while True:
            udp_sock.sendto(
                message.encode("utf-8"), (broadcast_address, self.broadcast_port)
            )
            time.sleep(2)  # Рассылаем сообщение каждые 2 секунды

    def handle_new_connection(self):
        self.client_socket = self.server.nextPendingConnection()
        self.client_socket.readyRead.connect(self.read_data)
        self.client_connected.emit(self.client_socket)
        print("Клиент подключился")

    def read_data(self):
        data = self.client_socket.readAll()
        message = data.data().decode("utf-8")
        self.message_received.emit(message)
        print(f"Получено сообщение: {message}")

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

        # Параметры для прослушивания широковещательных сообщений
        self.broadcast_port = 37020  # Тот же порт, что и у сервера
        self.broadcast_message = "SyncServerAvailable"

    def start_broadcast_listener(self):
        # Запускаем поток для прослушивания широковещательных сообщений
        self.broadcast_listener_thread = threading.Thread(
            target=self.listen_for_server_broadcast, daemon=True
        )
        self.broadcast_listener_thread.start()

    def listen_for_server_broadcast(self):
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_sock.bind(("", self.broadcast_port))  # Прослушиваем на всех интерфейсах

        while True:
            data, addr = udp_sock.recvfrom(1024)
            message = data.decode("utf-8")
            if message.startswith(self.broadcast_message):
                # Извлекаем порт сервера из сообщения
                _, port = message.split(":")
                server_ip = addr[0]
                server_port = int(port)
                print(f"Найден сервер: {server_ip}:{server_port}")
                # Подключаемся к серверу
                self.connect_to_server(server_ip, server_port)
                break  # Останавливаем прослушивание после подключения

    def connect_to_server(self, ip, port=8765):
        self.socket.connectToHost(ip, port)

    def on_connected(self):
        self.connected.emit()
        print("Подключено к серверу")

    def read_data(self):
        data = self.socket.readAll()
        message = data.data().decode("utf-8")
        self.message_received.emit(message)
        print(f"Получено сообщение: {message}")

    def send_data(self, message):
        data = QByteArray()
        data.append(message)
        self.socket.write(data)
        print(f"Отправлено сообщение: {message}")

    def on_error(self, socket_error):
        error_message = self.socket.errorString()
        self.error_occurred.emit(error_message)
        print(f"Ошибка сокета: {error_message}")
