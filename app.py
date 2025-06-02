import tkinter as tk
from tkinter import ttk
import obd
import time
from datetime import datetime
import RPi.GPIO as GPIO

MODE_BUTTON_PIN = 17

class OBDDisplay:
    def __init__(self, master, connection):
        self.master = master
        self.connection = connection
        self.current_mode = 0  # 0=Basic, 1=Advanced, 2=DTC
        self.dtc_check_interval = 5  # Seconds
        self.last_dtc_check = datetime.now()
        
        #GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(MODE_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(MODE_BUTTON_PIN, GPIO.FALLING, 
                            callback=self.switch_mode, bouncetime=200)

        self.rpm_var = tk.StringVar(value="N/A")
        self.speed_var = tk.StringVar(value="N/A")
        self.accel_var = tk.StringVar(value="N/A")
        self.throttle_var = tk.StringVar(value="N/A")
        self.load_var = tk.StringVar(value="N/A")
        self.temp_var = tk.StringVar(value="N/A")
        self.dtc_var = tk.StringVar(value="No DTCs")

        self.create_basic_frame()
        self.create_advanced_frame()
        self.create_dtc_frame()
        self.show_frame()

        self.update_data()

    def create_basic_frame(self):
        self.frame_basic = ttk.Frame(self.master)
        
        ttk.Label(self.frame_basic, text="RPM:", font=('Arial', 20)).grid(row=0, column=0, padx=10, pady=10)
        ttk.Label(self.frame_basic, textvariable=self.rpm_var, font=('Arial', 20)).grid(row=0, column=1)
        
        ttk.Label(self.frame_basic, text="Speed:", font=('Arial', 20)).grid(row=1, column=0)
        ttk.Label(self.frame_basic, textvariable=self.speed_var, font=('Arial', 20)).grid(row=1, column=1)
        
        ttk.Label(self.frame_basic, text="Accel:", font=('Arial', 20)).grid(row=2, column=0)
        ttk.Label(self.frame_basic, textvariable=self.accel_var, font=('Arial', 20)).grid(row=2, column=1)

    def create_advanced_frame(self):
        self.frame_advanced = ttk.Frame(self.master)
        
        ttk.Label(self.frame_advanced, text="Throttle:", font=('Arial', 20)).grid(row=0, column=0, padx=10, pady=10)
        ttk.Label(self.frame_advanced, textvariable=self.throttle_var, font=('Arial', 20)).grid(row=0, column=1)
        
        ttk.Label(self.frame_advanced, text="Engine Load:", font=('Arial', 20)).grid(row=1, column=0)
        ttk.Label(self.frame_advanced, textvariable=self.load_var, font=('Arial', 20)).grid(row=1, column=1)
        
        ttk.Label(self.frame_advanced, text="Coolant Temp:", font=('Arial', 20)).grid(row=2, column=0)
        ttk.Label(self.frame_advanced, textvariable=self.temp_var, font=('Arial', 20)).grid(row=2, column=1)

    def create_dtc_frame(self):
        self.frame_dtc = ttk.Frame(self.master)
        ttk.Label(self.frame_dtc, text="Diagnostic Trouble Codes:", 
                font=('Arial', 16)).pack(pady=10)
        ttk.Label(self.frame_dtc, textvariable=self.dtc_var, 
                font=('Arial', 14), wraplength=300).pack(pady=10)

    def show_frame(self):
        for frame in [self.frame_basic, self.frame_advanced, self.frame_dtc]:
            frame.pack_forget()
        
        if self.current_mode == 0:
            self.frame_basic.pack(fill=tk.BOTH, expand=True)
        elif self.current_mode == 1:
            self.frame_advanced.pack(fill=tk.BOTH, expand=True)
        elif self.current_mode == 2:
            self.frame_dtc.pack(fill=tk.BOTH, expand=True)

    def switch_mode(self, channel=None):
        self.current_mode = (self.current_mode + 1) % 3
        self.show_frame()

    def get_acceleration(self, speed_prev, speed_current, time_delta):
        if speed_prev is None or time_delta <= 0:
            return 0.0
        return (speed_current*1000/3600 - speed_prev*1000/3600) / time_delta

    def update_data(self):
        now = datetime.now()
        
        # Get regular data
        rpm = self.connection.query(obd.commands.RPM).value.magnitude
        speed = self.connection.query(obd.commands.SPEED).value.magnitude
        throttle = self.connection.query(obd.commands.THROTTLE_POS).value.magnitude
        engine_load = self.connection.query(obd.commands.ENGINE_LOAD).value.magnitude
        coolant_temp = self.connection.query(obd.commands.COOLANT_TEMP).value.magnitude
        
        # Calculate acceleration
        acceleration = self.get_acceleration(
            getattr(self, 'prev_speed', None),
            speed,
            (now - getattr(self, 'prev_time', now)).total_seconds()
        )
        self.prev_speed = speed
        self.prev_time = now

        if (now - self.last_dtc_check).total_seconds() >= self.dtc_check_interval:
            dtc_response = self.connection.query(obd.commands.GET_DTC)
            if not dtc_response.is_null():
                dtcs = dtc_response.value
                self.dtc_var.set("\n".join([dtc.code for dtc in dtcs]) if dtcs else "No DTCs")
            self.last_dtc_check = now

        self.rpm_var.set(f"{rpm:.1f}" if rpm else "N/A")
        self.speed_var.set(f"{speed:.1f}" if speed else "N/A")
        self.accel_var.set(f"{acceleration:.2f}" if acceleration else "N/A")
        self.throttle_var.set(f"{throttle:.1f}%" if throttle else "N/A")
        self.load_var.set(f"{engine_load:.1f}%" if engine_load else "N/A")
        self.temp_var.set(f"{coolant_temp:.1f}°C" if coolant_temp else "N/A")

        self.master.after(1000, self.update_data)

def main():
    connection = obd.OBD()
    if not connection.is_connected():
        print("Failed to connect to OBD-II adapter")
        return

    root = tk.Tk()
    root.geometry("320x240")
    OBDDisplay(root, connection)
    root.mainloop()

    connection.close()
    GPIO.cleanup()

if __name__ == "__main__":
    main()