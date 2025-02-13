import socket


def start_client(server_ip, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, port))
    print(f"Подключение к серверу {server_ip}:{port}")

    while True:
        message = input("Введите сообщение для сервера: ")
        if message.lower() == "exit":
            print("Отключение от сервера.")
            break
        client_socket.sendall(message.encode())
        data = client_socket.recv(1024)
        print(f"Получено от сервера: {data.decode()}")

    client_socket.close()
    print("Соединение закрыто.")


if __name__ == "__main__":
    SERVER_IP = "127.0.0.1"  # IP-адрес сервера
    PORT = 65432  # Порт
    start_client(SERVER_IP, PORT)
