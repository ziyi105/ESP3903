from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
import serial
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

class VoltageApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        
        # Start button
        self.start_button = Button(text='Start Data Collection')
        self.start_button.bind(on_press=self.start_data_collection)
        self.layout.add_widget(self.start_button)

        # Status label
        self.status_label = Label(text="Press 'Start' to begin")
        self.layout.add_widget(self.status_label)

        # Serial connection setup for HC-05
        # self.port = "/dev/tty.HC-05"  # Mac
        self.port = "COM5"  # Windows
        self.baudrate = 9600
        
        # Try to establish the serial connection
        self.serial_conn = None
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            if self.serial_conn.is_open:
                self.status_label.text = f"Connected to {self.port}"
            else:
                self.status_label.text = "Connection failed."
        except serial.SerialException as e:
            self.status_label.text = f"Error opening serial port: {e}"
            return self.layout  # Exit if unable to connect

        # Placeholder for voltage data and time
        self.voltage_data = []
        self.current_data = []
        self.time_data = []

        # Initialize plot
        self.fig, self.ax = plt.subplots()
        self.graph_widget = None  # Placeholder for the graph widget

        # Set data collection duration (in seconds)
        self.collection_duration = 60  # Change this to any desired duration
        
        return self.layout

    def start_data_collection(self, instance):
        self.status_label.text = "Collecting data..."
        self.start_time = time.time()
        self.voltage_data.clear()
        self.current_data.clear()
        self.time_data.clear()

        # Schedule data collection every 0.5 seconds
        self.data_event = Clock.schedule_interval(self.collect_data, 0.5)

    def collect_data(self, dt):
        current_time = time.time() - self.start_time
        if current_time >= self.collection_duration:  # Stop after set duration
            self.stop_data_collection()
            return
        
        # Read data from HC-05
        if self.serial_conn.in_waiting > 0:
            try:
                # Read and decode the data, then split it based on delimiter ";"
                raw_data = self.serial_conn.readline().decode('utf-8').strip()
                readings = raw_data.split(";")  # Split by semicolon delimiter
                print(f"Received: {readings}")

                # Process each reading (voltage,current)
                for reading in readings:
                    if reading:  # Ensure the reading is not empty
                        try:
                            voltage_str, current_str = reading.split(",")
                            voltage = float(voltage_str)
                            current = float(current_str)
                            self.voltage_data.append(voltage)
                            self.current_data.append(current)
                            print(f"Received: {voltage} V, {current} A at {current_time:.2f}s")
                        except ValueError:
                            print(f"Error parsing '{reading}'.")

                # Update status label
                self.status_label.text = f"Collected data at {current_time:.2f}s"
            except ValueError:
                self.status_label.text = "Error reading data."
                
    def stop_data_collection(self):
        Clock.unschedule(self.data_event)
        self.status_label.text = "Data collection finished. Generating graph..."
        print(f"Received: {self.voltage_data}")

        # Plot the graph as an IV curve
        if self.voltage_data and self.current_data:  # Check if there is data to plot
            self.ax.clear()
            self.ax.plot(self.voltage_data, self.current_data, label="IV Curve", marker='o')
            self.ax.set_xlabel("Voltage (V)")
            self.ax.set_ylabel("Current (A)")
            self.ax.set_title("IV Curve")
            self.ax.legend()

            # Create a canvas and draw it
            self.graph_widget = FigureCanvasAgg(self.fig)
            self.graph_widget.draw()

            # Save to a temporary file and load it for display
            self.fig.savefig('temp_graph.png')
            self.layout.add_widget(Label(text="Graph generated."))
            self.layout.add_widget(Button(text='Show Graph', on_press=self.show_graph))
        else:
            self.status_label.text = "No data collected to plot."

    def show_graph(self, instance):
        from kivy.uix.image import Image
        self.layout.add_widget(Image(source='temp_graph.png'))

if __name__ == "__main__":
    VoltageApp().run()
