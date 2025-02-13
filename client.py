#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Клиентская часть для создания сетевого соединения между устройствами в одной Wi-Fi сети.
Клиент подключается к серверу, отправляет сообщения и получает от него ответ.
"""

import socket

# Настройки клиента
SERVER_IP = "192.168.1.8"  # Замените на IP-адрес сервера
PORT = 12345  # Должен совпадать с портом сервера

# Создание TCP сокета
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Подключение к серверу
client_socket.connect((SERVER_IP, PORT))
print("Подключено к серверу:", SERVER_IP)

try:
    while True:
        message = input("Введите сообщение (или 'exit' для выхода): ")
        if message.lower() == "exit":
            break
        # Отправка сообщения серверу
        client_socket.sendall(message.encode("utf-8"))
        # Получение ответа от сервера
        data = client_socket.recv(1024)
        print("Ответ сервера:", data.decode("utf-8"))
finally:
    client_socket.close()
    print("Отключение от сервера.")
