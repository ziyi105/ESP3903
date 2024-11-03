#include <SoftwareSerial.h>

SoftwareSerial Bluetooth(11, 12); // RX, TX for Bluetooth
const int pwmPin = 10;            // PWM output for square wave
const int dischargePin = 9;       // Controls the discharge transistor
const int analogPin_V1 = A0;      // Voltage reading across the Resistor
const int analogPin_V2 = A1;      // Voltage reading across the LED
const int analogPin_V3 = A2;      // Voltage reading across the LED

float voltageData[600]; // Array for voltage data (adjust size if needed)
float currentData[600]; // Array for current data (adjust size if needed)
int dataIndex = 0;      // Track number of data points collected

void setup() {
    pinMode(pwmPin, OUTPUT);
    pinMode(dischargePin, OUTPUT);
    Serial.begin(9600);
    Bluetooth.begin(9600);
}

void loop() {
    // Generate a square wave at ~1kHz
    digitalWrite(pwmPin, HIGH);
    digitalWrite(dischargePin, LOW);
    delayMicroseconds(3000000); // Wait a short time after setting HIGH

    // Collect data for a specific duration or number of samples
    digitalWrite(pwmPin, LOW);
    digitalWrite(dischargePin, HIGH);
    unsigned long startTime = millis();
    while (millis() - startTime < 3000) { // Loop for 3 seconds
        float V1 = analogRead(analogPin_V1) * (5.0 / 1023.0);
        float V2 = analogRead(analogPin_V2) * (5.0 / 1023.0);
        float V3 = analogRead(analogPin_V3) * (5.0 / 1023.0);

        float voltage_LED = V2 - V3;
        float voltage_R = V1 - V2;
        float current_LED = voltage_R / 200;

        if (dataIndex < 600) {  // Prevent overflow
            voltageData[dataIndex] = voltage_LED;
            currentData[dataIndex] = current_LED;
            Serial.println(voltage_LED);
            dataIndex++;
        }
        delay(5);
    }

    Bluetooth.println("START");
    // Send all data over Bluetooth
    for (int i = 0; i < dataIndex; i++) {
        Bluetooth.print(voltageData[i]);
        Bluetooth.print(",");
        Bluetooth.print(currentData[i], 5);
        Bluetooth.println(";");
    }
    
    // Send stop token
    Bluetooth.println("STOP");
    Serial.println("STOP");
    Serial.println(dataIndex);

    // Reset data index for the next collection
    dataIndex = 0;
    delay(100);  // Optional: Delay before the next collection cycle
}
