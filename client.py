#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Клиент с автоопределением сети:
- Автоматически находит все локальные сети
- Отправляет broadcast во все активные интерфейсы
- Не требует ручного ввода IP-адресов
"""

import socket
import time
import netifaces
import curses


def get_local_broadcasts():
    broadcasts = []
    for interface in netifaces.interfaces():
        try:
            # Пропускаем ненужные интерфейсы
            if interface.startswith(("lo", "tun")):
                continue

            addrs = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
            for addr in addrs:
                if "broadcast" in addr:
                    if addr.get("addr") not in ("127.0.0.1", "0.0.0.0"):
                        broadcasts.append(addr["broadcast"])
        except (ValueError, KeyError):
            continue

    return broadcasts or ["255.255.255.255"]


def discover_servers(udp_port=50000, timeout=3):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.settimeout(timeout)

    message = "DISCOVER_REQUEST"
    servers = []

    broadcast_targets = get_local_broadcasts()
    print(f"🔎 Сканирую сети: {', '.join(broadcast_targets)}")

    for target in broadcast_targets:
        try:
            udp_socket.sendto(message.encode(), (target, udp_port))
        except Exception as e:
            print(f"⚠️ Ошибка отправки на {target}: {e}")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            data, addr = udp_socket.recvfrom(1024)
            message = data.decode().strip()
            if message.startswith("SERVER_RESPONSE;"):
                parts = message.split(";")
                if len(parts) >= 3:
                    server_name = parts[1]
                    tcp_port = int(parts[2])
                    servers.append((server_name, addr[0], tcp_port))
                    print(f"✅ Найден сервер: {server_name} ({addr[0]}:{tcp_port})")
        except socket.timeout:
            break
        except Exception as e:
            print(f"🚨 Ошибка при получении данных: {e}")

    udp_socket.close()
    return servers


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

        # Инициализация curses для клиента
        stdscr = curses.initscr()
        curses.curs_set(0)  # Скрыть реальный курсор
        stdscr.nodelay(1)  # Неблокирующий ввод
        stdscr.timeout(100)  # Таймаут для обновления
        curses.mousemask(curses.ALL_MOUSE_EVENTS)

        # Положение курсора клиента
        client_cursor = [0, 0]

        print("\nВведите сообщение (или 'exit' для выхода):")
        while True:
            try:
                # Обработка ввода с клавиатуры и мыши
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
                elif key == curses.KEY_MOUSE:
                    try:
                        _, mx, my, _, bstate = curses.getmouse()
                        if bstate & curses.BUTTON1_PRESSED:
                            client_cursor[0] = my
                            client_cursor[1] = mx
                    except Exception:
                        pass

                # Считывание текстового сообщения (это можно заменить на curses-методы, если нужно)
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


if __name__ == "__main__":
    print("🕵️‍♂️ Поиск серверов в локальной сети...")
    servers = discover_servers()

    if not servers:
        print("❌ Серверы не найдены")
        exit(0)

    print("\nНайденные серверы:")
    for idx, (name, ip, port) in enumerate(servers):
        print(f"{idx}: {name} ({ip}:{port})")

    try:
        choice = int(input("Выберите номер сервера: "))
        if 0 <= choice < len(servers):
            selected = servers[choice]
            tcp_client(selected[1], selected[2])
        else:
            print("⚠️ Неверный выбор")
    except ValueError:
        print("⚠️ Введите число")
