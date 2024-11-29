from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.logger import Logger
import serial
import matplotlib.pyplot as plt
from kivy.uix.image import Image
import numpy as np

class VoltageApp(App):
    def build(self):
        Logger.setLevel('WARNING')
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.status_label = Label(text="Connecting...", size_hint=(1, None), height=50)
        self.layout.add_widget(self.status_label)

        self.center_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=200)
        self.start_button = Button(text='Start Data Collection', size_hint=(1, None), size=(200, 50), height=50)
        self.start_button.bind(on_press=self.start_data_collection)
        self.center_layout.add_widget(self.start_button)

        self.start_instruction = Label(text="Press 'Start' to begin", size_hint=(1, None), height=50)
        self.center_layout.add_widget(self.start_instruction)

        self.layout.add_widget(self.center_layout)

        self.port = "COM5"
        self.baudrate = 9600
        
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            if self.serial_conn.is_open:
                self.status_label.text = f"Connected to {self.port}"
            else:
                self.status_label.text = "Connection failed."
        except serial.SerialException as e:
            self.status_label.text = f"Error opening serial port: {e}"
            return self.layout

        self.voltage_data = []
        self.current_data = []

        return self.layout

    def start_data_collection(self, instance):
        self.center_layout.remove_widget(self.start_button)
        self.center_layout.remove_widget(self.start_instruction)
        
        self.status_label.text = "Waiting for START token..."
        self.voltage_data.clear()
        self.current_data.clear()

        self.start_event = Clock.schedule_interval(self.wait_for_start_token, 0.01)

    def wait_for_start_token(self, dt):
        if self.serial_conn.in_waiting > 0:
            raw_data = self.serial_conn.readline().decode('utf-8').strip()
            if raw_data == "START":
                self.status_label.text = "Collecting data..."
                self.start_data_collection_proceed()
                Clock.unschedule(self.start_event)

    def start_data_collection_proceed(self):
        self.data_event = Clock.schedule_interval(self.collect_data, 0.1)

    def collect_data(self, dt):
        if self.serial_conn.in_waiting > 0:
            raw_data = self.serial_conn.readline().decode('utf-8').strip()
            
            if raw_data == "STOP":
                print(len(self.voltage_data))
                self.stop_data_collection()
                return
            
            readings = raw_data.split(";")
            for reading in readings:
                if reading:
                    try:
                        voltage_str, current_str = reading.split(",")
                        voltage = float(voltage_str)
                        current = float(current_str)
                        self.voltage_data.append(voltage)
                        self.current_data.append(current)
                    except ValueError:
                        print(f"Error parsing '{reading}'.")

    def stop_data_collection(self):
        Clock.unschedule(self.data_event)
        self.status_label.text = "Data collection finished. Generating graphs..."
        self.calculate_planck_constant()

        if self.voltage_data:
            voltages = np.array(self.voltage_data)
            currents = np.array(self.current_data)

            voltage_diffs = np.diff(voltages)
            decay_threshold = -0.05  
            threshold_index = np.argmax(voltage_diffs < decay_threshold)
            if threshold_index > 0:
                threshold_voltage = voltages[threshold_index]
            else:
                threshold_voltage = None  

            plt.figure()
            plt.plot(voltages, label="Voltage (V)")
            if threshold_voltage is not None:
                plt.axvline(x=threshold_index, color='r', linestyle='--', label=f"Threshold Voltage ({threshold_voltage:.2f} V)")
            plt.xlabel("Data Points")
            plt.ylabel("Voltage (V)")
            plt.title("Voltage-Time Curve")
            plt.legend()
            plt.savefig('temp_vt_graph.png')
            plt.close()

            plt.figure()
            plt.plot(voltages, currents, label="Current (A)")
            if threshold_voltage is not None:
                plt.axvline(x=threshold_voltage, color='r', linestyle='--', label=f"Threshold Voltage ({threshold_voltage:.2f} V)")
            plt.xlabel("Voltage (V)")
            plt.ylabel("Current (A)")
            plt.title("Current-Voltage Curve")
            plt.legend()
            plt.savefig('temp_iv_graph.png')
            plt.close()

            self.layout.add_widget(Label(text="Graphs generated."))
            self.show_iv_button = Button(text='Show V-t Graph', on_press=self.show_vt_graph)
            self.layout.add_widget(self.show_iv_button)
            self.show_vt_button = Button(text='Show I-V Graph', on_press=self.show_iv_graph)
            self.layout.add_widget(self.show_vt_button)
        else:
            self.status_label.text = "No data collected to plot."

    def calculate_planck_constant(self):
        wavelength = 611.4e-9 
        frequency = 299792458 / wavelength
        
        voltages = np.array(self.voltage_data)
        
        if len(voltages) > 1:
            voltage_diffs = np.diff(voltages)
            
            baseline_values = voltage_diffs[len(voltage_diffs) - 60:]
            baseline_std_dev = np.std(baseline_values)
            decay_threshold = 15 * baseline_std_dev
            
            significant_changes = np.where(np.abs(voltage_diffs)[30:] > decay_threshold)[0]
            
            if len(significant_changes) > 0:
                threshold_voltage = voltages[significant_changes[0]]
                
                e = 1.602e-19
                h = (e * threshold_voltage) / frequency 
                
                self.layout.add_widget(Label(text=f"Threshold Voltage: {threshold_voltage:.2f} V"))
                self.layout.add_widget(Label(text=f"Estimated Planck's constant: {h:.4e} J·s"))
                print(f"Threshold Voltage: {threshold_voltage:.2f} V")
                print(f"Calculated Planck's constant: {h:.4e} J·s")
            else:
                self.layout.add_widget(Label(text="Unable to determine threshold voltage from data."))
                print("Error: Unable to detect significant change in decay rate for threshold voltage calculation.")
        else:
            self.layout.add_widget(Label(text="Insufficient data for Planck's constant calculation."))

    def show_vt_graph(self, instance):
        self.layout.remove_widget(self.show_iv_button)
        self.layout.add_widget(Image(source='temp_vt_graph.png'))

    def show_iv_graph(self, instance):
        self.layout.remove_widget(self.show_vt_button)
        self.layout.add_widget(Image(source='temp_iv_graph.png'))

if __name__ == "__main__":
    VoltageApp().run()
