#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сервер:
1. При запуске запрашивает название сервера.
2. Запускает TCP-сервер (например, на порту 12345) для обмена сообщениями.
3. Запускает UDP-сервер (на порту 50000) для ответа на запросы обнаружения.
"""

import socket
import threading
import sys


def handle_client(client_socket, addr):
    """Обработка подключения по TCP (простой эхо-сервер)"""
    print(f"[TCP] Клиент {addr} подключился.")
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            print(f"[TCP] Получено от {addr}: {data.decode('utf-8')}")
            client_socket.sendall(data)  # отправка обратно (эхо)
    except Exception as e:
        print(f"[TCP] Ошибка с клиентом {addr}: {e}")
    finally:
        client_socket.close()
        print(f"[TCP] Клиент {addr} отключился.")


def tcp_server(host, port):
    """Запускаем TCP-сервер для обмена сообщениями"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"[TCP] Сервер слушает на {host if host else '0.0.0.0'}:{port}")
    except Exception as e:
        print(f"[TCP] Не удалось запустить сервер: {e}")
        sys.exit(1)

    while True:
        client_socket, addr = server_socket.accept()
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket, addr)
        )
        client_thread.start()


def udp_discovery(server_name, tcp_port, udp_port=50000):
    """
    UDP-сервер для обнаружения.
    При получении сообщения "DISCOVER_REQUEST" отвечает сообщением:
    "SERVER_RESPONSE;{server_name};{tcp_port}"
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp_socket.bind(("", udp_port))
        print(f"[UDP] Discovery сервер слушает на порту {udp_port}")
    except Exception as e:
        print(f"[UDP] Ошибка при запуске UDP сервера: {e}")
        sys.exit(1)

    while True:
        try:
            data, addr = udp_socket.recvfrom(1024)
            message = data.decode("utf-8")
            if message.strip() == "DISCOVER_REQUEST":
                response = f"SERVER_RESPONSE;{server_name};{tcp_port}"
                udp_socket.sendto(response.encode("utf-8"), addr)
                print(f"[UDP] Отправлен ответ на запрос обнаружения {addr}")
        except Exception as e:
            print(f"[UDP] Ошибка: {e}")


if __name__ == "__main__":
    # Запрос названия сервера у пользователя
    server_name = input("Введите название сервера: ")
    tcp_port = 12345  # фиксированный TCP-порт, можно сделать вводным
    host = ""  # '' означает прослушивание на всех интерфейсах

    # Запуск UDP discovery сервера в отдельном потоке
    udp_thread = threading.Thread(
        target=udp_discovery, args=(server_name, tcp_port), daemon=True
    )
    udp_thread.start()

    # Запуск TCP-сервера в отдельном потоке
    tcp_thread = threading.Thread(target=tcp_server, args=(host, tcp_port), daemon=True)
    tcp_thread.start()

    print("Сервер запущен. Для выхода нажмите Ctrl+C.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
        sys.exit(0)
