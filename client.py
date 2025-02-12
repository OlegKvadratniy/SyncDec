import asyncio
import socket

BROADCAST_PORT = 65433
DISCOVERY_TIMEOUT = 1  # Секунды для ожидания широковещательных сообщений


async def discover_servers():
    servers = {}
    loop = asyncio.get_running_loop()

    # Создаем сокет для приема широковещательных сообщений
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: BroadcastProtocol(servers), local_addr=("0.0.0.0", BROADCAST_PORT)
    )

    try:
        await asyncio.sleep(DISCOVERY_TIMEOUT)
    finally:
        transport.close()

    return servers


class BroadcastProtocol(asyncio.DatagramProtocol):
    def __init__(self, servers):
        self.servers = servers

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message = data.decode()
        if message.startswith("SERVER:"):
            parts = message.split(":")
            if len(parts) == 3:
                name = parts[1]
                port = int(parts[2])
                self.servers[(addr[0], port)] = {"name": name, "port": port}

    def error_received(self, exc):
        print(f"Ошибка в широковещательном сокете: {exc}")

    def connection_lost(self, exc):
        pass  # Вызывается при закрытии транспорта


def list_servers(servers):
    if not servers:
        print("Не удалось обнаружить серверы.")
        return
    print("Доступные серверы:")
    for idx, ((ip, port), info) in enumerate(servers.items(), start=1):
        print(f"{idx}. {info['name']} (IP: {ip}, порт: {port})")


async def handle_client(reader, writer):
    addr = writer.get_extra_info("peername")
    try:
        while True:
            message = input("Введите сообщение для отправки (или 'exit' для выхода): ")
            if message.lower() == "exit":
                print("Отключение от сервера.")
                break
            writer.write(message.encode())
            await writer.drain()
            data = await reader.read(1024)
            if not data:
                print("Соединение закрыто сервером.")
                break
            print(f"Получено от сервера: {data.decode()}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        writer.close()
        await writer.wait_closed()


async def start_client():
    servers = await discover_servers()
    list_servers(servers)
    if not servers:
        return
    try:
        choice = int(input("Введите номер сервера для подключения: "))
        if choice < 1 or choice > len(servers):
            print("Недопустимый выбор.")
            return
    except ValueError:
        print("Пожалуйста, введите число.")
        return

    selected_server = list(servers.items())[choice - 1]
    (server_ip, server_port) = selected_server[0]
    server_info = selected_server[1]
    server_name = server_info["name"]
    print(f"Подключение к серверу '{server_name}' на {server_ip}:{server_port}")

    try:
        reader, writer = await asyncio.open_connection(server_ip, server_port)
        print(f"Подключен к серверу '{server_name}' на {server_ip}:{server_port}")
        await handle_client(reader, writer)
    except ConnectionRefusedError:
        print("Не удалось подключиться к серверу. Проверьте IP-адрес и порт.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(start_client())
