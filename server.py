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


import socket
import threading
import curses
import time


def handle_client(client_socket, addr):
    """Обработка подключения по TCP (простой эхо-сервер)"""
    print(f"[TCP] Клиент {addr} подключился.")
    try:
        # Инициализация curses
        stdscr = curses.initscr()
        curses.curs_set(0)  # Скрыть реальный курсор
        stdscr.nodelay(1)  # Неблокирующий ввод
        stdscr.timeout(100)  # Таймаут для обновления

        # Положение курсора сервера
        server_cursor = [0, 0]

        while True:
            try:
                # Обработка ввода
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
                data = client_socket.recv(1024)
                if data:
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

                    # Отправка положения курсора сервера
                    cursor_info = f"CURSOR;{server_cursor[0]};{server_cursor[1]}"
                    client_socket.sendall(cursor_info.encode("utf-8"))

            except Exception as e:
                print(f"[TCP] Ошибка с клиентом {addr}: {e}")
                break

    except Exception as e:
        print(f"[TCP] Ошибка с клиентом {addr}: {e}")
    finally:
        client_socket.close()
        curses.endwin()
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


if __name__ == "__main__":
    # Запрос названия сервера у пользователя
    server_name = input("Введите название сервера: ")
    tcp_port = 12345  # фиксированный TCP-порт, можно сделать вводным
    host = ""  # '' означает прослушивание на всех интерфейсах

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
