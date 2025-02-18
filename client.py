#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Клиент:
1. Отправляет UDP broadcast с запросом обнаружения серверов.
2. Собирает ответы и выводит список найденных серверов.
3. После выбора сервера устанавливает TCP-соединение для обмена сообщениями.
"""

import socket
import socket
import threading
import curses
import time


def tcp_client(server_ip, tcp_port):
    """Подключение по TCP к выбранному серверу"""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.settimeout(5)
        client_socket.connect((server_ip, tcp_port))
        print(f"\n🟢 Успешно подключено к {server_ip}:{tcp_port}")

        # Блок определения расположения сервера
        valid_sides = {1: "спереди", 2: "сзади", 3: "слева", 4: "справа"}
        print("\nОпределите расположение сервера:")
        for key, value in valid_sides.items():
            print(f"{key}. {value.capitalize()}")

        while True:
            try:
                choice = int(
                    input(
                        "Выберите сторону [1.Спереди/2.Сзади/3.Слева/4.Справа]: "
                    ).strip()
                )
                if choice in valid_sides:
                    side = valid_sides[choice]
                    print(
                        f"\033[93m\u25AA Расположение сервера: {side.capitalize()}\033[0m"
                    )
                    break
                else:
                    print(
                        "\033[91m⚠ Некорректный ввод! Используйте варианты из списка.\033[0m"
                    )
            except ValueError:
                print("\033[91m⚠ Некорректный ввод! Введите число от 1 до 4.\033[0m")

        # Инициализация curses
        stdscr = curses.initscr()
        curses.curs_set(0)  # Скрыть реальный курсор
        stdscr.nodelay(1)  # Неблокирующий ввод
        stdscr.timeout(100)  # Таймаут для обновления

        # Положение курсора клиента
        client_cursor = [0, 0]

        # Основной цикл отправки сообщений и обновления курсора
        print("\nВведите сообщение (или 'exit' для выхода):")
        while True:
            try:
                # Обработка ввода
                try:
                    key = stdscr.getch()
                    if key == curses.KEY_LEFT:
                        client_cursor[1] -= 1
                    elif key == curses.KEY_RIGHT:
                        client_cursor[1] += 1
                    elif key == curses.KEY_UP:
                        client_cursor[0] -= 1
                    elif key == curses.KEY_DOWN:
                        client_cursor[0] += 1
                    elif key == ord("q"):
                        break
                except:
                    pass

                # Отправка сообщения
                message = input("\033[94m> \033[0m")
                if message.lower() == "exit":
                    break

                # Отправка положения курсора
                cursor_info = f"CURSOR;{client_cursor[0]};{client_cursor[1]}"
                client_socket.sendall(cursor_info.encode("utf-8"))

                # Получение данных от сервера
                data = client_socket.recv(1024)
                if data:
                    response = data.decode("utf-8")
                    if response.startswith("CURSOR;"):
                        parts = response.split(";")
                        if len(parts) == 3:
                            server_cursor = [int(parts[1]), int(parts[2])]
                            # Обновление экрана
                            stdscr.clear()
                            stdscr.addstr(server_cursor[0], server_cursor[1], "S")
                            stdscr.addstr(client_cursor[0], client_cursor[1], "C")
                            stdscr.refresh()

            except socket.timeout:
                print("\033[33mТаймаут ответа сервера\033[0m")

            except Exception as send_error:
                print(f"\033[91mОшибка отправки: {send_error}\033[0m")
                break

    except Exception as connect_error:
        print(f"\033[91m🔴 Ошибка подключения: {connect_error}\033[0m")

    finally:
        client_socket.close()
        curses.endwin()
        print("\033[90m🔌 Соединение закрыто\033[0m")
