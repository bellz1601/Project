
# test_sender.py  (ADD-ONLY)
# Sends one JSON line to localhost:4000 to simulate a tag read.
import socket, json
HOST = "127.0.0.1"
PORT = 4000
payload = {
    "ts": "2025-10-09T00:50:00Z",
    "epc": "RFID-AEER-12-TEST007",
    "antenna": "1",
    "rssi": "-47"
}
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.sendall((json.dumps(payload) + "\n").encode("utf-8"))
s.close()
print("Sent:", payload)
