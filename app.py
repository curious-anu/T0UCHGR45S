from datetime import datetime, timezone
from threading import Thread

from flask import Flask, jsonify, render_template
from pymodbus.client import ModbusTcpClient

from detector import analyze_event
from modbus_server import run_server

app = Flask(__name__)

events = []
setpoint_history = []


def process_event(event):
    result = analyze_event(event)

    record = {
        **event,
        **result,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    events.insert(0, record)
    del events[200:]

    if (
        int(event.get("function_code", 0)) in [5, 6, 15, 16]
        and int(event.get("register", -1)) == 120
        and event.get("old_value") is not None
    ):
        setpoint_history.insert(0, {
            "timestamp": record["timestamp"],
            "source": record["source"],
            "old_value": event["old_value"],
            "new_value": event["value"],
            "status": record["status"],
            "severity": record["severity"],
            "source_type": record["source_type"]
        })
        del setpoint_history[100:]

    return record


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/status")
def status():
    return jsonify({
        "model": "Isolation Forest",
        "model_ready": True,
        "event_count": len(events),
        "alert_count": sum(
            e["status"] != "NORMAL" for e in events
        ),
        "live_capture": False,
        "modbus_server": "127.0.0.1:5020"
    })


@app.route("/api/events")
def get_events():
    return jsonify(events)


@app.route("/api/history")
def get_history():
    return jsonify(setpoint_history)


@app.route("/api/test/<scenario>", methods=["POST"])
def simulated_test(scenario):
    samples = {
        "normal": {
            "source": "PLC-SIM-01",
            "protocol": "Modbus/TCP",
            "function_code": 3,
            "register": 10,
            "value": 45,
            "source_type": "SIMULATED"
        },
        "unauthorized": {
            "source": "UNKNOWN-CLIENT",
            "protocol": "Modbus/TCP",
            "function_code": 6,
            "register": 100,
            "value": 50,
            "source_type": "SIMULATED"
        },
        "unsafe": {
            "source": "PLC-SIM-01",
            "protocol": "Modbus/TCP",
            "function_code": 6,
            "register": 120,
            "old_value": 0,
            "value": 95,
            "source_type": "SIMULATED"
        }
    }

    if scenario not in samples:
        return jsonify({"error": "Unknown scenario"}), 400

    return jsonify(process_event(samples[scenario]))


@app.route("/api/modbus-test/<scenario>", methods=["POST"])
def modbus_test(scenario):
    if scenario not in (
        "normal", "safe", "unauthorized", "unsafe"
    ):
        return jsonify({"error": "Unknown scenario"}), 400

    client = ModbusTcpClient(
        "127.0.0.1",
        port=5020,
        timeout=3
    )

    if not client.connect():
        return jsonify({
            "error": "Modbus server is not ready on port 5020"
        }), 503

    try:
        if scenario == "normal":
            result = client.read_holding_registers(
                address=120,
                count=1,
                slave=1
            )

            if result.isError():
                return jsonify({"error": str(result)}), 502

            event = {
                "source": "PLC-SIM-01",
                "protocol": "Modbus/TCP",
                "function_code": 3,
                "register": 120,
                "value": result.registers[0],
                "source_type": "CLIENT TEST"
            }

        else:
            register = 100 if scenario == "unauthorized" else 120
            value = 95 if scenario == "unsafe" else 45

            previous = client.read_holding_registers(
                address=register,
                count=1,
                slave=1
            )

            if previous.isError():
                return jsonify({"error": str(previous)}), 502

            old_value = previous.registers[0]

            result = client.write_register(
                address=register,
                value=value,
                slave=1
            )

            if result.isError():
                return jsonify({"error": str(result)}), 502

            event = {
                "source": (
                    "UNKNOWN-CLIENT"
                    if scenario == "unauthorized"
                    else "PLC-SIM-01"
                ),
                "protocol": "Modbus/TCP",
                "function_code": 6,
                "register": register,
                "old_value": old_value,
                "value": value,
                "source_type": "CLIENT TEST"
            }

        return jsonify(process_event(event))

    except Exception as exc:
        app.logger.exception("Modbus test failed")
        return jsonify({"error": str(exc)}), 500

    finally:
        client.close()


if __name__ == "__main__":
    server_thread = Thread(
        target=run_server,
        daemon=True,
        name="FlowSentinel-Modbus"
    )
    server_thread.start()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )

import socket

def trigger_esp32(cmd="TRIP", reason="Abnormal Setpoint"):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(f"{cmd}:{reason}".encode(), ("127.0.0.1", 9999))

# Inside her "Unauthorized Write" button handler:
trigger_esp32("TRIP", "Unauthorized Write")

# Inside her "Abnormal Setpoint" button handler:
trigger_esp32("TRIP", "Abnormal Setpoint")