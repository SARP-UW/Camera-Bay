from picamera2 import Picamera2
import subprocess
import serial
import time
import os

engine = Picamera2(0)
horizon = Picamera2(1)

engine_config = engine.create_video_configuration()
horizon_config = horizon.create_video_configuration()

engine.configure(engine_config)
horizon.configure(horizon_config)

engine.start()
horizon.start()

time.sleep(5)

engine.start_recording("camera1.mkv")
horizon.start_recording("camera2.mkv")


def detect_cameras():

    result = subprocess.run(
        ["rpicam-hello","--list-cameras"],
        capture_output=True,
        text=True
    )

    output = result.stdout

    camera_count = output.count(" : imx708")

    return camera_count

uart = serial.Serial(
    "/dev/serial0",
    baudrate=112500,
    timeout=1
    # Change Depending on how Telemetry recieves data
)

e_seconds = 0
e_minutes = 0
e_hours = 0

start_time = time.monotonic()

try:
    while True:
        time.sleep(1)

        # elapsed time

        elapsed = int(time.monotonic() - start_time)

        e_hours = elapsed // 3600
        e_minutes = (elapsed % 3600) // 60
        e_seconds = elapsed % 60

        camera1 = 1
        camera2 = 1

        quantity = detect_cameras()

        if quantity == 1:
            camera2 = 0

        elif quantity == 0:
            camera1 = 0

        file_size_1 = os.path.getsize('camera1.mkv')
        file_size_2 = os.path.getsize('camera2.mkv')

        file_size_1_mb = file_size_1 // 1_000_000
        file_size_2_mb = file_size_2 // 1_000_000

        file_size_data1 = file_size_1_mb.to_bytes(2, byteorder="big")
        file_size_data2 = file_size_2_mb.to_bytes(2, byteorder="big")

        output = bytes([
            0xFF,
            0x09,
            e_hours, 
            e_minutes, 
            e_seconds, 
            camera1, 
            camera2
        ]) + file_size_data1 + file_size_data2

        uart.write(output)

except KeyboardInterrupt:

    engine.stop_recording()
    horizon.stop_recording()

    engine.stop()
    horizon.stop()

    uart.close()

uart.close()
