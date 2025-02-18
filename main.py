import socket
import threading
import time


def start_server():
    server_name = input("Введите название сервера: ")
    udp_port = 50000
    tcp_port = 12345

    # UDP сервер для обнаружения
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.bind(("", udp_port))

    print(f"Сервер запущен. Для выхода нажмите Ctrl+C.")
    print(f"[UDP] Discovery сервер слушает на порту {udp_port}")

    def udp_broadcast():
        while True:
            udp_socket.sendto(server_name.encode(), ("<broadcast>", udp_port))
            time.sleep(2)

    threading.Thread(target=udp_broadcast, daemon=True).start()

    # TCP сервер
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(("0.0.0.0", tcp_port))
    tcp_socket.listen(5)

    print(f"[TCP] Сервер слушает на 0.0.0.0:{tcp_port}")

    while True:
        conn, addr = tcp_socket.accept()
        print(f"Новое подключение от {addr}")
        conn.send(f"Добро пожаловать на {server_name}".encode())
        conn.close()


def start_client():
    udp_port = 50000
    tcp_port = 12345

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.settimeout(5)
    udp_socket.bind(("", udp_port))

    print("Поиск серверов...")

    try:
        data, addr = udp_socket.recvfrom(1024)
        server_ip = addr[0]
        server_name = data.decode()
        print(f"Найден сервер: {server_name} ({server_ip})")
    except socket.timeout:
        print("Сервер не найден")
        return

    udp_socket.close()

    # Подключение к серверу по TCP
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((server_ip, tcp_port))
        msg = tcp_socket.recv(1024).decode()
        print(f"Сообщение от сервера: {msg}")
    except Exception as e:
        print(f"Ошибка подключения: {e}")
    finally:
        tcp_socket.close()


if __name__ == "__main__":
    mode = input("Выберите режим работы:\n1. Сервер\n2. Клиент\nВведите номер режима: ")
    if mode == "1":
        start_server()
    elif mode == "2":
        start_client()
    else:
        print("Неверный выбор.")
