# T0UCHGR45S
Problem statement: CS-07 FlowSentinel
# FlowSentinel 🛡️🌊

> **Out-of-Band OT Cybersecurity IDS & Air-Gapped Hardware Safety Shutdown System**

FlowSentinel is an AI-assisted Intrusion Detection System (IDS) and physical hardware safety prototype designed for Operational Technology (OT) environments like water treatment plants. It combines a deterministic rule engine and an Isolation Forest machine learning model to monitor Modbus/TCP industrial traffic, log anomalies, and trigger an independent, air-gapped hardware shutdown system via an ESP32 microcontroller.

---

## 🏗️ System Architecture

```text
[ Attacker / Client ] ──(Modbus/TCP)──> [ Monitored PLC (modbus_server.py) ]
                                                   │ (HTTP Ingest)
                                                   ▼
[ ESP32 Hardware Box ] <──(UDP / Serial HMAC)── [ Flask IDS & Dashboard (app.py) ]
  (Red/Green LEDs, Buzzer, OLED)               (Isolation Forest + Rule Engine)

flowsentinel/
├── static/                 # Dashboard CSS and JavaScript assets
├── templates/              # HTML views for the operator dashboard
├── .gitignore              # Git ignore configuration (.env, pycache, etc.)
├── app.py                  # Main Flask application and IDS API server
├── bridge.py               # Hardware bridge (translates network events to ESP32 serial/HMAC)
├── detector.py             # Rule engine and Isolation Forest anomaly detector
├── modbus_server.py        # Simulated Modbus/TCP industrial PLC server
└── modbus_test_client.py   # Test script for generating traffic and simulation scenarios

Getting Started & Local Setup
1. Prerequisites
Make sure you have Python 3.8+ installed on your machine.

2. Install Dependencies
Open your terminal inside the flowsentinel project folder and install the required packages:
pip install flask pymodbus pyserial scikit-learn numpy
python bridge.py
python modbus_server.py
python app.py
Simulating Live Multi-Device Attacks (Two-Laptop Demo)
To demonstrate a real network attack during your presentation:

Connect Laptop 1 (Attacker) and Laptop 2 (IDS & ESP32) to the same mobile hotspot/Wi-Fi network.

On Laptop 2, find your local IP address using ipconfig (Windows) or ifconfig (Mac/Linux).

On Laptop 1, run a test request pointing to Laptop 2's IP address:

import urllib.request

# Replace with Laptop 2's actual Wi-Fi IP address
target_url = "[http://192.168.43.105:5000/api/test/unsafe](http://192.168.43.105:5000/api/test/unsafe)"

req = urllib.request.Request(target_url, method="POST")
res = urllib.request.urlopen(req)
print("Attack simulated:", res.read().decode())

The Result: Laptop 2's dashboard logs the threat immediately, and bridge.py triggers the ESP32 hardware to sound the physical buzzer and illuminate the Red LED.


Hardware Features & Security Design
Out-of-Band Safety System: The ESP32 operates independently from the main IP network, making it immune to software-based HMI spoofing or network malware overrides.

Cryptographic Verification: Serial packets between the host and ESP32 are secured using HMAC-SHA256 signatures with a monotonic counter to prevent replay attacks.

Fail-Safe Heartbeat: If the host bridge loses connection for more than 10 seconds, the ESP32 automatically triggers a fail-safe isolation state.

Physical Latching: Once tripped into an emergency shutdown, software commands are locked out—requiring an operator to physically press the BOOT button on the hardware box to reset.
