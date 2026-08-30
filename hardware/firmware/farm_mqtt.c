#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "ohos_init.h"
#include "cmsis_os2.h"
#include "wifi_connect.h"
#include "MQTTClient.h"
#include "cJSON.h"
#include "E53_IA1.h"

#define WIFI_SSID  "1"
#define WIFI_PWD   "68680077"

#define MQTT_HOST  "8.137.105.88"
#define MQTT_PORT  1883

#define UUID_TEMP  "3b8dcefd-3a51-4adc-b452-47c184c0951d"
#define UUID_MOIST "814621f7-2561-49ad-9766-72d3fcd18d86"
#define UUID_IRRIG "435106ba-01e7-4745-9646-3907d15b28df"

#define TOPIC_TEMP_DATA  "sensor/3b8dcefd-3a51-4adc-b452-47c184c0951d/data"
#define TOPIC_MOIST_DATA "sensor/814621f7-2561-49ad-9766-72d3fcd18d86/data"
#define TOPIC_CMD  "sensor/cmd"
#define TOPIC_ACK  "sensor/ack"

E53_IA1_Data_TypeDef E53_IA1_Data;

static unsigned char sendBuf[2048];
static unsigned char readBuf[2048];
static Network network;
static MQTTClient mqttClient;
static unsigned int g_ackSeq = 1000;

void messageArrived(MessageData *data);

static int reconnect_mqtt(void)
{
    int rc;

    printf("MQTT reconnecting...\r\n");

    if (network.my_socket > 0) {
        NetworkDisconnect(&network);
        network.my_socket = 0;
    }

    rc = NetworkConnect(&network, MQTT_HOST, MQTT_PORT);
    if (rc != 0) {
        printf("reconnect net fail rc=%d\r\n", rc);
        return -1;
    }

    MQTTClientInit(&mqttClient, &network, 1000, sendBuf, sizeof(sendBuf), readBuf, sizeof(readBuf));

    MQTTString clientId = MQTTString_initializer;
    clientId.cstring = "bearpi-farm";

    MQTTPacket_connectData connectData = MQTTPacket_connectData_initializer;
    connectData.clientID = clientId;
    connectData.willFlag = 0;
    connectData.MQTTVersion = 3;
    connectData.keepAliveInterval = 60;
    connectData.cleansession = 1;

    rc = MQTTConnect(&mqttClient, &connectData);
    if (rc != 0) {
        printf("reconnect MQTT fail rc=%d\r\n", rc);
        return -1;
    }

    rc = MQTTSubscribe(&mqttClient, TOPIC_CMD, 1, messageArrived);
    if (rc != 0) {
        printf("reconnect sub fail rc=%d\r\n", rc);
        return -1;
    }

    printf("MQTT reconnected\r\n");
    return 0;
}

static unsigned long get_ts_ms(void)
{
    return (unsigned long)osKernelGetTickCount() * 10UL;
}

static void publish_ack(unsigned int cmdSeq, const char *sw)
{
    char ack[512];
    snprintf(ack, sizeof(ack),
        "{\"seq\":%u,\"cmdSeq\":%u,\"action\":\"control\",\"deviceId\":\"%s\",\"result\":\"ok\",\"switch\":\"%s\",\"name\":\"P001-IRRIG\"}",
        g_ackSeq, cmdSeq, UUID_IRRIG, sw);
    g_ackSeq++;

    MQTTMessage msg;
    msg.qos = 1;
    msg.retained = 0;
    msg.payload = ack;
    msg.payloadlen = strlen(ack);
    MQTTPublish(&mqttClient, TOPIC_ACK, &msg);
    printf("ACK: %s\r\n", ack);
}

void messageArrived(MessageData *data)
{
    char *buf = (char *)malloc(data->message->payloadlen + 1);
    if (buf == NULL) {
        return;
    }
    memcpy(buf, data->message->payload, data->message->payloadlen);
    buf[data->message->payloadlen] = '\0';
    printf("CMD: %s\r\n", buf);

    cJSON *root = cJSON_Parse(buf);
    if (root == NULL) {
        free(buf);
        return;
    }

    cJSON *deviceId = cJSON_GetObjectItem(root, "deviceId");
    cJSON *sw = cJSON_GetObjectItem(root, "switch");
    cJSON *seq = cJSON_GetObjectItem(root, "seq");

    if (deviceId != NULL && sw != NULL && seq != NULL &&
        cJSON_IsString(deviceId) && cJSON_IsString(sw) &&
        strcmp(deviceId->valuestring, UUID_IRRIG) == 0) {
        if (strcmp(sw->valuestring, "on") == 0) {
            Motor_StatusSet(ON);
        } else if (strcmp(sw->valuestring, "off") == 0) {
            Motor_StatusSet(OFF);
        }
        unsigned int cmdSeq = 0;
        if (cJSON_IsNumber(seq)) {
            cmdSeq = (unsigned int)seq->valueint;
        }
        publish_ack(cmdSeq, sw->valuestring);
    }

    cJSON_Delete(root);
    free(buf);
}

