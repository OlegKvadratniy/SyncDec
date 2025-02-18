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
    try:
        # Инициализация curses для сервера
        stdscr = curses.initscr()
        curses.curs_set(0)  # Скрыть реальный курсор
        stdscr.nodelay(1)  # Неблокирующий ввод
        stdscr.timeout(100)  # Таймаут для обновления

        # Положение курсора сервера
        server_cursor = [5, 5]

        while True:
            # Обработка ввода с клавиатуры
            try:
                key = stdscr.getch()
                if key == curses.KEY_LEFT:
                    server_cursor[1] -= 1
                elif key == curses.KEY_RIGHT:
                    server_cursor[1] += 1
                elif key == curses.KEY_UP:
                    server_cursor[0] -= 1
                elif key == curses.KEY_DOWN:
                    server_cursor[0] += 1
                elif key == ord("q"):
                    break
            except:
                pass

            # Получение данных от клиента
            try:
                data = client_socket.recv(1024)
                if not data:
                    break

                message = data.decode("utf-8")
                if message.startswith("CURSOR;"):
                    parts = message.split(";")
                    if len(parts) == 3:
                        client_cursor = [int(parts[1]), int(parts[2])]
                        # Обновление экрана
                        stdscr.clear()
                        stdscr.addstr(server_cursor[0], server_cursor[1], "S")
                        stdscr.addstr(client_cursor[0], client_cursor[1], "C")
                        stdscr.refresh()

                    # Отправка положения курсора сервера клиенту
                    cursor_info = f"CURSOR;{server_cursor[0]};{server_cursor[1]}"
                    client_socket.sendall(cursor_info.encode("utf-8"))

                else:
                    # Эхо-ответ для других сообщений
                    client_socket.sendall(f"Сервер получил: {message}".encode("utf-8"))

            except Exception as e:
                print(f"{RED}[TCP] Ошибка с клиентом {addr}: {e}{RESET}")
                break

    except Exception as e:
        print(f"{RED}[TCP] Ошибка с клиентом {addr}: {e}{RESET}")
    finally:
        client_socket.close()
        curses.endwin()
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
