#define LED_RED 4
#define LED_GREEN 2

String current_received_data = "clear";
String last_received_data = "clear";

typedef enum {
    ENABLE,
    DISABLE,
    IDEL
}state;

state indicator_state = DISABLE;
 
void setup() {
    Serial.begin(115200);
    pinMode(LED_RED, OUTPUT);
    pinMode(LED_GREEN, OUTPUT);

    digitalWrite(LED_RED, LOW);
    digitalWrite(LED_GREEN, HIGH);

}

void loop() {

    if (Serial.available()>0){
        current_received_data = Serial.readStringUntil('\n');
        Serial.println(current_received_data);
        if (current_received_data == "detected" && last_received_data == "clear"){
            indicator_state = ENABLE;
            last_received_data = current_received_data;
        }
        if (current_received_data == "clear" && last_received_data == "detected"){
            indicator_state = DISABLE;
            last_received_data = current_received_data;
        }
    }
    switch (indicator_state){
    case ENABLE:
        digitalWrite(LED_RED, HIGH);
        digitalWrite(LED_GREEN, LOW);
        indicator_state = IDEL;
        break;
    case DISABLE:
        digitalWrite(LED_RED, LOW);
        digitalWrite(LED_GREEN, HIGH);
        indicator_state = IDEL;
        break;
    default:
        break;
    }
}