static void FarmMQTTTask(void)
{
    WifiConnect(WIFI_SSID, WIFI_PWD);
    printf("WiFi OK, connect MQTT...\r\n");

    int rc;
    NetworkInit(&network);

    for (;;) {
        rc = NetworkConnect(&network, MQTT_HOST, MQTT_PORT);
        if (rc == 0) {
            break;
        }
        printf("network connect retry...\r\n");
        osDelay(20);    /* 20 tick = 200ms（tick=10ms） */
    }

    MQTTClientInit(&mqttClient, &network, 1000, sendBuf, sizeof(sendBuf), readBuf, sizeof(readBuf));

    MQTTString clientId = MQTTString_initializer;
    clientId.cstring = "bearpi-farm";

    MQTTPacket_connectData connectData = MQTTPacket_connectData_initializer;
    connectData.clientID = clientId;
    connectData.willFlag = 0;
    connectData.MQTTVersion = 3;
    connectData.keepAliveInterval = 60;
    connectData.cleansession = 1;

    rc = MQTTConnect(&mqttClient, &connectData);
    if (rc != 0) {
        printf("MQTT connect fail %d\r\n", rc);
        return;
    }
    printf("MQTT connected\r\n");

    rc = MQTTSubscribe(&mqttClient, TOPIC_CMD, 1, messageArrived);
    if (rc != 0) {
        printf("subscribe fail %d\r\n", rc);
        return;
    }
    printf("subscribed %s\r\n", TOPIC_CMD);

    E53_IA1_Init();

    int pub_fail = 0;

    while (1) {
        E53_IA1_Read_Data();

        unsigned long ts = get_ts_ms();
        char payload[256];
        MQTTMessage msg;
        msg.qos = 1;    /* QoS1: 等回执才能检测断线，死了好触发重连 */
        msg.retained = 0;

        snprintf(payload, sizeof(payload),
            "{\"temperature\":%.2f,\"deviceId\":\"%s\",\"timestamp\":%lu,\"msgId\":\"%lu\"}",
            E53_IA1_Data.Temperature, UUID_TEMP, ts, ts);
        msg.payload = payload;
        msg.payloadlen = strlen(payload);
        int r1 = MQTTPublish(&mqttClient, TOPIC_TEMP_DATA, &msg);
        if (r1 != 0) {
            printf("pub temp fail %d\r\n", r1);
        }

        snprintf(payload, sizeof(payload),
            "{\"plot_moisture\":%.2f,\"deviceId\":\"%s\",\"timestamp\":%lu,\"msgId\":\"%lu\"}",
            E53_IA1_Data.Humidity, UUID_MOIST, ts, ts);
        msg.payload = payload;
        msg.payloadlen = strlen(payload);
        int r2 = MQTTPublish(&mqttClient, TOPIC_MOIST_DATA, &msg);
        if (r2 != 0) {
            printf("pub moist fail %d\r\n", r2);
        }

        printf("pub temp=%.2f hum=%.2f\r\n", E53_IA1_Data.Temperature, E53_IA1_Data.Humidity);

        MQTTYield(&mqttClient, 100);

        if (r1 != 0 || r2 != 0) {
            pub_fail++;
            if (pub_fail >= 3) {
                pub_fail = 0;
                printf("link dead, entering reconnect loop...\r\n");
                while (reconnect_mqtt() != 0) {
                    osDelay(100);    /* 100 tick = 1s：阻塞重试直到连回 */
                }
            }
            osDelay(10);             /* 10 tick = 100ms：失败后立刻再试 */
        } else {
            pub_fail = 0;
            osDelay(200);            /* 200 tick = 2s：成功后按 2 秒节奏发 */
        }
    }
}

static void FarmMQTT(void)
{
    osThreadAttr_t attr;
    attr.name = "FarmMQTTTask";
    attr.attr_bits = 0U;
    attr.cb_mem = NULL;
    attr.cb_size = 0U;
    attr.stack_mem = NULL;
    attr.stack_size = 10240;
    attr.priority = osPriorityNormal;

    if (osThreadNew((osThreadFunc_t)FarmMQTTTask, NULL, &attr) == NULL) {
        printf("create FarmMQTTTask fail\r\n");
    }
}

APP_FEATURE_INIT(FarmMQTT);
