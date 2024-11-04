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
        self.layout = BoxLayout(orientation='vertical')
        
        # Start button
        self.start_button = Button(text='Start Data Collection')
        self.start_button.bind(on_press=self.start_data_collection)
        self.layout.add_widget(self.start_button)

        # Status label
        self.status_label = Label(text="Press 'Start' to begin")
        self.layout.add_widget(self.status_label)

        # Serial connection setup for HC-05
        self.port = "COM5"  # Windows
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

        # Placeholder for voltage and current data
        self.voltage_data = []
        self.current_data = []

        return self.layout

    def start_data_collection(self, instance):
        self.status_label.text = "Waiting for START token..."
        self.voltage_data.clear()
        self.current_data.clear()

        # Start listening for the START token
        self.start_event = Clock.schedule_interval(self.wait_for_start_token, 0.001)

    def wait_for_start_token(self, dt):
        # Read data from Bluetooth
        if self.serial_conn.in_waiting > 0:
            raw_data = self.serial_conn.readline().decode('utf-8').strip()
            if raw_data == "START":
                self.status_label.text = "Collecting data..."
                self.start_data_collection_proceed()
                Clock.unschedule(self.start_event)

    def start_data_collection_proceed(self):
        # Schedule data collection
        self.data_event = Clock.schedule_interval(self.collect_data, 0.1)

    def collect_data(self, dt):
        # Read data from Bluetooth
        if self.serial_conn.in_waiting > 0:
            raw_data = self.serial_conn.readline().decode('utf-8').strip()
            
            # Check if received the stop token
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


        # Plot V-t Curve
        if self.voltage_data:
            plt.figure()
            plt.plot(self.voltage_data, label="Voltage (V)")
            plt.xlabel("Data Points")
            plt.ylabel("Voltage (V)")
            plt.title("Voltage-Time Curve")
            plt.legend()
            plt.savefig('temp_vt_graph.png')
            plt.close()

            # Plot I-V Curve
            plt.figure()
            plt.plot(self.voltage_data, self.current_data, label="Current (A)")
            plt.xlabel("Voltage (V)")
            plt.ylabel("Current (A)")
            plt.title("Current-Voltage Curve")
            plt.legend()
            plt.savefig('temp_iv_graph.png')
            plt.close()

            # Calculate Planck's constant
            self.calculate_planck_constant()

            # Display buttons to show graphs
            self.layout.add_widget(Label(text="Graphs generated."))
            self.layout.add_widget(Button(text='Show V-t Graph', on_press=self.show_vt_graph))
            self.layout.add_widget(Button(text='Show I-V Graph', on_press=self.show_iv_graph))
        else:
            self.status_label.text = "No data collected to plot."

    def calculate_planck_constant(self):
        # Define LED frequency (or wavelength)
        frequency = 4.90338e14  # in Hz, example value; replace with your LED frequency
        
        # Convert voltage and current data to numpy arrays for processing
        voltages = np.array(self.voltage_data)
        currents = np.array(self.current_data)
        
        # Filter for the linear region (adjust threshold as necessary)
        linear_region_mask = currents > 0.005  # Example threshold to detect significant current
        linear_voltages = voltages[linear_region_mask]
        linear_currents = currents[linear_region_mask]

        # Linear fit for the linear region
        if len(linear_voltages) > 1:
            slope, intercept = np.polyfit(linear_voltages, linear_currents, 1)
            threshold_voltage = -intercept / slope  # Extrapolate to find threshold voltage

            # Calculate Planck's constant
            e = 1.602e-19  # Elementary charge in Coulombs
            h = (e * threshold_voltage) / frequency  # Planck's constant in J·s
            
            # Display calculated Planck's constant
            self.layout.add_widget(Label(text=f"Estimated Planck's constant: {h:.4e} J·s"))
            print("length of voltage data: ", len(self.voltage_data))
            print("length of current data: ", len(self.current_data))
            print(f"Threshold Voltage: {threshold_voltage:.2f} V")
            print(f"Calculated Planck's constant: {h:.4e} J·s")
        else:
            self.layout.add_widget(Label(text="Insufficient data for Planck's constant calculation."))

    def show_vt_graph(self, instance):
        self.layout.add_widget(Image(source='temp_vt_graph.png'))

    def show_iv_graph(self, instance):
        self.layout.add_widget(Image(source='temp_iv_graph.png'))

if __name__ == "__main__":
    VoltageApp().run()
