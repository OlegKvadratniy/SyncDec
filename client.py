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


def get_local_broadcasts():
    broadcasts = []
    for interface in netifaces.interfaces():
        try:
            # Пропускаем только явно ненужные интерфейсы
            if interface.startswith(("lo", "tun")):  # только loopback и VPN
                continue

            addrs = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
            for addr in addrs:
                if "broadcast" in addr:
                    # Проверяем, что интерфейс активен (имеет IP)
                    if addr.get("addr") not in ("127.0.0.1", "0.0.0.0"):
                        broadcasts.append(addr["broadcast"])

        except (ValueError, KeyError):
            continue

    return broadcasts or ["255.255.255.255"]  # универсальный fallback


def discover_servers(udp_port=50000, timeout=3):
    """Обновленная версия с автоопределением сети"""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.settimeout(timeout)

    message = "DISCOVER_REQUEST"
    servers = []

    # Получаем все актуальные broadcast-адреса
    broadcast_targets = get_local_broadcasts()
    print(f"🔎 Сканирую сети: {', '.join(broadcast_targets)}")

    # Отправляем запросы на все найденные адреса
    for target in broadcast_targets:
        try:
            udp_socket.sendto(message.encode(), (target, udp_port))
        except Exception as e:
            print(f"⚠️ Ошибка отправки на {target}: {e}")

    # Сбор ответов
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
        print(f"🟢 Успешное подключение к {server_ip}:{tcp_port}")
        print("Введите сообщение (или 'exit' для выхода):")

        while True:
            message = input("> ")
            if message.lower() == "exit":
                break

            try:
                client_socket.sendall(message.encode("utf-8"))
                data = client_socket.recv(1024)
                print(f"🔷 Ответ сервера: {data.decode('utf-8')}")
            except socket.timeout:
                print("Таймаут ожидания ответа")

    except Exception as e:
        print(f"🔴 Ошибка подключения: {e}")
    finally:
        client_socket.close()
        print("🔌 Соединение закрыто")


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
