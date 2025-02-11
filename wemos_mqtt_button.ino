#include <WiFi.h>
#include <PubSubClient.h>

// ✅ WiFi 连接信息
const char* ssid = "Leo";  
const char* password = "12345678";

// ✅ MQTT 服务器信息
const char* mqtt_server = "172.20.10.10";  // 你的 MQTT 服务器 IP
const int mqtt_port = 1883;                 // MQTT 默认端口
const char* mqtt_topic = "xarm/move";       // 发送 MQTT 消息的主题

WiFiClient espClient;
PubSubClient client(espClient);

// ✅ 按钮引脚
#define PIN 4        // 使用GPIO4
const int buttonPin = PIN;  // 按钮 GPIO
int lastButtonState = HIGH;  // 记录上次按钮状态
bool buttonPressed = false;  // 按钮是否已触发
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;  // 50ms 按钮去抖动时间

// ✅ 连接 WiFi
void setup_wifi() {
    delay(10);
    Serial.println("正在连接WiFi...");
    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\n✅ WiFi 连接成功！");
    Serial.print("IP 地址: ");
    Serial.println(WiFi.localIP());
}

// ✅ 连接 MQTT 服务器
void reconnect_mqtt() {
    while (!client.connected()) {
        Serial.print("尝试连接MQTT...");
        if (client.connect("ESP32_Client")) {
            Serial.println("✅ MQTT 连接成功！");
            client.publish(mqtt_topic, "ESP32 上线！");  // 连接成功后发送上线消息
        } else {
            Serial.print("❌ 连接失败，状态码: ");
            Serial.print(client.state());
            Serial.println("，5 秒后重试...");
            delay(5000);
        }
    }
}

void setup() {
    Serial.begin(115200);
    setup_wifi();
    client.setServer(mqtt_server, mqtt_port);  // 设置 MQTT 服务器
    reconnect_mqtt();
    pinMode(buttonPin, INPUT_PULLUP);  // 配置按钮引脚，使用内部上拉电阻
}

void loop() {
    if (!client.connected()) {
        reconnect_mqtt();
    }
    client.loop();

    // ✅ 读取按钮状态
    int reading = digitalRead(buttonPin);

    // ✅ 处理按钮去抖动
    if (reading != lastButtonState) {
        lastDebounceTime = millis();  // 记录去抖时间
    }

    if ((millis() - lastDebounceTime) > debounceDelay) {
        // ✅ 只在按钮按下时触发一次（LOW）
        if (reading == LOW && !buttonPressed) {
            Serial.println("📩 按钮被按下，发送 MQTT 消息！");
            client.publish(mqtt_topic, "2");  // 发送 MQTT 消息
            buttonPressed = true;  // 标记按钮已经触发
        }
        // ✅ 释放按钮后，允许再次触发
        else if (reading == HIGH) {
            buttonPressed = false;
        }
    }

    lastButtonState = reading;  // 更新按钮状态
}