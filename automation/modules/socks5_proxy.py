import asyncio
import logging
import socket
import struct
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("socks5")

SO_BINDTODEVICE = 25


class Socks5Server:
    def __init__(self, host="127.0.0.1", port=1080, bind_iface=None):
        self.host = host
        self.port = port
        self.bind_iface = bind_iface.encode() if bind_iface else None

    async def handle_client(self, reader, writer):
        peer = writer.get_extra_info("peername")
        try:
            version = await reader.readexactly(1)
            if version != b"\x05":
                logger.error(
                    f"[{peer}] Non-SOCKS5 connection attempted. First byte: {version}"
                )
                writer.close()
                return
            nmethods = (await reader.readexactly(1))[0]
            methods = await reader.readexactly(nmethods)
            writer.write(b"\x05\x00")
            await writer.drain()

            request = await reader.readexactly(4)
            version, cmd, _, address_type = request
            if cmd != 1:
                writer.close()
                return

            if address_type == 1:
                address = socket.inet_ntoa(await reader.readexactly(4))
            elif address_type == 3:
                domain_length = (await reader.readexactly(1))[0]
                address = (await reader.readexactly(domain_length)).decode()
            elif address_type == 4:
                address = socket.inet_ntop(
                    socket.AF_INET6, await reader.readexactly(16)
                )
            else:
                writer.close()
                return

            port = struct.unpack("!H", await reader.readexactly(2))[0]
            logger.info(f"Connecting to {address}:{port} via {self.bind_iface}")

            # Create the socket manually to apply SO_BINDTODEVICE before connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setblocking(False)

            if self.bind_iface:
                sock.setsockopt(socket.SOL_SOCKET, SO_BINDTODEVICE, self.bind_iface)

            # We must resolve the domain manually if it's a hostname since we're using raw sockets
            loop = asyncio.get_running_loop()
            try:
                # Get IP of the destination
                addr_info = await loop.getaddrinfo(
                    address, port, family=socket.AF_INET, type=socket.SOCK_STREAM
                )
                dest_ip = addr_info[0][4][0]

                await asyncio.wait_for(
                    loop.sock_connect(sock, (dest_ip, port)), timeout=10.0
                )

                remote_reader, remote_writer = await asyncio.open_connection(sock=sock)
                writer.write(
                    b"\x05\x00\x00\x01"
                    + socket.inet_aton("0.0.0.0")
                    + struct.pack("!H", 0)
                )
                await writer.drain()
            except Exception as e:
                logger.error(f"Failed to connect to {address}:{port} - {e}")
                writer.write(
                    b"\x05\x05\x00\x01"
                    + socket.inet_aton("0.0.0.0")
                    + struct.pack("!H", 0)
                )
                await writer.drain()
                writer.close()
                sock.close()
                return

            async def forward(src, dst):
                try:
                    while True:
                        data = await src.read(8192)
                        if not data:
                            break
                        dst.write(data)
                        await dst.drain()
                except Exception:
                    pass
                finally:
                    dst.close()

            t1 = asyncio.create_task(forward(reader, remote_writer))
            t2 = asyncio.create_task(forward(remote_reader, writer))
            await asyncio.wait([t1, t2], return_when=asyncio.FIRST_COMPLETED)

            writer.close()
            remote_writer.close()

        except asyncio.IncompleteReadError:
            pass
        except Exception as e:
            logger.error(f"Error handling client: {e}")
            writer.close()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        logger.info(
            f"SOCKS5 proxy listening on {self.host}:{self.port} (binding outbound to {self.bind_iface})"
        )
        async with server:
            await server.serve_forever()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bind-iface",
        help="Outbound network interface to bind to (e.g. tun0)",
        default=None,
    )
    parser.add_argument("--port", type=int, default=1080)
    args = parser.parse_args()
    server = Socks5Server(bind_iface=args.bind_iface, port=args.port)
    asyncio.run(server.start())
