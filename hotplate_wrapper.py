######## Hotplate Communication Functions - RS-232 Wrapper #######
# Author: Jerry A. Yang
# Date: Oct 26, 2025
# Note: Only the plate heat/stir commands are provided. Timing is handled by software, so is not 

import serial
import serial.tools.list_ports
import sys
import re
import time
import keyboard
from datetime import datetime

### Serial communication port commands ###
def open_comm():
    """ Opens an RS-232 communication line to hotplate"""
    # Print each port's details
    ports = serial.tools.list_ports.comports()
    for port in ports:
      print(f"Port: {port.device}, Description: {port.description}, HWID: {port.hwid}")

    # Open a serial port
    ser = serial.Serial('COM3', 2400, timeout=1)
    print(ser.name)
    return ser

def close_comm(ser):
    """ Closes an RS-232 communication line to hotplate"""
    print("Closing serial connection.")
    ser.close()

### Heater Functions ###
def set_heater_temp(ser, temp):
    if temp <= 25:
        print("Heater temp too low, turn off heater instead!")
        return set_heater_off(ser)
    print("Setting heater temp to: "+str(temp)+" C...")
    cmdheat = 'A'+str(temp)+'\r'
    ser.write(cmdheat.encode('utf-8'))
    data = ser.read(100) # Read up to 100 bytes
    if 'OK' not in data.decode('utf-8'):
        print("Set Heater Temp Failed!")
        return False
    print("Set Heater Temp Success!")
    return True
    
def set_heater_ramp(ser, ramp):
    print("Setting heater ramp to: "+str(ramp)+" C/hr...")
    cmdheat = 'D'+str(ramp)+'\r'
    ser.write(cmdheat.encode('utf-8'))
    data = ser.read(100) # Read up to 100 bytes
    if 'OK' not in data.decode('utf-8'):
        print("Set Heater Ramp Failed!")
        return False
    print("Set Heater Ramp Success!")
    return True

def set_heater_off(ser):
    print("Turning off heater...")
    cmdstir = 'G\r'
    ser.write(cmdstir.encode('utf-8'))
    data = ser.read(100) # Read up to 100 bytes
    if 'OK' not in data.decode('utf-8'):
        print("Heater Turn Off Failed!")
        return False
    print("Heater Turn Off Success!")
    return True

def get_temp(ser):
    print("Getting current hotplate temp...")
    cmdgettemp = 'a\r'
    ser.write(cmdgettemp.encode('utf-8'))
    data = ser.read(100)
    curtemp = re.findall(r"-?\d+", data.decode('utf-8'))  # Extracts all sequences of digits
    curtemp = [int(x) for x in curtemp]  # Converts to integers
    curtemp = curtemp[0]
    return curtemp

def get_target_temp(ser):
    print("Getting current hotplate temp...")
    cmdgettemp = 'e\r'
    ser.write(cmdgettemp.encode('utf-8'))
    data = ser.read(100) 
    curtemp = re.findall(r"-?\d+", data.decode('utf-8'))  # Extracts all sequences of digits
    curtemp = [int(x) for x in curtemp]  # Converts to integers
    curtemp = curtemp[0]
    return curtemp

def get_ramp(ser):
    print("Getting hotplate ramp...")
    cmdgettemp = 'd\r'
    ser.write(cmdgettemp.encode('utf-8'))
    data = ser.read(100)
    curtemp = re.findall(r"-?\d+", data.decode('utf-8'))  # Extracts all sequences of digits
    curtemp = [int(x) for x in curtemp]  # Converts to integers
    curtemp = curtemp[0]
    return curtemp
    
##### Stirrer Functions #####
def set_stir(ser, stir):
    if stir <= 1:
        print("Ramp speed too low, turn off stirrer instead!")
        return set_stir_off(ser)
    print("Setting stirrer speed to: "+str(stir)+" RPM...")
    cmdstir = 'E'+str(stir)+'\r'
    ser.write(cmdstir.encode('utf-8'))
    data = ser.read(100) # Read up to 100 bytes
    if 'OK' not in data.decode('utf-8'):
        print("Set Stir Speed Failed!")
        return False
    print("Set Stir Speed Success!")
    return True

def set_stir_off(ser):
    print("Turning off stirrer...")
    cmdstir = 'F\r'
    ser.write(cmdstir.encode('utf-8'))
    data = ser.read(100) # Read up to 100 bytes
    if 'OK' not in data.decode('utf-8'):
        print("Stirrer Turn Off Failed!")
        return False
    print("Stirrer Turn Off Success!")
    return True

def get_stir(ser):
    print("Getting stirrer speed...")
    cmdgetspeed = 'g\r'
    ser.write(cmdgetspeed.encode('utf-8'))
    data = ser.read(100)
    
    curspeed = re.findall(r"-?\d+", data.decode('utf-8'))  # Extracts all sequences of digits
    curspeed = [int(x) for x in curspeed]  # Converts to integers
    curspeed = curspeed[0]
    return curspeed
