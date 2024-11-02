  #include <SoftwareSerial.h>

  SoftwareSerial Bluetooth(11, 12); // RX, TX for Bluetooth
  const int pwmPin = 10; // PWM output for square wave
  const int dischargePin = 9; // Controls the discharge transistor
  const int analogPin_V1 = A0; // Voltage reading across the Resistor
  const int analogPin_V2 = A1; // Voltage reading across the LED
  const int analogPin_V3 = A2; // Voltage reading across the LED

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

    // Average multiple readings for accuracy
    float voltage_LED;
    float voltage_R;
    float V1 = analogRead(analogPin_V1) * (5.0 / 1023.0);
    float V2 = analogRead(analogPin_V2) * (5.0 / 1023.0);
    float V3 = analogRead(analogPin_V3) * (5.0 / 1023.0);
    voltage_LED = V2 - V3;
    voltage_R = V1 - V2;

    Serial.print("analogPin_LED when HIGH: ");
    Serial.println(voltage_LED);
    Serial.print("analogPin_R when HIGH: ");
    Serial.println(voltage_R);
    delayMicroseconds(30000); // Wait a short time after setting LOW

    digitalWrite(pwmPin, LOW);
    digitalWrite(dischargePin, HIGH); // Turn off the discharge transistor when the square wave is LOW

    // Print values every 10 milliseconds for the duration of 3 seconds (3000 milliseconds)
    unsigned long startTime = millis();
    while (millis() - startTime < 3000) { // Loop for 3 seconds

        // Read voltages
        float V1 = analogRead(analogPin_V1) * (5.0 / 1023.0);
        float V2 = analogRead(analogPin_V2) * (5.0 / 1023.0);
        float V3 = analogRead(analogPin_V3) * (5.0 / 1023.0);

        // Calculate voltage differences
        float voltage_LED = V2 - V3;
        float voltage_R = V1 - V2;
        float current_LED = voltage_R / 200;

        // Print values
        Serial.print("analogPin_LED when LOW: ");
        Serial.println(voltage_LED);
        Serial.print("analogPin_R when LOW: ");
        Serial.println(voltage_R);
        // Bluetooth.print("analogPin_LED when LOW: ");
        Bluetooth.print(voltage_LED);
        Bluetooth.print(",");
        Bluetooth.print(current_LED);
        Bluetooth.println(";");
        // Bluetooth.print("analogPin_R when LOW: ");
        // Bluetooth.println(voltage_R);

        delay(5);
    }

  }
