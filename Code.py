#! Add a header here documenting what this file does!!
#! Use this commenting guide for any function 
#! https://courses.cs.washington.edu/courses/cse123/23wi/resources/commenting/
#! Incase you havent found it here is the picamera2 documenatation
#! https://pip-assets.raspberrypi.com/categories/652-raspberry-pi-camera-module-2/documents/RP-008156-DS-6-picamera2-manual.pdf

#! I have added inline comments but bigger things are up here. 
#! Make a main function! Use the boiler plate statement (look this up) to run your main function instead of declaring everything in
#! Global scope. It would also be valuable to create arguments to run this command with for debugging, maybe add an argument that is a boolean
#! That when passed creates a lot of debug prints, etc. My biggest thing is adding more comments and adding more distinct functions.

from picamera2 import Picamera2
import subprocess
import serial
import time
import os

#! This should be its own function that returns a camera. You also have a lot of duplicated code here
#! I would make a function that creates 1 camera given an index (0 or 1 in this case) and then returns the configured
#! Camera. You might need to stop and start the camera based on different conditions, so dont make it such that the cameras
#! are started immediately. 

# Function start
engine = Picamera2(0)
horizon = Picamera2(1)

engine_config = engine.create_video_configuration()
horizon_config = horizon.create_video_configuration()

engine.configure(engine_config)
horizon.configure(horizon_config)
# Function end with return

# Can be in main function calling above function
engine.start()
horizon.start()

#! Add comments, like why is this sleep here?
time.sleep(5)

#! This will need to be replaced with a different file path each time or your will write over your video files.
#! Also make sure these are absolute paths, ie /home/camera_user/flight_videos/<Month>_<Day>_<Year>/<Hours>_<Mins>_<Secs>_<Camera_Angle>.mkv
#! You can write a function using the date library that gets the current date. Then you can format that into a string for the file name and use the
#! other parts of the date and the OS module to create the file paths required. 
engine.start_recording("camera1.mkv")
horizon.start_recording("camera2.mkv")

#! This might work, probably gonna need testing though
def detect_cameras():

    result = subprocess.run(
        ["rpicam-hello","--list-cameras"],
        capture_output=True,
        text=True
    )

    output = result.stdout

    camera_count = output.count(" : imx708")

    return camera_count

#! Verify that this is the right way to do this. You wil likely need to configure this, I believe the /dev/serial0 is reserved for 
#! the debug pins but maybe thats what we want
uart = serial.Serial(
    "/dev/serial0",
    baudrate=112500, #! Always define constant values that arent completely trival (0 or 1 in most cases) in SCREAMING_CASE in global scope at the top of the file
                     #! Typically right after the imports
    timeout=1        #! This should be like UART_TIMEOUT_S = 1 for example at the top of the file, then referenced here. 
    # Change Depending on how Telemetry recieves data
)

e_seconds = 0
e_minutes = 0
e_hours = 0

start_time = time.monotonic()

#! Try catches are fragile logic most of the time, its fine for testing but we can write more robust logic. Typically only try catch the section of code
#! That can actually throw an error
try:
    while True:
        time.sleep(1)

        # elapsed time

        elapsed = int(time.monotonic() - start_time)

        #! Magic numbers, use constants (see above)
        e_hours = elapsed // 3600
        e_minutes = (elapsed % 3600) // 60
        e_seconds = elapsed % 60

        camera1 = 1
        camera2 = 1

        #! This logic isnt robust. If horizon is camera1 and Fins is camera2, if horizon goes down there will be 1 camera in the list, and now camera2 
        #! will say down when really camera1 is down. Think about how you can adjust your detect cameras function to be more definitive instead of just returning a
        #! number (Can be done with regex or text parsing the stdout from the subprocess I think) 
        quantity = detect_cameras()
        
        if quantity == 1:
            camera2 = 0

        elif quantity == 0:
            camera1 = 0

        #! This is repeated code that can be shoved into a function
        #! Same file path issue as mentoned before
        file_size_1 = os.path.getsize('camera1.mkv')
        file_size_2 = os.path.getsize('camera2.mkv')

        #! Magic numbers
        file_size_1_mb = file_size_1 // 1_000_000
        file_size_2_mb = file_size_2 // 1_000_000

        #! Magic numbers & why are you using big endian? 
        file_size_data1 = file_size_1_mb.to_bytes(2, byteorder="big")
        file_size_data2 = file_size_2_mb.to_bytes(2, byteorder="big")

        output = bytes([
            0xFF, #! Make this a constant and make descriptive
            0x09, #! Make this a constant and make descriptive, Also while you have 9 items here, there is more than 9 bytes of information.
                  #! You will need to cast all fields to bytes. Reference the C language for typical sizes. 
            e_hours, 
            e_minutes, 
            e_seconds, 
            camera1, 
            camera2
        ]) + file_size_data1 + file_size_data2

        uart.write(output)

#! Why is this interrupting on a keystroke
except KeyboardInterrupt:

    engine.stop_recording()
    horizon.stop_recording()

    engine.stop()
    horizon.stop()

    uart.close()

#! This will call uart.close() twice (will probably thrown an error but regardless its never good to do this)
uart.close()
