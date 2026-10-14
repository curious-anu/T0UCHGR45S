from pymodbus.server import StartTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext
)


def run_server():
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0] * 200),
        co=ModbusSequentialDataBlock(0, [0] * 200),
        hr=ModbusSequentialDataBlock(0, [0] * 200),
        ir=ModbusSequentialDataBlock(0, [0] * 200)
    )

    context = ModbusServerContext(
        slaves=store,
        single=True
    )

    print("FlowSentinel simulated PLC starting")
    print("Listening on 127.0.0.1:5020")

    StartTcpServer(
        context=context,
        address=("127.0.0.1", 5020)
    )


if __name__ == "__main__":
    run_server()