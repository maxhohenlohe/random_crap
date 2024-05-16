import can
import threading
import time

bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=1000000)

def send_keep_alive():
    while True:
        keep_alive_message = [0x10, 0x09, 0x45, 0x00, 0x00]
        message = can.Message(arbitration_id=0x2C7, data=keep_alive_message, is_extended_id=False)
        bus.send(message)
        time.sleep(0.1)

def send_analog_values():
    AVI_VALUES = [1024, 2048, 1024, 4096]

    while True:
        data = []
        for value in AVI_VALUES:
            data.extend([value >> 8, value & 0xFF])
        message = can.Message(arbitration_id=0x2C1, data=data, is_extended_id=False)
        bus.send(message)
        time.sleep(0.02)


def send_dpi_values():
    # 36000 / MPH = Period/dpi_value
    dpi_values = [5217, 521, 500, 1]

    while True:
        data = []
        for period in dpi_values:
            duty_cycle_data = 0
            period_data = int(period)

            data.extend([0, duty_cycle_data])
            data.extend([period_data >> 8, period_data & 0xFF])

        bus.send(can.Message(arbitration_id=0x2C3, data=data[:8], is_extended_id=False))
        bus.send(can.Message(arbitration_id=0x2C5, data=data[8:], is_extended_id=False))

        time.sleep(0.02)

def receive_dpo_values():
    while True:
        message = bus.recv()
        if message.arbitration_id == 0x2D1:
            data_bytes = message.data

            # Parse DPO1 duty cycle
            dpo1_duty_cycle_raw = (data_bytes[0] << 8) | data_bytes[1]
            dpo1_duty_cycle = (dpo1_duty_cycle_raw * 100.0) / 64000.0

            # Parse DPO1 period
            dpo1_period_raw = (data_bytes[2] << 8) | data_bytes[3]
            dpo1_period = dpo1_period_raw / 100.0

            # Calculate Hz
            dpo1_frequency = 1000.0 / dpo1_period

            # Print shit
            print(f"DPO1 Duty Cycle: {dpo1_duty_cycle}%")
            print(f"DPO1 Frequency: {dpo1_frequency} Hz")

threads = []
threads.append(threading.Thread(target=send_keep_alive))
threads.append(threading.Thread(target=send_analog_values))
threads.append(threading.Thread(target=send_dpi_values))
threads.append(threading.Thread(target=receive_dpo_values))

for thread in threads:
    thread.start()
