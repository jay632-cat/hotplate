######## Hotplate Communication Code #######
# Author: Jerry A. Yang
# Date: Oct 26, 2025

import hotplate_wrapper
import sys
import re
import time
from datetime import datetime
from contextlib import nullcontext

def parse_recipe_file(input_file):
    with open(input_file, 'r') as file:
        lines = file.readlines()
        lines = [line.strip() for line in lines if line.strip()]
    commands = [line for line in lines if not line.strip().startswith("#")]

    for onecmd in commands:
        numbers = re.findall(r"-?\d+", onecmd)
        onecmd_values = list(map(int, numbers))
        if len(onecmd_values) != 5:
            raise Exception("File invalid - not all commands have 5 inputs!")

    return commands

def _lock_context(serial_lock):
    return serial_lock if serial_lock else nullcontext()

def run_recipe(ser, input_file, progress_callback=None, stop_event=None, continue_event=None, serial_lock=None):
    commands = parse_recipe_file(input_file)
    total_steps = len(commands)

    if progress_callback:
        progress_callback({
            "type": "start",
            "file": input_file,
            "total_steps": total_steps
        })

    for step_index, onecmd in enumerate(commands, start=1):
        if stop_event and stop_event.is_set():
            if progress_callback:
                progress_callback({"type": "cancelled"})
            return

        numbers = re.findall(r"-?\d+", onecmd)
        onecmd_values = list(map(int, numbers))

        if progress_callback:
            progress_callback({
                "type": "step_start",
                "step": step_index,
                "total_steps": total_steps,
                "target_temp": onecmd_values[0],
                "ramp_rate": onecmd_values[1],
                "stir_speed": onecmd_values[2],
                "dwell_seconds": onecmd_values[3],
                "stabilize": onecmd_values[4]
            })

        with _lock_context(serial_lock):
            hotplate_wrapper.set_heater_temp(ser, onecmd_values[0])
            hotplate_wrapper.set_heater_ramp(ser, onecmd_values[1])
            hotplate_wrapper.set_stir(ser, onecmd_values[2])

        # Stabilization routine - Poll plate to check temp
        printtemp = 0
        last5temps = []
        if progress_callback:
            progress_callback({"type": "stabilizing_start", "step": step_index})
        while True:
            if stop_event and stop_event.is_set():
                if progress_callback:
                    progress_callback({"type": "cancelled"})
                return

            if onecmd_values[3] < 0:
                break

            with _lock_context(serial_lock):
                curtemp = hotplate_wrapper.get_temp(ser)

            if printtemp == 5:
                last5temps.append(curtemp)
                print(last5temps)
                printtemp = 0
                if len(last5temps) > 5:
                    last5temps.pop(0)
                if progress_callback:
                    progress_callback({
                        "type": "stabilizing",
                        "step": step_index,
                        "temp": curtemp
                    })

                if (onecmd_values[4] == 1 and len(last5temps) > 4
                    and all(x >= last5temps[0]-1 and x <= last5temps[0]+1 for x in last5temps)
                    and last5temps[0] >= onecmd_values[0]-1
                    and last5temps[0] <= onecmd_values[0]+1):
                        break

                if onecmd_values[4] == 0 and curtemp >= onecmd_values[0]-2 and curtemp <= onecmd_values[0]+2:
                    break

            printtemp = printtemp + 1
            time.sleep(0.2)

        # Start dwell timer when stabilized at temp
        if onecmd_values[3] < 0:
            if progress_callback:
                progress_callback({"type": "await_continue", "step": step_index})
            if continue_event:
                while True:
                    if stop_event and stop_event.is_set():
                        if progress_callback:
                            progress_callback({"type": "cancelled"})
                        return
                    if continue_event.wait(timeout=0.2):
                        continue_event.clear()
                        break
            else:
                return
        else:
            dwell_seconds = onecmd_values[3]
            start_time = time.time()
            if progress_callback:
                progress_callback({"type": "dwell_start", "step": step_index, "dwell_seconds": dwell_seconds})
            while True:
                if stop_event and stop_event.is_set():
                    if progress_callback:
                        progress_callback({"type": "cancelled"})
                    return
                elapsed = time.time() - start_time
                if elapsed >= dwell_seconds:
                    break
                remaining = max(0, int(dwell_seconds - elapsed))
                if progress_callback:
                    progress_callback({
                        "type": "dwell_tick",
                        "step": step_index,
                        "remaining": remaining
                    })
                time.sleep(1)

    if progress_callback:
        progress_callback({"type": "done"})
