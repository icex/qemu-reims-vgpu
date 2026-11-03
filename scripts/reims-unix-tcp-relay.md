# Local per-connection guest forwarding

The local `unix-socket:` guestfwd backend uses libslirp's per-connection Unix
socket transport. It avoids executing a host command inside a large QEMU
process for every guest connection. Existing `cmd:` and character-device
backends keep their original behavior.

Start the byte relay before QEMU, in a private directory owned by the same
user, then stop it after QEMU exits:

```sh
python3 scripts/reims-unix-tcp-relay.py --socket /private/run/agent.sock --port 8888
```

Select that socket in the explicitly configured guest forwarding rule:

```text
-netdev user,id=net0,restrict=on,guestfwd=tcp:10.0.2.2:8888-unix-socket:/private/run/agent.sock
```

Each guest TCP connection gets a fresh upstream connection to the chosen
host and port (127.0.0.1 by default). The proxy preserves byte order,
backpressure and directional EOF. It creates no subprocess per connection.
SIGTERM closes the listener and connections and removes its owned socket.
The optional `--receipt` argument writes connection/byte/cleanup counters.

This is a local Linux experiment. Host transfer checks and an instrumented
macOS desktop comparison are separate from full QEMU checks or a deployment.
No upstream contribution or normal-launcher change is included.
