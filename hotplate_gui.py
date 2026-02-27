#%%
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import csv
from queue import Queue
from collections import deque
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from matplotlib.figure import Figure
import hotplate_wrapper as hw

class TemperatureData:
    """Manages temperature history"""
    def __init__(self, max_points=86400):  # 24 hours at 1 second intervals
        self.timestamps = deque(maxlen=max_points)
        self.temperatures = deque(maxlen=max_points)
        self.start_time = time.time()
    
    def add_point(self, temp):
        elapsed = time.time() - self.start_time
        self.timestamps.append(elapsed)  # Time in seconds
        self.temperatures.append(temp)
    
    def get_data(self):
        return list(self.timestamps), list(self.temperatures)
    
    def clear(self):
        self.timestamps.clear()
        self.temperatures.clear()
        self.start_time = time.time()

class HotplateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hotplate Control Interface")
        self.root.state('zoomed')  # Maximize window on startup
        
        # Backend connection
        self.ser = None
        self.connected = False
        self.temp_data = TemperatureData()
        
        # Serial communication lock
        self.serial_lock = threading.Lock()
        
        # Background polling thread
        self.polling_queue = Queue()
        self.polling_stop = threading.Event()
        self.polling_thread = None
        
        # Create GUI
        self.create_widgets()
        self.create_layout()
        
        # Start periodic update
        self.periodic_update()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Auto-connect on startup
        self.root.after(100, self.connect)
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # ===== LEFT PANEL =====
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # TITLE SECTION
        self.title_frame = ttk.Frame(self.left_frame)
        self.title_frame.pack(fill=tk.X, pady=(0, 8))
        
        title_label = ttk.Label(self.title_frame, text="Torrey Pines Hotplate", 
                                font=("Arial", 14, "bold"))
        title_label.pack(anchor=tk.W)
        
        date_label = ttk.Label(self.title_frame, text="February 26, 2026", 
                               font=("Arial", 9))
        date_label.pack(anchor=tk.W)
        
        author_label = ttk.Label(self.title_frame, text="Author: Jerry A. Yang", 
                                 font=("Arial", 9))
        author_label.pack(anchor=tk.W)
        
        # CONNECTION SECTION
        self.conn_frame = ttk.LabelFrame(self.left_frame, text="Connection", padding=8)
        self.conn_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.connect_button = ttk.Button(self.conn_frame, text="Connect to Hotplate", 
                                         command=self.toggle_connection)
        self.connect_button.pack(fill=tk.X, pady=(0, 5))
        
        self.status_label = ttk.Label(self.conn_frame, text="Disconnected", 
                                      foreground="red", font=("Arial", 10))
        self.status_label.pack()
        
        # CURRENT VALUES SECTION
        self.display_frame = ttk.LabelFrame(self.left_frame, text="Current Values", padding=8)
        self.display_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Current Temperature
        ttk.Label(self.display_frame, text="Current Temp:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.current_temp_value = ttk.Label(self.display_frame, text="-- °C", 
                                            font=("Arial", 12, "bold"), foreground="blue")
        self.current_temp_value.grid(row=0, column=1, sticky=tk.E, pady=3)
        
        # Setpoint Temperature
        ttk.Label(self.display_frame, text="Setpoint Temp:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.setpoint_temp_value = ttk.Label(self.display_frame, text="-- °C", 
                                             font=("Arial", 11), foreground="green")
        self.setpoint_temp_value.grid(row=1, column=1, sticky=tk.E, pady=3)
        
        # Ramp Rate
        ttk.Label(self.display_frame, text="Ramp Rate:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.ramp_rate_value = ttk.Label(self.display_frame, text="-- °C/hr", 
                                         font=("Arial", 11), foreground="purple")
        self.ramp_rate_value.grid(row=2, column=1, sticky=tk.E, pady=3)
        
        # Stir Speed
        ttk.Label(self.display_frame, text="Stir Speed:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.stir_speed_value = ttk.Label(self.display_frame, text="-- RPM", 
                                          font=("Arial", 11), foreground="darkorange")
        self.stir_speed_value.grid(row=3, column=1, sticky=tk.E, pady=3)
        
        self.display_frame.columnconfigure(1, weight=1)
        
        # CONTROLS SECTION
        self.control_frame = ttk.LabelFrame(self.left_frame, text="Controls", padding=8)
        self.control_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        # Temperature control
        ttk.Label(self.control_frame, text="Set Temperature (°C):").pack(anchor=tk.W, pady=(5, 2))
        self.set_temp_input = ttk.Spinbox(self.control_frame, from_=30, to=500, width=10)
        self.set_temp_input.set(25)
        self.set_temp_input.pack(fill=tk.X, pady=(0, 2))
        self.set_temp_button = ttk.Button(self.control_frame, text="Set Temperature", 
                                          command=self.set_temperature)
        self.set_temp_button.pack(fill=tk.X, pady=(0, 8))
        
        # Ramp rate control
        ttk.Label(self.control_frame, text="Set Ramp Rate (°C/hr):").pack(anchor=tk.W, pady=(5, 2))
        self.set_ramp_input = ttk.Spinbox(self.control_frame, from_=1, to=300, width=10)
        self.set_ramp_input.set(450)
        self.set_ramp_input.pack(fill=tk.X, pady=(0, 2))
        self.set_ramp_button = ttk.Button(self.control_frame, text="Set Ramp Rate", 
                                          command=self.set_ramp_rate)
        self.set_ramp_button.pack(fill=tk.X, pady=(0, 8))
        
        # Stir speed control
        ttk.Label(self.control_frame, text="Set Stir Speed (RPM):").pack(anchor=tk.W, pady=(5, 2))
        self.set_stir_input = ttk.Spinbox(self.control_frame, from_=0, to=1500, width=10)
        self.set_stir_input.set(0)
        self.set_stir_input.pack(fill=tk.X, pady=(0, 2))
        self.set_stir_button = ttk.Button(self.control_frame, text="Set Stir Speed", 
                                          command=self.set_stir_speed)
        self.set_stir_button.pack(fill=tk.X, pady=(0, 8))
        
        # Off buttons
        self.heater_off_button = ttk.Button(self.control_frame, text="Turn Off Heater", 
                                            command=self.turn_off_heater)
        self.heater_off_button.pack(fill=tk.X, pady=(0, 5))
        
        self.stir_off_button = ttk.Button(self.control_frame, text="Turn Off Stirrer", 
                                          command=self.turn_off_stirrer)
        self.stir_off_button.pack(fill=tk.X, pady=(0, 5))
        
        # Store control widgets for enable/disable
        self.control_widgets = [
            self.set_temp_input, self.set_temp_button,
            self.set_ramp_input, self.set_ramp_button,
            self.set_stir_input, self.set_stir_button,
            self.heater_off_button, self.stir_off_button
        ]
        
        # ===== RIGHT PANEL: PLOT =====
        self.plot_frame = ttk.LabelFrame(self.main_frame, text="Temperature Plot", padding=8)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("Time (seconds)")
        self.ax.set_ylabel("Temperature (°C)")
        self.ax.set_title("Temperature vs Time")
        self.ax.grid(True, alpha=0.3)
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Plot control buttons frame
        self.plot_buttons_frame = ttk.Frame(self.plot_frame)
        self.plot_buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Save CSV button
        self.save_csv_button = ttk.Button(self.plot_buttons_frame, text="Save Plot as CSV", 
                                          command=self.save_csv)
        self.save_csv_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Clear button
        self.clear_button = ttk.Button(self.plot_buttons_frame, text="Clear Plot Data", 
                                       command=self.clear_plot_data)
        self.clear_button.pack(side=tk.LEFT)
    
    def create_layout(self):
        """Layout is created in create_widgets for tkinter"""
        pass
    
    def toggle_connection(self):
        """Connect or disconnect from hotplate"""
        if not self.connected:
            self.connect()
        else:
            self.disconnect()
    
    def connect(self):
        """Establish connection to hotplate"""
        try:
            self.ser = hw.open_comm()
            self.connected = True
            self.update_connection_status(True, "Connected")
            self.connect_button.config(text="Disconnect from Hotplate")
            self.temp_data.clear()
            
            # Start background polling thread
            self.polling_stop.clear()
            self.polling_thread = threading.Thread(target=self.background_polling, daemon=True)
            self.polling_thread.start()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.update_connection_status(False, "Connection Failed")
    
    def disconnect(self):
        """Close connection to hotplate"""
        try:
            # Stop background polling thread
            self.polling_stop.set()
            if self.polling_thread and self.polling_thread.is_alive():
                self.polling_thread.join(timeout=2)
            
            if self.ser:
                hw.close_comm(self.ser)
            self.connected = False
            self.update_connection_status(False, "Disconnected")
            self.connect_button.config(text="Connect to Hotplate")
        except Exception as e:
            messagebox.showerror("Disconnection Error", f"Error during disconnect: {str(e)}")
    
    def update_connection_status(self, connected, status):
        """Update connection status display"""
        self.status_label.config(text=status, foreground="green" if connected else "red")
        
        # Enable/disable controls
        for widget in self.control_widgets:
            widget.config(state=tk.NORMAL if connected else tk.DISABLED)
    
    
    def background_polling(self):
        """Background thread that polls the hotplate without blocking GUI"""
        while not self.polling_stop.is_set():
            if self.connected and self.ser:
                try:
                    with self.serial_lock:
                        current_temp = hw.get_temp(self.ser)
                        setpoint_temp = hw.get_target_temp(self.ser)
                        ramp_rate = hw.get_ramp(self.ser)
                        stir_speed = hw.get_stir(self.ser)
                    
                    # Put data in queue for main thread to consume
                    self.polling_queue.put({
                        'current_temp': current_temp,
                        'setpoint_temp': setpoint_temp,
                        'ramp_rate': ramp_rate,
                        'stir_speed': stir_speed
                    })
                except Exception as e:
                    print(f"Error in background polling: {e}")
                    # Keep polling even if there's an error, but wait a bit
                    time.sleep(0.5)
            
            # Sleep for a bit before next poll
            time.sleep(1)
    
    def periodic_update(self):
        """Update GUI from queue without blocking on I/O"""
        # Check if there's data in the queue
        try:
            while True:
                data = self.polling_queue.get_nowait()
                
                # Add temperature to plot data
                self.temp_data.add_point(data['current_temp'])
                
                # Update display
                self.current_temp_value.config(text=f"{data['current_temp']} °C")
                self.setpoint_temp_value.config(text=f"{data['setpoint_temp']} °C")
                self.ramp_rate_value.config(text=f"{data['ramp_rate']} °C/hr")
                
                # Display stir speed or warning if no data
                if data['stir_speed'] <= 0:
                    self.stir_speed_value.config(text="No data")
                else:
                    self.stir_speed_value.config(text=f"{data['stir_speed']} RPM")
                
                # Update plot
                self.update_plot()
        except:
            # Queue is empty, which is fine
            pass
        
        # Schedule next check
        self.root.after(100, self.periodic_update)
    
    def update_plot(self):
        """Update the temperature vs time plot"""
        times, temps = self.temp_data.get_data()
        
        self.ax.clear()
        if times and temps:
            self.ax.plot(times, temps, 'b-', linewidth=2, label='Temperature')
            
            # Get setpoint temperature and draw horizontal line
            setpoint_text = self.setpoint_temp_value.cget("text")
            if setpoint_text != "-- °C":
                try:
                    setpoint = float(setpoint_text.split()[0])
                    self.ax.axhline(y=setpoint, color='g', linestyle='--', alpha=0.7, label='Setpoint')
                except:
                    pass
        
        self.ax.set_xlabel("Time (seconds)")
        self.ax.set_ylabel("Temperature (°C)")
        self.ax.set_title("Temperature vs Time")
        self.ax.grid(True, alpha=0.3)
        if times and temps:
            self.ax.legend(loc='upper left')
        
        self.canvas.draw()
    
    def set_temperature(self):
        """Set the heater temperature setpoint"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to hotplate first")
            return
        
        try:
            temp = int(self.set_temp_input.get())
            with self.serial_lock:
                result = hw.set_heater_temp(self.ser, temp)
            if result:
                messagebox.showinfo("Success", f"Temperature set to {temp} °C")
            else:
                messagebox.showwarning("Failed", "Failed to set temperature")
        except Exception as e:
            messagebox.showerror("Error", f"Error setting temperature: {str(e)}")
    
    def set_ramp_rate(self):
        """Set the heater ramp rate"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to hotplate first")
            return
        
        try:
            ramp = int(self.set_ramp_input.get())
            with self.serial_lock:
                result = hw.set_heater_ramp(self.ser, ramp)
            if result:
                messagebox.showinfo("Success", f"Ramp rate set to {ramp} °C/hr")
            else:
                messagebox.showwarning("Failed", "Failed to set ramp rate")
        except Exception as e:
            messagebox.showerror("Error", f"Error setting ramp rate: {str(e)}")
    
    def set_stir_speed(self):
        """Set the stirrer speed"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to hotplate first")
            return
        
        try:
            speed = int(self.set_stir_input.get())
            with self.serial_lock:
                if speed == 0:
                    result = hw.set_stir_off(self.ser)
                else:
                    result = hw.set_stir(self.ser, speed)
            
            if speed == 0:
                messagebox.showinfo("Success", "Stirrer turned off")
            elif result:
                messagebox.showinfo("Success", f"Stir speed set to {speed} RPM")
            else:
                messagebox.showwarning("Failed", "Failed to set stir speed")
        except Exception as e:
            messagebox.showerror("Error", f"Error setting stir speed: {str(e)}")
    
    def turn_off_heater(self):
        """Turn off the heater"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to hotplate first")
            return
        
        try:
            with self.serial_lock:
                result = hw.set_heater_off(self.ser)
            if result:
                messagebox.showinfo("Success", "Heater turned off")
            else:
                messagebox.showwarning("Failed", "Failed to turn off heater")
        except Exception as e:
            messagebox.showerror("Error", f"Error turning off heater: {str(e)}")
    
    def turn_off_stirrer(self):
        """Turn off the stirrer"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to hotplate first")
            return
        
        try:
            with self.serial_lock:
                result = hw.set_stir_off(self.ser)
            if result:
                messagebox.showinfo("Success", "Stirrer turned off")
            else:
                messagebox.showwarning("Failed", "Failed to turn off stirrer")
        except Exception as e:
            messagebox.showerror("Error", f"Error turning off stirrer: {str(e)}")
    
    def clear_plot_data(self):
        """Clear temperature plot data"""
        self.temp_data.clear()
        self.update_plot()
        messagebox.showinfo("Success", "Plot data cleared")
    
    def save_csv(self):
        """Save temperature plot data to CSV file"""
        times, temps = self.temp_data.get_data()
        
        if not times or not temps:
            messagebox.showwarning("No Data", "No temperature data to save")
            return
        
        try:
            # Open file dialog to choose save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save Temperature Data"
            )
            
            if file_path:
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Time (seconds)", "Temperature (°C)"])
                    for t, temp in zip(times, temps):
                        writer.writerow([t, temp])
                
                messagebox.showinfo("Success", f"Data saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving CSV: {str(e)}")
    
    def on_closing(self):
        """Handle window close event"""
        # Stop polling thread
        self.polling_stop.set()
        if self.polling_thread and self.polling_thread.is_alive():
            self.polling_thread.join(timeout=2)
        
        if self.connected:
            self.disconnect()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = HotplateGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
