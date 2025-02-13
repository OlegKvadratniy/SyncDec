import socket


def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Сервер запущен на {host}:{port}, ожидание подключения клиента...")

    conn, addr = server_socket.accept()
    print(f"Подключен клиент с адреса: {addr}")

    while True:
        data = conn.recv(1024)
        if not data:
            break
        print(f"Получено от клиента: {data.decode()}")
        response = input("Введите сообщение для клиента: ")
        conn.sendall(response.encode())

    conn.close()
    server_socket.close()
    print("Соединение закрыто.")


if __name__ == "__main__":
    HOST = "127.0.0.1"  # Локальный IP-адрес
    PORT = 65432  # Порт
    start_server(HOST, PORT)
