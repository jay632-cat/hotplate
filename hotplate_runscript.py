######## Hotplate Communication Code #######
# Author: Jerry A. Yang
# Date: Oct 26, 2025

import hotplate_wrapper
import serial
import serial.tools.list_ports
import sys
import re
import time
import keyboard
from datetime import datetime

# Open serial connection
ser = hotplate_wrapper.open_comm()

# Check if the file argument is provided
if len(sys.argv) < 2:
    print("Usage: python script.py <input_file>")
    sys.exit(1)

# Get the file name from the command-line arguments
input_file = sys.argv[1]
try:
    # Read the file line by line into a list
    with open(input_file, 'r') as file:
        lines = file.readlines()
        lines = [line.strip() for line in lines if line.strip()]  # Remove trailing newlines or spaces
    print("File content as a list of strings:")
    commands = [line for line in lines if not line.strip().startswith("#")]
except FileNotFoundError:
    print(f"Error: File '{input_file}' not found.")
except Exception as e:
    print(f"An error occurred: {e}")

# Check that every row has all five numbers
for onecmd in commands:
    numbers = re.findall(r"-?\d+", onecmd)  # Extracts all sequences of digits
    onecmd_values = list(map(int, numbers))  # Converts to integers
    if len(onecmd_values) != 5:
        raise Exception("File invalid - not all commands have 5 inputs!")

# Display the file commands
for onecmd in commands:
    numbers = re.findall(r"-?\d+", onecmd)  # Extracts all sequences of digits
    onecmd_values = list(map(int, numbers))  # Converts to integers
    
    hotplate_wrapper.set_heater_temp(ser, onecmd_values[0])
    hotplate_wrapper.set_heater_ramp(ser, onecmd_values[1])
    hotplate_wrapper.set_stir(ser, onecmd_values[2])
    
    # Stabilization routine - Poll plate to check temp
    printtemp = 0
    last5temps = []
    print("Wait for hotplate ramp and stabilize... started at: ", datetime.now())
    while True:
        if onecmd_values[3] < 0:
            break

        curtemp = hotplate_wrapper.get_temp(ser)
        
        if printtemp == 5:
            last5temps.append(curtemp)
            print(last5temps)
            printtemp = 0
            if len(last5temps) > 5:
                last5temps.pop(0)
            if (onecmd_values[4] == 1 and len(last5temps) > 4 
                and all(x >= last5temps[0]-1 and x <= last5temps[0]+1 for x in last5temps)
                and last5temps[0] >= onecmd_values[0]-1
                and last5temps[0] <= onecmd_values[0]+1):
                    print("Hotplate at temp. Stabilization done.")
                    break
                
            if onecmd_values[4] == 0 and curtemp >= onecmd_values[0]-2 and curtemp <= onecmd_values[0]+2:
                print("Hotplate at temp. No stabilization done.")
                break
        printtemp = printtemp + 1
    
    # Start dwell timer when stabilized at temp
    # If dwell == -1, system waits for user input to continue
    if onecmd_values[3] < 0:
        input("Press Enter to continue recipe...")
    else:
        print('Dwell for: '+numbers[3]+' s')
        print('Start dwell at: ', datetime.now())
        time.sleep(onecmd_values[3])
        print('End dwell at: ', datetime.now())

# Close the serial port
print("Recipe done.")
hotplate_wrapper.close_comm(ser)