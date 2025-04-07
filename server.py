#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сервер:
1. При запуске запрашивает название сервера.
2. Запускает TCP-сервер для обмена сообщениями и информацией о курсоре.
3. Запускает UDP-сервер для ответа на запросы обнаружения.
"""

import socket
import threading
import sys
import curses
import pyautogui
import time

# Цветовые коды ANSI для красивых надписей
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Цвета текста
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"


def handle_client(client_socket, addr):
    """Обработка подключения по TCP (обмен сообщениями и информацией о курсоре)"""
    print(f"{GREEN}[TCP] Клиент {addr} подключился.{RESET}")
    server_side = "не указано"
    screen_width, screen_height = pyautogui.size()
    client_connected = True

    def track_server_cursor():
        """Отслеживает курсор сервера и отправляет события клиенту только для активного края."""
        nonlocal client_connected
        while client_connected:
            try:
                x, y = pyautogui.position()
                # Активный край зависит от положения клиента (обратно server_side)
                if (
                    server_side == "слева" and x >= screen_width - 1
                ):  # Клиент справа → уходим вправо
                    client_socket.sendall(f"CURSOR_EXIT;right;{y}".encode("utf-8"))
                    pyautogui.moveTo(screen_width - 2, y)
                elif server_side == "справа" and x <= 0:  # Клиент слева → уходим влево
                    client_socket.sendall(f"CURSOR_EXIT;left;{y}".encode("utf-8"))
                    pyautogui.moveTo(1, y)
                elif (
                    server_side == "спереди" and y >= screen_height - 1
                ):  # Клиент сзади → уходим вниз
                    client_socket.sendall(f"CURSOR_EXIT;bottom;{x}".encode("utf-8"))
                    pyautogui.moveTo(x, screen_height - 2)
                elif server_side == "сзади" and y <= 0:  # Клиент спереди → уходим вверх
                    client_socket.sendall(f"CURSOR_EXIT;top;{x}".encode("utf-8"))
                    pyautogui.moveTo(x, 1)
                time.sleep(0.01)
            except (OSError, ConnectionError):
                client_connected = False
                break

    try:
        cursor_thread = threading.Thread(target=track_server_cursor, daemon=True)
        cursor_thread.start()

        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break

                message = data.decode("utf-8")
                if message.startswith("CURSOR_EXIT;"):
                    parts = message.split(";")
                    if len(parts) == 3:
                        direction = parts[1]
                        coord = int(parts[2])
                        # Перенос курсора с клиента на сервер
                        if server_side == "слева" and direction == "left":
                            pyautogui.moveTo(
                                screen_width - 1, coord
                            )  # Появляется справа
                        elif server_side == "справа" and direction == "right":
                            pyautogui.moveTo(0, coord)  # Появляется слева
                        elif server_side == "спереди" and direction == "top":
                            pyautogui.moveTo(
                                coord, screen_height - 1
                            )  # Появляется снизу
                        elif server_side == "сзади" and direction == "bottom":
                            pyautogui.moveTo(coord, 0)  # Появляется сверху

                elif message.startswith("SERVER_SIDE;"):
                    parts = message.split(";")
                    if len(parts) == 2:
                        server_side = parts[1]
                        print(
                            f"{MAGENTA}[INFO] Клиент указал сторону сервера: {server_side}{RESET}"
                        )

                else:
                    client_socket.sendall(f"Сервер получил: {message}".encode("utf-8"))

            except Exception as e:
                print(f"{RED}[TCP] Ошибка с клиентом {addr}: {e}{RESET}")
                break

    except Exception as e:
        print(f"{RED}[TCP] Ошибка с клиентом {addr}: {e}{RESET}")
    finally:
        client_connected = False
        client_socket.close()
        print(f"{YELLOW}[TCP] Клиент {addr} отключился.{RESET}")


def tcp_server(host, port):
    """Запускаем TCP-сервер для обмена сообщениями и информацией о курсоре"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(
            f"{CYAN}[TCP] Сервер слушает на {host if host else '0.0.0.0'}:{port}{RESET}"
        )
    except Exception as e:
        print(f"{RED}[TCP] Не удалось запустить сервер: {e}{RESET}")
        sys.exit(1)

    while True:
        client_socket, addr = server_socket.accept()
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket, addr)
        )
        client_thread.start()


def udp_discovery(server_name, tcp_port, udp_port=50000):
    """UDP-сервер для обнаружения.
    При получении сообщения "DISCOVER_REQUEST" отвечает сообщением:
    "SERVER_RESPONSE;{server_name};{tcp_port}"
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp_socket.bind(("", udp_port))
        print(f"{CYAN}[UDP] Discovery сервер слушает на порту {udp_port}{RESET}")
    except Exception as e:
        print(f"{RED}[UDP] Ошибка при запуске UDP сервера: {e}{RESET}")
        sys.exit(1)

    while True:
        try:
            data, addr = udp_socket.recvfrom(1024)
            message = data.decode("utf-8")
            if message.strip() == "DISCOVER_REQUEST":
                response = f"SERVER_RESPONSE;{server_name};{tcp_port}"
                udp_socket.sendto(response.encode("utf-8"), addr)
                print(f"{GREEN}[UDP] Ответил на запрос обнаружения от {addr}{RESET}")
        except Exception as e:
            print(f"{YELLOW}[UDP] Ошибка: {e}{RESET}")


if __name__ == "__main__":
    # Запрос названия сервера у пользователя
    print(f"{BOLD}🚀 Запуск сервера...{RESET}")
    server_name = input(f"{MAGENTA}Введите название сервера: {RESET}")
    tcp_port = 12345  # Можно сделать вводным, если необходимо
    host = ""  # '' означает прослушивание на всех интерфейсах

    # Запуск UDP discovery сервера в отдельном потоке
    udp_thread = threading.Thread(
        target=udp_discovery, args=(server_name, tcp_port), daemon=True
    )
    udp_thread.start()

    # Запуск TCP-сервера в отдельном потоке
    tcp_thread = threading.Thread(target=tcp_server, args=(host, tcp_port), daemon=True)
    tcp_thread.start()

    print(f"{GREEN}Сервер '{server_name}' запущен успешно!{RESET}")
    print(f"{BLUE}Для остановки сервера нажмите Ctrl+C.{RESET}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}👋 Сервер остановлен.{RESET}")
        sys.exit(0)
