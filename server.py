import socket


def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"Сервер запущен на {host}:{port}, ожидание подключения клиента...")
    except Exception as e:
        print(f"Ошибка при запуске сервера: {e}")
        return

    try:
        conn, addr = server_socket.accept()
        print(f"Подключен клиент с адреса: {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                print(f"Клиент {addr} отключился.")
                break
            print(f"Получено от клиента: {data.decode()}")
            response = input("Введите сообщение для клиента: ")
            conn.sendall(response.encode())
    except Exception as e:
        print(f"Ошибка при обработке клиента: {e}")
    finally:
        conn.close()
        server_socket.close()
        print("Соединение закрыто.")


if __name__ == "__main__":
    HOST = "37.45.198.216"  # Локальный IP-адрес
    PORT = 65433  # Порт
    start_server(HOST, PORT)
