import tkinter as tk
from tkinter import simpledialog
import hotplate_wrapper
import sys
import re
import time
import keyboard
from datetime import datetime

ser = []


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Hotplate Controller")
        self.root.geometry("600x500")
        
        global ser
        ser = hotplate_wrapper.open_comm() 
        curtemp = hotplate_wrapper.get_temp(ser)
        targettemp = hotplate_wrapper.get_target_temp(ser)
        if targettemp == 0:
            targettemp = curtemp
        ramp = hotplate_wrapper.get_ramp(ser)
        stir = hotplate_wrapper.get_stir(ser)    
        
        self.display1 = tk.Label(root, text="Hotplate Temp: "+str(curtemp), bg="lightpink", width=30, height=2)
        self.display1.pack(pady=10)
        
        self.display2 = tk.Label(root, text="Hotplate Target Temp: "+str(targettemp), bg="lightgreen", width=30, height=2)
        self.display2.pack(pady=10)
        
        self.display3 = tk.Label(root, text="Hotplate Ramp: "+str(ramp), bg="lightblue", width=30, height=2)
        self.display3.pack(pady=10)
        
        self.display4 = tk.Label(root, text="Hotplate Stir: "+str(stir), bg="lightyellow", width=30, height=2)
        self.display4.pack(pady=10)
        
        instrs = "Instructions: Enter positive integer value into input field, then press button for desired function.\nIf you wish to run a recipe, CLOSE THIS WINDOW and use the command-line interface."
        
        self.display5 = tk.Label(root, text=instrs, width=75, height=2)
        self.display5.pack(pady=10)
        
        # Create a Button to trigger input retrieval     
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        Button(self, button_frame, "Set Heat Temp", self.get_desired_temp)
        Button(self, button_frame, "Set Heat Ramp", self.get_desired_ramp)
        Button(self, button_frame, "Set Stir Speed", self.get_desired_stir)
        button_frame2 = tk.Frame(root)
        button_frame2.pack(pady=10)
        Button(self, button_frame2, "Turn Heat Off", self.turn_heater_off)
        Button(self, button_frame2, "Turn Stir Off", self.turn_stirrer_off)

        # Create an Entry widget
        self.entry = tk.Entry(root, width=30)
        self.entry.pack(pady=10)

        # Label to display the retrieved input
        self.label = tk.Label(root, text="")
        self.label.pack(pady=10)
        
        # Periodically update display
        self.update_curtemp()
        self.update_curtarget()
        self.update_curramp()
        self.update_curstir()
          

    def get_desired_temp(self):
        # Retrieve the input from the Entry widget
        user_input = self.entry.get()
        hotplate_wrapper.set_heater_temp(ser, int(user_input))
        # Display the input in the Label
        self.label.config(text=f"Setting hotplate to: {user_input} C")
        self.entry.delete(0, tk.END)
        
    def get_desired_stir(self):
        # Retrieve the input from the Entry widget
        user_input = self.entry.get()
        hotplate_wrapper.set_stir(ser, int(user_input))
        # Display the input in the Label
        self.label.config(text=f"Setting stirrer to: {user_input} RPM")
        self.entry.delete(0, tk.END)
        
    def get_desired_ramp(self):
        # Retrieve the input from the Entry widget
        user_input = self.entry.get()
        hotplate_wrapper.set_heater_ramp(ser, int(user_input))
        # Display the input in the Label
        self.label.config(text=f"Setting hotplate ramp to: {user_input} RPM")
        self.entry.delete(0, tk.END)
        
    def turn_heater_off(self):
        # Retrieve the input from the Entry widget
        user_input = self.entry.get()
        hotplate_wrapper.set_heater_off(ser)
        # Display the input in the Label
        self.label.config(text=f"Heater turning off")
        self.entry.delete(0, tk.END)
        
    def turn_stirrer_off(self):
        # Retrieve the input from the Entry widget
        user_input = self.entry.get()
        hotplate_wrapper.set_stir_temp(ser)
        # Display the input in the Label
        self.label.config(text=f"Stirrer turning off")
        self.entry.delete(0, tk.END)
        
    def update_curtemp(self):
        current_time = hotplate_wrapper.get_temp(ser)  # Get current time
        self.display1.config(text=f"Hotplate Temp: {current_time} C")  # Update label text
        root.after(10000, self.update_curtemp)
    def update_curstir(self):
        current_time = hotplate_wrapper.get_stir(ser)  # Get current time
        self.display4.config(text=f"Hotplate Stir: {current_time} RPM")  # Update label text
        root.after(10000, self.update_curstir)
    def update_curramp(self):
        current_time = hotplate_wrapper.get_ramp(ser)  # Get current time
        self.display3.config(text=f"Hotplate Ramp: {current_time} C/hr")  # Update label text
        root.after(10000, self.update_curramp)
    def update_curtarget(self):
        current_time = hotplate_wrapper.get_target_temp(ser)  # Get current time
        self.display2.config(text=f"Hotplate Target Temp: {current_time} C")  # Update label text
        root.after(10000, self.update_curtarget)
    
class Button:
    def __init__(self, root, parent, text, command):
        self.button = tk.Button(parent, text=text, command=command, width=15)
        self.button.pack(side=tk.LEFT, padx=5)

# Create the main Tkinter window
root = tk.Tk()
app = App(root)
root.mainloop()