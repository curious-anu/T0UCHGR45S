import socket, serial, serial.tools.list_ports, time, hmac, hashlib, threading, os, json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

SECRET = b"flowsentinel_ot_secret_2026"
UDP_PORT = 9999
HTTP_PORT = 9998

counter = int(time.time())
ser = None

def auto_find_esp32():
    # Automatically finds the ESP32 USB port if ESP32_PORT isn't set
    env_port = os.getenv("ESP32_PORT")
    if env_port:
        return env_port
    for p in serial.tools.list_ports.comports():
        desc = (p.description or "").lower()
        if any(k in desc for k in ["cp210", "ch340", "usb", "uart", "serial"]):
            return p.device
    return "COM3"

PORT = auto_find_esp32()
try:
    ser = serial.Serial(PORT, 115200, timeout=1)
    print(f"[BRIDGE] Connected to physical ESP32 on {PORT}")
except Exception as e:
    print(f"[BRIDGE] No ESP32 on {PORT} ({e}). Running in SOFTWARE FALLBACK MODE!")

def send_to_esp32(cmd, reason="Alert"):
    global counter
    counter += 1
    reason = str(reason)[:21]
    payload = f"{cmd}|{counter}|{reason}"
    sig = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()[:16]
    packet = f"{payload}|{sig}\n"
    
    if ser and ser.is_open:
        ser.write(packet.encode())
        ack = ser.readline().decode(errors="ignore").strip()
        print(f"[SERIAL -> ESP32] {packet.strip()} | ACK: {ack}")
    else:
        print(f"[SOFTWARE FALLBACK] State: {cmd} | Reason: {reason} | HMAC: {sig}")

def translate_message(raw_text):
    raw_text = raw_text.strip()
    if raw_text.startswith("{"):
        try:
            data = json.loads(raw_text)
            status = str(data.get("cmd") or data.get("severity") or data.get("type") or "TRIP").upper()
            reason = str(data.get("reason") or data.get("msg") or data.get("event") or "Anomaly")
            if "WARN" in status: return "WARN", reason
            if "RESET" in status or "SAFE" in status: return "SAFE", reason
            return "TRIP", reason
        except Exception:
            pass
    if ":" in raw_text:
        p = raw_text.split(":", 1)
        if p[0].upper() in ["TRIP", "WARN", "SAFE", "RESET", "HB"]:
            return p[0].upper(), p[1]
    return "TRIP", raw_text

class WebButtonHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        reason = parse_qs(parsed.query).get("reason", ["Manual Trigger"])[0]
        path = parsed.path.lower()
        if "warn" in path: send_to_esp32("WARN", reason)
        elif "reset" in path or "safe" in path: send_to_esp32("SAFE", reason)
        else: send_to_esp32("TRIP", reason)
        
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args): return

def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))
    while True:
        data, _ = sock.recvfrom(2048)
        cmd, reason = translate_message(data.decode(errors="ignore"))
        send_to_esp32(cmd, reason)

def heartbeat_loop():
    while True:
        send_to_esp32("HB", "Alive")
        time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    threading.Thread(target=udp_listener, daemon=True).start()
    print(f"[BRIDGE READY] Listening on UDP :{UDP_PORT} and HTTP http://127.0.0.1:{HTTP_PORT}")
    HTTPServer(("0.0.0.0", HTTP_PORT), WebButtonHandler).serve_forever()