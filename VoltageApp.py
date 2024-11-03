from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.logger import Logger
import serial
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

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
        self.status_label.text = "Collecting data..."
        self.voltage_data.clear()
        self.current_data.clear()

        # Schedule data collection
        self.data_event = Clock.schedule_interval(self.collect_data, 0.5)

    def collect_data(self, dt):
        # Read data from Bluetooth
        if self.serial_conn.in_waiting > 0:
            raw_data = self.serial_conn.readline().decode('utf-8').strip()
            
            # Check if received the stop token
            if raw_data == "STOP":
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
        self.status_label.text = "Data collection finished. Generating graph..."

        # Plot V-t Curve
        if self.voltage_data:
            plt.plot(self.voltage_data, label="Voltage (V)")
            plt.xlabel("Data Points")
            plt.ylabel("Voltage (V)")
            plt.title("Voltage-Time Curve")
            plt.legend()

            # Save to a temporary file and load it for display
            plt.savefig('temp_vt_graph.png')
            self.layout.add_widget(Label(text="Graph generated."))
            self.layout.add_widget(Button(text='Show Graph', on_press=self.show_graph))
        else:
            self.status_label.text = "No data collected to plot."

    def show_graph(self, instance):
        from kivy.uix.image import Image
        self.layout.add_widget(Image(source='temp_vt_graph.png'))

if __name__ == "__main__":
    VoltageApp().run()