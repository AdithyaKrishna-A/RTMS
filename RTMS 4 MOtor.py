import tkinter as tk
import RPi.GPIO as GPIO
import time
import math

TRIG1 = 23
ECHO1 = 24
TRIG2 = 31
ECHO2 = 32
IR1 = 12
IR2 = 13

# Motor driver pins (first side)
MOTOR_ENABLE_PIN = 36  # Replace with the actual GPIO pin connected to the motor driver enable pin
MOTOR_INPUT1_PIN = 38  # Replace with the actual GPIO pin connected to the motor driver input1 pin
MOTOR_INPUT2_PIN = 40 

# Motor driver pins (second side)
MOTOR_ENABLE_PIN_2 = 16  # Replace with the actual GPIO pin connected to the second side motor driver enable pin
MOTOR_INPUT3_PIN = 8  # Replace with the actual GPIO pin connected to the second side motor driver input3 pin
MOTOR_INPUT4_PIN = 10  # Replace with the actual GPIO pin connected to the second side motor driver input4 pin

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(TRIG1, GPIO.OUT)
GPIO.setup(ECHO1, GPIO.IN)
GPIO.setup(TRIG2, GPIO.OUT)
GPIO.setup(ECHO2, GPIO.IN)
GPIO.setup(IR1, GPIO.IN)
GPIO.setup(IR2, GPIO.IN)

# Motor driver setup (first side)
GPIO.setup(MOTOR_ENABLE_PIN, GPIO.OUT)
GPIO.setup(MOTOR_INPUT1_PIN, GPIO.OUT)
GPIO.setup(MOTOR_INPUT2_PIN, GPIO.OUT)
motor_pwm = GPIO.PWM(MOTOR_ENABLE_PIN, 50)  # 50 Hz PWM frequency for the first side motor

# Motor driver setup (second side)
GPIO.setup(MOTOR_ENABLE_PIN_2, GPIO.OUT)
GPIO.setup(MOTOR_INPUT3_PIN, GPIO.OUT)
GPIO.setup(MOTOR_INPUT4_PIN, GPIO.OUT)
motor_pwm_2 = GPIO.PWM(MOTOR_ENABLE_PIN_2, 50)  # 50 Hz PWM frequency for the second side motor

WHEEL_RADIUS = 7.5  # in centimeters
TARGET_DISTANCE = 100000  # Target distance to reverse direction in centimeters

revolutions = 0  # Variable to store the number of revolutions
reversal_triggered = False
fault_detected = False  # Variable to indicate whether a fault is detected
distance_moved = 0.0  # Variable to store the distance moved

def distance(trig, echo):
    GPIO.output(trig, False)
    time.sleep(0.00001)
    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)

    while GPIO.input(echo) == 0:
        pulse_start = time.time()

    while GPIO.input(echo) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    return distance

def control_motor(enable, input1, input2, status):
    GPIO.output(enable, GPIO.HIGH)  # Enable the motor driver

    if status == "on":
        GPIO.output(input1, GPIO.HIGH)
        GPIO.output(input2, GPIO.LOW)
    elif status == "off":
        GPIO.output(input1, GPIO.LOW)
        GPIO.output(input2, GPIO.LOW)
    elif status == "reverse":
        # Reverse the motor direction
        GPIO.output(input1, GPIO.LOW)
        GPIO.output(input2, GPIO.HIGH)

def control_motor_2(enable, input3, input4, status):
    GPIO.output(enable, GPIO.HIGH)  # Enable the second side motor driver

    if status == "on":
        GPIO.output(input3, GPIO.HIGH)
        GPIO.output(input4, GPIO.LOW)
    elif status == "off":
        GPIO.output(input3, GPIO.LOW)
        GPIO.output(input4, GPIO.LOW)
    elif status == "reverse":
        # Reverse the second side motor direction
        GPIO.output(input3, GPIO.LOW)
        GPIO.output(input4, GPIO.HIGH)

def start_stop_motor():
    global motor_running, fault_detected
    motor_running = not motor_running  # Toggle the motor state
    if motor_running:
        if not fault_detected:  # Only start the motor if no fault is detected
            control_motor(MOTOR_ENABLE_PIN, MOTOR_INPUT1_PIN, MOTOR_INPUT2_PIN, "on")
            control_motor_2(MOTOR_ENABLE_PIN_2, MOTOR_INPUT3_PIN, MOTOR_INPUT4_PIN, "on")
            start_stop_button.config(text="Stop Motor")
            continue_button.config(state=tk.DISABLED)  # Disable the Continue button
    else:
        control_motor(MOTOR_ENABLE_PIN, MOTOR_INPUT1_PIN, MOTOR_INPUT2_PIN, "off")
        control_motor_2(MOTOR_ENABLE_PIN_2, MOTOR_INPUT3_PIN, MOTOR_INPUT4_PIN, "off")
        start_stop_button.config(text="Start Motor")
        continue_button.config(state=tk.NORMAL)  # Enable the Continue button

