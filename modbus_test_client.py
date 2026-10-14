import sys
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient(
    "127.0.0.1",
    port=5020,
    timeout=3
)

if not client.connect():
    print("Could not connect to simulated PLC.")
    sys.exit(1)

try:
    mode = sys.argv[1] if len(sys.argv) > 1 else "read"

    if mode == "read":
        result = client.read_holding_registers(
            address=120, count=1, slave=1
        )
        if result.isError():
            print("Read failed:", result)
        else:
            print("Register 120:", result.registers[0])

    elif mode in ("safe", "unsafe"):
        value = 45 if mode == "safe" else 95
        result = client.write_register(
            address=120, value=value, slave=1
        )
        print("Write response:", result)

    else:
        print("Choose read, safe, or unsafe.")

finally:
    client.close()