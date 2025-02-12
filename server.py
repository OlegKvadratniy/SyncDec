import asyncio
import socket

BROADCAST_PORT = 65433
DISCOVERY_DELAY = 1  # Seconds between broadcasts


def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Connect to a public DNS server to get the local IP
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


async def broadcast_server_info(name, port, stop_event):
    broadcast_message = f"SERVER:{name}:{port}".encode()
    loop = asyncio.get_running_loop()
    # Create a UDP socket for broadcasting
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)
        while not stop_event.is_set():
            try:
                # No need to bind the socket when sending broadcasts
                sock.sendto(broadcast_message, ("<broadcast>", BROADCAST_PORT))
                await asyncio.sleep(DISCOVERY_DELAY)
            except Exception as e:
                print(f"Error during broadcasting: {e}")
                break


async def handle_client(reader, writer):
    addr = writer.get_extra_info("peername")
    print(f"Client connected from {addr}")
    try:
        while True:
            data = await reader.read(1024)
            if not data:
                print(f"Client {addr} disconnected.")
                break
            message = data.decode()
            print(f"Received from {addr}: {message}")
            writer.write(data)  # Echo response
            await writer.drain()
    except ConnectionResetError:
        print(f"Client {addr} forcibly closed the connection.")
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Connection with {addr} closed.")


async def find_free_port(start_port=1024, end_port=65535):
    for port in range(start_port, end_port):
        try:
            server = await asyncio.start_server(lambda r, w: None, port=port)
            server.close()
            await server.wait_closed()
            return port
        except OSError:
            continue
    raise OSError("Unable to find a free port.")


async def start_server():
    local_ip = get_local_ip()
    port = await find_free_port()
    print(f"Server starting on {local_ip}:{port}")
    name = input("Enter server name: ").strip() or f"Server_{port}"
    print(f"Server name set to '{name}'.")

    stop_event = asyncio.Event()
    broadcast_task = asyncio.create_task(broadcast_server_info(name, port, stop_event))

    server = await asyncio.start_server(handle_client, "", port)
    async with server:
        try:
            await server.serve_forever()
        except KeyboardInterrupt:
            print("Shutdown signal received. Stopping server...")
        finally:
            stop_event.set()
            broadcast_task.cancel()
            # Wait for the broadcast task to finish
            try:
                await broadcast_task
            except asyncio.CancelledError:
                pass
            print("Server stopped.")


if __name__ == "__main__":
    asyncio.run(start_server())