def continue_motor():
    global motor_running, reversal_triggered, fault_detected
    motor_running = True
    fault_detected = False  # Reset the fault detection
    start_stop_motor()  # Start both motors
    reversal_triggered = False  # Reset the reversal trigger

def log_fault():
    global fault_detected
    fault_detected = True
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    fault_detected_listbox.insert(tk.END, f"Fault Detected at {current_time} : {distance_moved}")
    fault_detected_listbox.yview(tk.END)  # Automatically scroll to the latest entry

def update_data():
    global revolutions, reversal_triggered, distance_moved
    
    dist1 = distance(TRIG1, ECHO1)
    dist2 = distance(TRIG2, ECHO2)
    ir1 = GPIO.input(IR1)
    ir2 = GPIO.input(IR2)

    if dist1 < 30 or dist2 < 30 or ir1 == 1 or ir2 == 1:
        label1.config(text="Fault Detected! ")
        log_fault()  # Log the fault occurrence
        control_motor(MOTOR_ENABLE_PIN, MOTOR_INPUT1_PIN, MOTOR_INPUT2_PIN, "off")
        control_motor_2(MOTOR_ENABLE_PIN_2, MOTOR_INPUT3_PIN, MOTOR_INPUT4_PIN, "off")
    else:
        label1.config(text="Clear ")

    if motor_running:
        # Only check sensors and control motor if it is running and no fault is detected
        if not fault_detected and dist1 > 30 and dist2 > 30 and ir1 == 0 and ir2 == 0:
            control_motor(MOTOR_ENABLE_PIN, MOTOR_INPUT1_PIN, MOTOR_INPUT2_PIN, "on")
            control_motor_2(MOTOR_ENABLE_PIN_2, MOTOR_INPUT3_PIN, MOTOR_INPUT4_PIN, "on")
            revolutions += 1  # Increment the number of revolutions
        else:
            control_motor(MOTOR_ENABLE_PIN, MOTOR_INPUT1_PIN, MOTOR_INPUT2_PIN, "off")
            control_motor_2(MOTOR_ENABLE_PIN_2, MOTOR_INPUT3_PIN, MOTOR_INPUT4_PIN, "off")

        # Calculate distance moved by the motor
        distance_moved = revolutions * (2 * math.pi * WHEEL_RADIUS)  # Circumference formula
        distance_moved_cm = round(distance_moved, 2)
        
        distance_label.config(text=f"Distance Moved: {distance_moved_cm} cm")

        # Check if the target distance is reached and reversal is not triggered
        if distance_moved >= TARGET_DISTANCE and not reversal_triggered:
            reversal_triggered = True
            control_motor(MOTOR_ENABLE_PIN, MOTOR_INPUT1_PIN, MOTOR_INPUT2_PIN, "off")
            control_motor_2(MOTOR_ENABLE_PIN_2, MOTOR_INPUT3_PIN, MOTOR_INPUT4_PIN, "off")
            time.sleep(1)  # Add a delay to ensure the motor stops before reversing
            control_motor(MOTOR_ENABLE_PIN, MOTOR_INPUT1_PIN, MOTOR_INPUT2_PIN, "reverse")
            control_motor_2(MOTOR_ENABLE_PIN_2, MOTOR_INPUT3_PIN, MOTOR_INPUT4_PIN, "reverse")
            start_stop_button.config(state=tk.DISABLED)  # Disable the Start/Stop button during reversal
            continue_button.config(state=tk.NORMAL)  # Enable the Continue button

    root.after(500, update_data)

try:
    root = tk.Tk()
    root.title("Sensor Data")
    root.geometry("600x400")

    label1 = tk.Label(root, text="Clear", font=("Helvetica", 16))
    label1.pack(pady=10)

    distance_label = tk.Label(root, text="Distance Moved: 0.0 cm", font=("Helvetica", 16))
    distance_label.pack(pady=10)

    start_stop_button = tk.Button(root, text="Start Motor", command=start_stop_motor)
    start_stop_button.pack(pady=10)

    continue_button = tk.Button(root, text="Continue", command=continue_motor, state=tk.DISABLED)
    continue_button.pack(pady=10)

    fault_detected_listbox_label = tk.Label(root, text="Fault Detected Log", font=("Helvetica", 16))
    fault_detected_listbox_label.pack(pady=10)

    # Listbox to display the fault log
    fault_detected_listbox = tk.Listbox(root, width=40, height=5)
    fault_detected_listbox.pack(pady=10)

    motor_pwm.start(0)
    motor_pwm_2.start(0)

    motor_running = False

    update_data()

    root.mainloop()

finally:
    GPIO.cleanup()

