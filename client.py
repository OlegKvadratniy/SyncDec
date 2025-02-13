#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Клиент:
1. Отправляет UDP broadcast с запросом обнаружения серверов.
2. Собирает ответы и выводит список найденных серверов.
3. После выбора сервера устанавливает TCP-соединение для обмена сообщениями.
"""

import socket
import time


def discover_servers(udp_port=50000, timeout=3):
    """
    Отправляет UDP broadcast с запросом "DISCOVER_REQUEST" и ожидает ответов.
    Формат ответа: "SERVER_RESPONSE;{server_name};{tcp_port}"
    Возвращает список кортежей (server_name, server_ip, tcp_port).
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.settimeout(timeout)

    message = "DISCOVER_REQUEST"
    broadcast_address = ("192.168.1.8", udp_port)

    try:
        udp_socket.sendto(message.encode("utf-8"), broadcast_address)
    except Exception as e:
        print(f"[UDP] Ошибка отправки broadcast: {e}")
        return []

    servers = []
    start_time = time.time()
    print("Ожидаем ответы от серверов...")
    while True:
        try:
            data, addr = udp_socket.recvfrom(1024)
            message = data.decode("utf-8")
            if message.startswith("SERVER_RESPONSE;"):
                parts = message.split(";")
                if len(parts) >= 3:
                    server_name = parts[1]
                    tcp_port = int(parts[2])
                    servers.append((server_name, addr[0], tcp_port))
                    print(
                        f"Получен ответ от {addr[0]}: {server_name} (TCP порт: {tcp_port})"
                    )
        except socket.timeout:
            break
        if time.time() - start_time > timeout:
            break
    return servers


def tcp_client(server_ip, tcp_port):
    """Подключение по TCP к выбранному серверу и обмен сообщениями (эхо-режим)"""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, tcp_port))
        print(f"[TCP] Подключено к серверу {server_ip}:{tcp_port}")
    except Exception as e:
        print(f"[TCP] Ошибка подключения: {e}")
        return

    try:
        while True:
            message = input("Введите сообщение (или 'exit' для выхода): ")
            if message.lower() == "exit":
                break
            client_socket.sendall(message.encode("utf-8"))
            data = client_socket.recv(1024)
            if not data:
                print("Сервер разорвал соединение.")
                break
            print("Ответ сервера:", data.decode("utf-8"))
    except Exception as e:
        print(f"[TCP] Ошибка во время обмена: {e}")
    finally:
        client_socket.close()
        print("[TCP] Соединение закрыто.")


if __name__ == "__main__":
    print("Поиск серверов в локальной сети...")
    servers = discover_servers()
    if not servers:
        print("Серверы не найдены.")
        exit(0)
    print("\nНайдены серверы:")
    for idx, (name, ip, port) in enumerate(servers):
        print(f"{idx}: {name} ({ip}:{port})")

    try:
        choice = int(input("Выберите номер сервера для подключения: "))
        if choice < 0 or choice >= len(servers):
            raise ValueError
    except ValueError:
        print("Неверный выбор.")
        exit(0)

    selected_server = servers[choice]
    tcp_client(selected_server[1], selected_server[2])
