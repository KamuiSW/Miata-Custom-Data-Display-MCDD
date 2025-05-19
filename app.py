import obd
import time
from datetime import datetime

intRPM = 3000

def get_acceleration(speed_prev, speed_current, time_delta):
    if speed_prev is None or time_delta <= 0:
        return 0.0

    speed_prev_ms = speed_prev * 1000 / 3600
    speed_current_ms = speed_current * 1000 / 3600
    return (speed_current_ms - speed_prev_ms) / time_delta

def main():
    connection = obd.OBD()
    # connection = obd.OBD("bt://00:1D:A5:68:98:8B")  #Bluetooth
    
    if not connection.is_connected():
        print("Failed to connect to OBD-II adapter")
        return

    print("Connected to OBD-II adapter")

    cmd_rpm = obd.commands.RPM
    cmd_speed = obd.commands.SPEED
    cmd_throttle = obd.commands.THROTTLE_POS
    cmd_engine_load = obd.commands.ENGINE_LOAD
    cmd_coolant_temp = obd.commands.COOLANT_TEMP

    prev_speed = None
    prev_time = datetime.now()
    last_dtc_check = datetime.now()
    dtc_check_interval = 5  # Check DTCs every 5 seconds

    try:
        while True:
            current_time = datetime.now()
            time_delta = (current_time - prev_time).total_seconds()
            prev_time = current_time

            # Check DTC's
            if (current_time - last_dtc_check).total_seconds() >= dtc_check_interval:
                dtc_response = connection.query(obd.commands.GET_DTC)
                print("\n--- Checking Diagnostic Trouble Codes (DTCs) ---")
                if not dtc_response.is_null():
                    dtcs = dtc_response.value
                    if dtcs:
                        print("Found DTCs:")
                        for dtc in dtcs:
                            print(f"  {dtc.code}")
                    else:
                        print("No DTCs detected.")
                else:
                    print("Unable to retrieve DTCs.")
                last_dtc_check = current_time

            rpm = connection.query(cmd_rpm)
            speed = connection.query(cmd_speed)
            throttle = connection.query(cmd_throttle)
            engine_load = connection.query(cmd_engine_load)
            coolant_temp = connection.query(cmd_coolant_temp)

            print("\n--- Vehicle Data ---")
            
            if not rpm.is_null():
                print(f"RPM: {rpm.value.magnitude:.1f}")
            
            if not speed.is_null():
                speed_value = speed.value.magnitude
                print(f"Speed: {speed_value:.1f} kph")

                if prev_speed is not None:
                    acceleration = get_acceleration(prev_speed, speed_value, time_delta)
                    print(f"Acceleration: {acceleration:.2f} m/s²")
                prev_speed = speed_value
            
            if not throttle.is_null():
                print(f"Throttle Position: {throttle.value.magnitude:.1f}%")
            
            if not engine_load.is_null():
                print(f"Engine Load: {engine_load.value.magnitude:.1f}%")
            
            if not coolant_temp.is_null():
                print(f"Coolant Temp: {coolant_temp.value.magnitude:.1f}°C")

            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        connection.close()

if __name__ == "__main__":
    main()