from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.garden.matplotlib import FigureCanvasKivyAgg
import serial
import time
import matplotlib.pyplot as plt

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
        self.port = "/dev/rfcomm0"  # Change this for Windows (e.g., "COM5")
        self.baudrate = 9600

        self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)

        # Placeholder for voltage data and time
        self.voltage_data = []
        self.time_data = []

        # Initialize plot
        self.fig, self.ax = plt.subplots()
        self.graph_widget = FigureCanvasKivyAgg(self.fig)
        self.layout.add_widget(self.graph_widget)
        
        return self.layout

    def start_data_collection(self, instance):
        self.status_label.text = "Collecting data..."
        self.start_time = time.time()
        self.voltage_data.clear()
        self.time_data.clear()
        
        # Schedule data collection every 0.5 seconds
        self.data_event = Clock.schedule_interval(self.collect_data, 0.5)

    def collect_data(self, dt):
        current_time = time.time() - self.start_time
        if current_time >= 10:  # Stop after 10 seconds
            self.stop_data_collection()
            return
        
        # Read data from HC-05
        if self.serial_conn.in_waiting > 0:
            try:
                data = float(self.serial_conn.readline().decode().strip())
                self.voltage_data.append(data)
                self.time_data.append(current_time)
                self.status_label.text = f"Collected data: {data} V at {current_time:.2f}s"
            except ValueError:
                self.status_label.text = "Error reading data."
    
    def stop_data_collection(self):
        Clock.unschedule(self.data_event)
        self.status_label.text = "Data collection finished. Generating graph..."

        # Plot the graph
        self.ax.clear()
        self.ax.plot(self.time_data, self.voltage_data, label="Voltage (V)")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Voltage (V)")
        self.ax.set_title("V-t Graph")
        self.ax.legend()
        
        # Update Kivy graph widget
        self.graph_widget.draw()
        self.status_label.text = "Graph generated."

if __name__ == "__main__":
    VoltageApp().run()
