import asyncio
import socket

BROADCAST_PORT = 65433
DISCOVERY_TIMEOUT = 2  # Seconds for waiting for broadcast messages


async def discover_servers():
    servers = {}
    loop = asyncio.get_running_loop()

    # Create a UDP socket for receiving broadcast messages
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
        print(f"Error in broadcast socket: {exc}")

    def connection_lost(self, exc):
        pass  # Called when the transport is closed


def list_servers(servers):
    if not servers:
        print("No servers discovered.")
        return
    print("Available servers:")
    for idx, ((ip, port), info) in enumerate(servers.items(), start=1):
        print(f"{idx}. {info['name']} (IP: {ip}, port: {port})")


async def handle_client(reader, writer):
    addr = writer.get_extra_info("peername")
    try:
        while True:
            message = input("Enter message to send (or 'exit' to quit): ")
            if message.lower() == "exit":
                print("Disconnecting from server.")
                break
            writer.write(message.encode())
            await writer.drain()
            data = await reader.read(1024)
            if not data:
                print("Connection closed by server.")
                break
            print(f"Received from server: {data.decode()}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        writer.close()
        await writer.wait_closed()


async def start_client():
    servers = await discover_servers()
    list_servers(servers)
    if not servers:
        return
    try:
        choice = int(input("Enter the number of the server to connect to: "))
        if choice < 1 or choice > len(servers):
            print("Invalid choice.")
            return
    except ValueError:
        print("Please enter a number.")
        return

    selected_server = list(servers.items())[choice - 1]
    (server_ip, server_port) = selected_server[0]
    server_info = selected_server[1]
    server_name = server_info["name"]
    print(f"Connecting to server '{server_name}' at {server_ip}:{server_port}")

    try:
        reader, writer = await asyncio.open_connection(server_ip, server_port)
        print(f"Connected to server '{server_name}' at {server_ip}:{server_port}")
        await handle_client(reader, writer)
    except ConnectionRefusedError:
        print("Connection refused. Check the IP address and port.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(start_client())
