"""Per-connection byte proxy outside QEMU; never forks a large VM address space."""
import argparse
import asyncio
import json
from pathlib import Path
import signal


async def main(args):
    path = Path(args.socket)
    assert not path.exists()
    stopping = asyncio.Event()
    active = set()
    counts = dict(accepted=0, connected=0, completed=0, refused=0, cancelled=0,
                  guest_to_host_bytes=0, host_to_guest_bytes=0)

    async def handle(reader, writer):
        task = asyncio.current_task()
        active.add(task)
        counts['accepted'] += 1
        upstream = None
        pumps = []
        try:
            peer, upstream = await asyncio.wait_for(
                asyncio.open_connection(args.host, args.port), timeout=3)
            counts['connected'] += 1

            async def pump(source, destination, key):
                while data := await source.read(65536):
                    counts[key] += len(data)
                    destination.write(data)
                    await destination.drain()
                if destination.can_write_eof():
                    destination.write_eof()
                    await destination.drain()

            pumps = [asyncio.create_task(pump(reader, upstream, 'guest_to_host_bytes')),
                     asyncio.create_task(pump(peer, writer, 'host_to_guest_bytes'))]
            await asyncio.gather(*pumps)
            counts['completed'] += 1
        except (ConnectionError, OSError, asyncio.TimeoutError):
            counts['refused'] += 1
        except asyncio.CancelledError:
            counts['cancelled'] += 1
            raise
        finally:
            for pump_task in pumps:
                if not pump_task.done():
                    pump_task.cancel()
            await asyncio.gather(*pumps, return_exceptions=True)
            for stream in (upstream, writer):
                if stream is not None:
                    stream.close()
                    try:
                        await stream.wait_closed()
                    except (OSError, ConnectionError):
                        pass
            active.discard(task)

    server = await asyncio.start_unix_server(handle, str(path), cleanup_socket=False)
    path.chmod(0o600)
    inode = path.stat().st_ino
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stopping.set)
    print(json.dumps(dict(event='ready', socket=str(path), inode=inode)), flush=True)
    try:
        await stopping.wait()
    finally:
        server.close()
        await server.wait_closed()
        if active:
            _, pending = await asyncio.wait(list(active), timeout=1)
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
        assert path.stat().st_ino == inode
        path.unlink()
        result = dict(event='exit', active=0, **counts)
        if args.receipt:
            Path(args.receipt).write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--socket', required=True)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8888)
    parser.add_argument('--receipt')
    asyncio.run(main(parser.parse_args()))
