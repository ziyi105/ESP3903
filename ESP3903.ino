#include <SoftwareSerial.h>

SoftwareSerial Bluetooth(11, 12); // RX, TX for Bluetooth
const int pwmPin = 10; // PWM output for square wave
const int dischargePin = 9; // Controls the discharge transistor
const int analogPin_V1 = A0; // Voltage reading across the Resistor
const int analogPin_V2 = A1; // Voltage reading across the LED
const int analogPin_V3 = A2; // Voltage reading across the LED

// Arrays to store data
float voltageArray[100];
float currentArray[100];
int dataIndex = 0; // Index for storing data

void setup() {
    pinMode(pwmPin, OUTPUT);
    pinMode(dischargePin, OUTPUT);
    Serial.begin(9600);
    Bluetooth.begin(9600);
}

void loop() {
    dataIndex = 0; // Reset data index at the start of each loop

    // Generate a square wave at ~1kHz
    digitalWrite(pwmPin, HIGH);
    digitalWrite(dischargePin, LOW);
    delayMicroseconds(3000000); // Wait a short time after setting HIGH

    // Collect data for 3 seconds
    unsigned long startTime = millis();
    while (millis() - startTime < 3000 && dataIndex < 100) { // Loop for 3 seconds or until array is full

        // Read voltages
        float V1 = analogRead(analogPin_V1) * (5.0 / 1023.0);
        float V2 = analogRead(analogPin_V2) * (5.0 / 1023.0);
        float V3 = analogRead(analogPin_V3) * (5.0 / 1023.0);

        // Calculate voltage differences
        float voltage_LED = V2 - V3;
        float voltage_R = V1 - V2;
        float current_LED = voltage_R / 200; // Calculate current

        // Store in arrays
        voltageArray[dataIndex] = voltage_LED;
        currentArray[dataIndex] = current_LED;
        dataIndex++;

        delay(1); // Delay to control sampling rate
    }

    digitalWrite(pwmPin, LOW);
    digitalWrite(dischargePin, HIGH); // Turn off discharge transistor when square wave is LOW

    // Send collected data via Bluetooth
    for (int i = 0; i < dataIndex; i++) {
        Bluetooth.print(voltageArray[i]);
        Bluetooth.print(",");
        Bluetooth.print(currentArray[i]);
        Bluetooth.println(";");
    }

    delay(3000); // Delay before starting the next loop
}
