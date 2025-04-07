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
import threading
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


def get_local_broadcasts():
    broadcasts = []
    for interface in netifaces.interfaces():
        try:
            # Пропускаем ненужные интерфейсы
            if interface.startswith(("lo", "tun", "vmnet")):
                continue

            addrs = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
            for addr in addrs:
                if "broadcast" in addr:
                    # Проверяем, что интерфейс активен
                    if addr.get("addr") not in ("127.0.0.1", "0.0.0.0"):
                        broadcasts.append(addr["broadcast"])

        except (ValueError, KeyError):
            continue

    return broadcasts or ["255.255.255.255"]  # Универсальный fallback


def discover_servers(udp_port=50000, timeout=3):
    """Обновлённая версия с автоопределением сети"""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.settimeout(timeout)

    message = "DISCOVER_REQUEST"
    servers = []

    # Получаем все актуальные broadcast-адреса
    broadcast_targets = get_local_broadcasts()
    print(f"{CYAN}{BOLD}🔎 Сканирую сети:{RESET} {', '.join(broadcast_targets)}")

    # Отправляем запросы на все найденные адреса
    for target in broadcast_targets:
        try:
            udp_socket.sendto(message.encode(), (target, udp_port))
        except Exception as e:
            print(f"{YELLOW}⚠️ Ошибка отправки на {target}: {e}{RESET}")

    # Сбор ответов
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            data, addr = udp_socket.recvfrom(1024)
            response_message = data.decode().strip()
            if response_message.startswith("SERVER_RESPONSE;"):
                parts = response_message.split(";")
                if len(parts) >= 3:
                    server_name = parts[1]
                    tcp_port = int(parts[2])
                    servers.append((server_name, addr[0], tcp_port))
                    print(
                        f"{GREEN}✅ Найден сервер:{RESET} {BOLD}{server_name}{RESET} ({addr[0]}:{tcp_port})"
                    )
        except socket.timeout:
            break
        except Exception as e:
            print(f"{RED}🚨 Ошибка при получении данных: {e}{RESET}")

    udp_socket.close()
    return servers


def tcp_client(server_ip, tcp_port):
    """Подключение по TCP к выбранному серверу"""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.settimeout(5)
        client_socket.connect((server_ip, tcp_port))
        print(f"{GREEN}🟢 Успешное подключение к {server_ip}:{tcp_port}{RESET}")

        # Определение расположения сервера
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
                        f"\033[93m\u25aa Расположение сервера: {side.capitalize()}\033[0m"
                    )
                    client_socket.sendall(f"SERVER_SIDE;{side}".encode("utf-8"))
                    break
                else:
                    print(
                        "\033[91m⚠ Некорректный ввод! Используйте варианты из списка.\033[0m"
                    )
            except ValueError:
                print("\033[91m⚠ Некорректный ввод! Введите число от 1 до 4.\033[0m")

        # Запуск потока отслеживания курсора
        cursor_thread = threading.Thread(
            target=track_cursor, args=(client_socket, side), daemon=True
        )
        cursor_thread.start()

        print(f"{BLUE}Введите сообщение (или 'exit' для выхода):{RESET}")
        while True:
            message = input(f"{MAGENTA}{BOLD}> {RESET}")
            if message.lower() == "exit":
                print(f"{YELLOW}👋 Выход из программы...{RESET}")
                break

            try:
                client_socket.sendall(message.encode("utf-8"))
                data = client_socket.recv(1024)
                print(f"{CYAN}🔷 Ответ сервера:{RESET} {data.decode('utf-8')}")
            except socket.timeout:
                print(f"{YELLOW}⏱️ Таймаут ожидания ответа{RESET}")

    except Exception as e:
        print(f"{RED}🔴 Ошибка подключения: {e}{RESET}")
    finally:
        client_socket.close()
        print(f"{YELLOW}🔌 Соединение закрыто{RESET}")


def track_cursor(client_socket, side):
    """Отслеживает курсор и отправляет события выхода за края серверу."""
    screen_width, screen_height = pyautogui.size()
    while True:
        x, y = pyautogui.position()
        if x <= 0:
            # Курсор вышел за левый край
            client_socket.sendall(f"CURSOR_EXIT;left;{y}".encode("utf-8"))
            pyautogui.moveTo(screen_width - 1, y)  # Перемещаем на правый край
        elif x >= screen_width - 1:
            # Курсор вышел за правый край
            client_socket.sendall(f"CURSOR_EXIT;right;{y}".encode("utf-8"))
            pyautogui.moveTo(0, y)  # Перемещаем на левый край
        elif y <= 0:
            # Курсор вышел за верхний край
            client_socket.sendall(f"CURSOR_EXIT;top;{x}".encode("utf-8"))
            pyautogui.moveTo(x, screen_height - 1)  # Перемещаем вниз
        elif y >= screen_height - 1:
            # Курсор вышел за нижний край
            client_socket.sendall(f"CURSOR_EXIT;bottom;{x}".encode("utf-8"))
            pyautogui.moveTo(x, 0)  # Перемещаем вверх
        time.sleep(0.01)  # Задержка, чтобы не грузить процессор


if __name__ == "__main__":
    print(f"{BLUE}{BOLD}🕵️‍♂️ Поиск серверов в локальной сети...{RESET}")
    servers = discover_servers()

    if not servers:
        print(f"{RED}{BOLD}❌ Серверы не найдены{RESET}")
        exit(0)

    print(f"\n{GREEN}{BOLD}🎯 Найденные серверы:{RESET}")
    for idx, (name, ip, port) in enumerate(servers):
        print(f"{YELLOW}{idx}{RESET}: {CYAN}{BOLD}{name}{RESET} ({ip}:{port})")

    try:
        choice = int(
            input(
                f"{MAGENTA}{BOLD}👉 Пожалуйста, выберите сервер, указав его номер: {RESET}"
            )
        )
        if 0 <= choice < len(servers):
            selected = servers[choice]
            tcp_client(selected[1], selected[2])
        else:
            print(f"{YELLOW}⚠️ Неверный выбор{RESET}")
    except ValueError:
        print(f"{YELLOW}⚠️ Введите корректное число{RESET}")
