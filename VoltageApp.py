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
        
        # Create a status label first
        self.status_label = Label(text="Connecting...", size_hint=(1, None), height=50)
        self.layout.add_widget(self.status_label)

        # Create a box layout for centering the button
        self.center_layout = BoxLayout(orientation='vertical', size_hint=(1, None), height=200)
        self.start_button = Button(text='Start Data Collection', size_hint=(1, None), size=(200, 50), height=50)
        self.start_button.bind(on_press=self.start_data_collection)
        self.center_layout.add_widget(self.start_button)

        self.start_instruction = Label(text="Press 'Start' to begin", size_hint=(1, None), height=50)
        self.center_layout.add_widget(self.start_instruction)

        self.layout.add_widget(self.center_layout)

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
        # Remove the start button after it is pressed
        self.center_layout.remove_widget(self.start_button)
        self.center_layout.remove_widget(self.start_instruction)
        
        self.status_label.text = "Waiting for START token..."
        self.voltage_data.clear()
        self.current_data.clear()

        # Start listening for the START token
        self.start_event = Clock.schedule_interval(self.wait_for_start_token, 0.01)

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
        self.calculate_planck_constant()

        # Plot V-t Curve
        if self.voltage_data:
            voltages = np.array(self.voltage_data)
            currents = np.array(self.current_data)

            # Detect the threshold voltage
            voltage_diffs = np.diff(voltages)
            decay_threshold = -0.05  # Adjust based on observed decay rate
            threshold_index = np.argmax(voltage_diffs < decay_threshold)
            if threshold_index > 0:
                threshold_voltage = voltages[threshold_index]
            else:
                threshold_voltage = None  # Handle case where threshold is not detected

            # V-t plot with threshold voltage marked
            plt.figure()
            plt.plot(self.voltage_data, self.current_data, label="Current (A)")
            if threshold_voltage is not None:
                plt.axvline(x=threshold_index, color='r', linestyle='--', label=f"Threshold Voltage ({threshold_voltage:.2f} V)")
            plt.xlabel("Data Points")
            plt.ylabel("Voltage (V)")
            plt.title("Voltage-Time Curve")
            plt.legend()
            plt.savefig('temp_vt_graph.png')
            plt.close()

            # I-V plot with threshold voltage marked
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

            # Display buttons to show graphs
            self.layout.add_widget(Label(text="Graphs generated."))
            self.show_iv_button = Button(text='Show V-t Graph', on_press=self.show_vt_graph)
            self.layout.add_widget(self.show_iv_button)
            self.show_vt_button = Button(text='Show I-V Graph', on_press=self.show_iv_graph)
            self.layout.add_widget(self.show_vt_button)
        else:
            self.status_label.text = "No data collected to plot."

    def calculate_planck_constant(self):
        # Define LED frequency (or wavelength)
        frequency = 4.90338e14  # in Hz, example value; replace with your LED frequency
        
        # Convert voltage data to numpy array for processing
        voltages = np.array(self.voltage_data)
        
        # Approximate the threshold voltage by detecting the change in decay rate
        if len(voltages) > 1:
            # Calculate the difference between consecutive voltage readings to detect decay rate change
            voltage_diffs = np.diff(voltages)
            print(voltage_diffs)
            
            # Find the point where the decay rate changes significantly
            # This threshold can be fine-tuned based on observed data
            decay_threshold = -0.05  # Example threshold for rate of decay change
            threshold_index = np.argmax(voltage_diffs < decay_threshold)
            
            if threshold_index > 0:
                # Get the threshold voltage at the point of rate change
                threshold_voltage = voltages[threshold_index]
                
                # Calculate Planck's constant
                e = 1.602e-19  # Elementary charge in Coulombs
                h = (e * threshold_voltage) / frequency  # Planck's constant in J·s
                
                # Display calculated Planck's constant
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
