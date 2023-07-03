
#include <HardwareSerial.h>

#define LED_RED 4
#define LED_GREEN 2
#define BUZZER 5

String current_received_data = "clear";
String last_received_data = "clear";
typedef enum 
{
    ENABLE,
    DISABLE,
    IDEL
}state;

state indicator_state = DISABLE;
HardwareSerial mySerial(2);  
void setup() {
    Serial.begin(115200);
    // Set the baud rate for the SoftwareSerial object
    mySerial.begin(115200);
    pinMode(LED_RED, OUTPUT);
    pinMode(LED_GREEN, OUTPUT);
    pinMode(BUZZER, OUTPUT);

    digitalWrite(LED_RED, LOW);
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(BUZZER, LOW);
}

void loop() {
    // Serial.println("test");
    if (Serial.available()>0)
    {
        current_received_data = Serial.readStringUntil('\n');
        Serial.println(current_received_data);
        mySerial.printf("current_received_data: %s and Last received data %s\n", current_received_data, last_received_data);
        if (current_received_data == "detected" && last_received_data == "clear")
        {
            // Serial.println("detected");
            mySerial.println("State Changes New State: Enable\n");
            indicator_state = ENABLE;
            last_received_data = current_received_data;
        }
        if (current_received_data == "clear" && last_received_data == "detected")
        {
            mySerial.println("State Changes New State: Disable\n");
            indicator_state = DISABLE;
            last_received_data = current_received_data;
        }
    }
    switch (indicator_state)
    {
    case ENABLE:
        digitalWrite(LED_RED, HIGH);
        digitalWrite(LED_GREEN, LOW);
        digitalWrite(BUZZER, HIGH);
        indicator_state = IDEL;
        break;
    case DISABLE:
        digitalWrite(LED_RED, LOW);
        digitalWrite(LED_GREEN, HIGH);
        digitalWrite(BUZZER, LOW);
        indicator_state = IDEL;
        break;
    default:
        break;
    }
    // delay(100);
}
