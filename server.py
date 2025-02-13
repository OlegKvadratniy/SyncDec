#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Серверная часть для создания сетевого соединения между устройствами в одной Wi-Fi сети.
Сервер принимает подключения, получает сообщения от клиента и отправляет их обратно.
"""

import socket

# Настройки сервера
HOST = ""  # '' означает, что сервер слушает все доступные сетевые интерфейсы
PORT = 12345  # Порт, который будет использовать сервер

# Создание TCP сокета
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Привязка сокета к адресу и порту
server_socket.bind((HOST, PORT))

# Прослушивание входящих подключений (максимум 5 в очереди)
server_socket.listen(5)
print("Сервер запущен. Ожидание подключения клиентов...")

try:
    while True:
        # Принятие входящего соединения
        client_socket, client_address = server_socket.accept()
        print("Подключен клиент:", client_address)

        # Работа с клиентом
        while True:
            data = client_socket.recv(1024)  # Получение данных (до 1024 байт)
            if not data:
                break
            print("Получено сообщение:", data.decode("utf-8"))
            # Отправка полученных данных обратно клиенту (эхо)
            client_socket.sendall(data)
        client_socket.close()
        print("Клиент отключился.")
except KeyboardInterrupt:
    print("\nСервер остановлен вручную.")
finally:
    server_socket.close()
