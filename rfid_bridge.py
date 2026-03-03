
# rfid_bridge.py  (ADD-ONLY)
# -----------------------------------------------------------
# Minimal TCP TagStream bridge for Alien readers.
# Listens on host:port (default 0.0.0.0:4000), parses each line,
# and exposes helper functions used by your app:
#   - start_tagstream_in_background(host, port)
#   - read_tags_since(since_iso8601)
#   - latest_ts()
#   - clear_tags()
#
# This file is ADD-ONLY. Drop it alongside your app.py without editing app.py.
# Your app already imports: from rfid_bridge import start_tagstream_in_background, read_tags_since, latest_ts, clear_tags
# -----------------------------------------------------------

import socket
import threading
import json
from datetime import datetime, timezone
from collections import deque

# In-memory buffer (adjust if you need more history)
_TAG_BUFFER = deque(maxlen=2000)
_LATEST_TS = None

def _now_iso_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def latest_ts():
    return _LATEST_TS

def clear_tags():
    global _LATEST_TS
    _TAG_BUFFER.clear()
    _LATEST_TS = None

def read_tags_since(since: str | None):
    # Return list of items since 'since' (ISO8601). If since=None, return all buffered items.
    if not since:
        return list(_TAG_BUFFER)
    return [t for t in _TAG_BUFFER if t.get("ts") and t["ts"] >= since]

def _append_item(item):
    global _LATEST_TS
    _TAG_BUFFER.append(item)
    ts = item.get("ts") or _now_iso_utc()
    item["ts"] = ts
    if (not _LATEST_TS) or (ts > _LATEST_TS):
        _LATEST_TS = ts

def _parse_line(line: str):
    # Supports:
    #   1) Custom JSON from Alien TagStream: {"ts":"...","epc":"...","antenna":"1","rssi":"-45"}
    #   2) Plain text with keys like 'EPC:', 'Antenna:', 'RSSI:', 'Timestamp:' (case-insensitive)
    line = (line or "").strip()
    if not line:
        return None

    # JSON format
    if line.startswith("{") and line.endswith("}"):
        try:
            d = json.loads(line)
            base_ts = d.get("ts") or d.get("time")
            ts = base_ts.strip() if isinstance(base_ts, str) else _now_iso_utc()
            epc = (d.get("epc") or d.get("tag") or "").strip()
            ant = str(d.get("antenna") or d.get("ant") or "").strip()
            rssi = str(d.get("rssi") or "").strip()
            if epc:
                return {"ts": ts, "epc": epc, "antenna": ant, "rssi": rssi, "raw": line}
        except Exception:
            return None

    # Text format (e.g., 'Tag: 3008..., Antenna: 1, RSSI: -47, Timestamp: 2025-10-09T12:34:56Z')
    low = line.lower()
    def _extract(after):
        i = low.find(after)
        if i == -1:
            return ""
        part = line[i+len(after):]
        return part.split(",")[0].strip()

    epc = _extract("epc:") or _extract("tag:")
    ant = _extract("antenna:")
    rssi = _extract("rssi:")
    ts   = _extract("timestamp:") or _extract("time:")
    if not ts:
        ts = _now_iso_utc()

    if epc:
        return {"ts": ts, "epc": epc, "antenna": ant, "rssi": rssi, "raw": line}

    return None

def _client_handler(conn, addr):
    try:
        with conn:
            buf = b""
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    try:
                        s = line.decode("utf-8", errors="ignore")
                    except Exception:
                        s = ""
                    item = _parse_line(s)
                    if item:
                        _append_item(item)
    except Exception as e:
        print("RFID client error:", e)

def start_tagstream_in_background(host="0.0.0.0", port=4000):
    # Start TCP server that accepts TagStream connections from Alien readers.
    def _server():
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(8)
        print(f"RFID TagStream server listening on {host}:{port}", flush=True)
        while True:
            conn, addr = srv.accept()
            t = threading.Thread(target=_client_handler, args=(conn, addr), daemon=True)
            t.start()

    th = threading.Thread(target=_server, daemon=True)
    th.start()
