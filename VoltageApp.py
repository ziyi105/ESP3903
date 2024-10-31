from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.logger import Logger
import serial
import time
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
        self.fig, self.axs = plt.subplots(2, 1)
        self.graph_widget = None  # Placeholder for the graph widget

        # Set data collection duration (in seconds)
        self.collection_duration = 4  # Change this to any desired duration
        
        return self.layout

    def start_data_collection(self, instance):
        self.status_label.text = "Collecting data..."
        self.start_time = time.time()
        self.voltage_data.clear()
        self.current_data.clear()
        self.time_data.clear()

        # Schedule data collection every 0.5 seconds
        self.data_event = Clock.schedule_interval(self.collect_data, 0.1)

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
                            self.time_data.append(current_time)
                            print(f"Received: {voltage} V, {current} A at {current_time:.2f}s")
                        except ValueError:
                            print(f"Error parsing '{reading}'.")

                # Update status label
                self.status_label.text = f"Collected data at {current_time:.2f}s"
            except ValueError:
                self.status_label.text = "Error reading data."
                
    def stop_data_collection(self):
        Clock.unschedule(self.data_event)
        self.status_label.text = "Data collection finished. Generating graphs..."
        print(f"Received: {self.voltage_data}")

        # Plot the graphs: IV curve and V-t curve
        if self.voltage_data and self.current_data:  # Check if there is data to plot
            self.axs[0].clear()  # Clear the first subplot (IV curve)
            self.axs[1].clear()  # Clear the second subplot (V-t curve)

            # IV Curve
            self.axs[0].plot(self.voltage_data, self.current_data, label="IV Curve", marker='o')
            self.axs[0].set_xlabel("Voltage (V)")
            self.axs[0].set_ylabel("Current (A)")
            self.axs[0].set_title("IV Curve")
            self.axs[0].legend()

            # V-t Curve
            self.axs[1].plot(self.time_data, self.voltage_data, label="V-t Curve", color='orange', marker='x')
            self.axs[1].set_xlabel("Time (s)")
            self.axs[1].set_ylabel("Voltage (V)")
            self.axs[1].set_title("Voltage-Time Curve")
            self.axs[1].legend()

            # Create a canvas and draw it
            self.graph_widget = FigureCanvasAgg(self.fig)
            self.graph_widget.draw()

            # Save to a temporary file and load it for display
            self.fig.savefig('temp_graphs.png')
            self.layout.add_widget(Label(text="Graphs generated."))
            self.layout.add_widget(Button(text='Show Graphs', on_press=self.show_graph))
        else:
            self.status_label.text = "No data collected to plot."

    def show_graph(self, instance):
        from kivy.uix.image import Image
        self.layout.add_widget(Image(source='temp_graphs.png'))

if __name__ == "__main__":
    VoltageApp().run()
