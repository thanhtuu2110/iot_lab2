import serial.tools.list_ports
import json
import time
import paho.mqtt.client as mqttclient
print("IoT Gateway")

BROKER_ADDRESS = "demo.thingsboard.io"
PORT = 1883
mess = ""

# TODO: Add your token and your comport
# Please check the comport in the device manager
THINGS_BOARD_ACCESS_TOKEN = "DoBTfBtTOGceKXL2cVu4"
bbc_port = "/dev/cu.usbmodem14402"
if len(bbc_port) > 0:
    ser = serial.Serial(port=bbc_port, baudrate=115200)

let cmd = ""
serial.onDataReceived(serial.delimiters(Delimiters.Hash), function() {
    cmd=serial.readUntil(serial.delimiters(Delimiters.Hash))
    basic.showString(cmd)
    if (cmd == "0") {
        basic.showIcon(IconNames.No)
    } else if (cmd == "1") {
        basic.showIcon(IconNames.Happy)
    } else if (cmd == "2") {
        basic.showIcon(IconNames.StickFigure)
    } else if (cmd == "3") {
        basic.showIcon(IconNames.Yes)
    }
})
basic.forever(function() {
    serial.writeString("!1:TEMP:" + input.temperature() + "#")
    basic.pause(5000)
    serial.writeString("!1:LIGHT:" + input.lightLevel() + "#")
    basic.pause(5000)
})


def processData(data):
    data = data.replace("!", "")
    data = data.replace("#", "")
    seperateData = data.split(":")
    processedData = dict()
    # TODO: Add your source code to publish data to the server
    if(seperateData[1] == "TEMP"):
        processedData["temperature"] = seperateData[-1]
    elif (seperateData[1] == "LIGHT"):
        processedData["light"] = seperateData[-1]
    client.publish('v1/devices/me/telemetry', json.dumps(processedData), 1)


def readSerial():
    bytesToRead = ser.inWaiting()
    if (bytesToRead > 0):
        global mess
        mess = mess + ser.read(bytesToRead).decode("UTF-8")
        while ("#" in mess) and ("!" in mess):
            start = mess.find("!")
            end = mess.find("#")
            processData(mess[start:end + 1])
            if (end == len(mess)):
                mess = ""
            else:
                mess = mess[end+1:]


def subscribed(client, userdata, mid, granted_qos):
    print("Subscribed successfully")


def recv_message(client, userdata, message):
    print("Received: ", message.payload.decode("utf-8"))
    temp_data = dict()
    cmd = -1
 # TODO: Update the cmd to control 2 devices
    global LED_SIG
    global FAN_SIG
    try:
        jsonobj = json.loads(message.payload)

        if jsonobj['method'] == "setLED":
            temp_data['led'] = jsonobj['payload']
            LED_SIG = jsonobj['payload']
            client.publish('v1/devices/me/attributes',
                           json.dumps(temp_data), 1)
        if jsonobj['method'] == "setFAN":
            temp_data['fan'] = jsonobj['payload']
            FAN_SIG = jsonobj['payload']
            client.publish('v1/devices/me/attributes',
                           json.dumps(temp_data), 1)

        print(f"led signal: {LED_SIG}, fan signal: {FAN_SIG}")
        if LED_SIG and FAN_SIG:
            cmd = 0
        if LED_SIG and not FAN_SIG:
            cmd = 1
        if not LED_SIG and FAN_SIG:
            cmd = 2
        if not LED_SIG and not FAN_SIG:
            cmd = 3

    except:
        pass

    if len(bbc_port) > 0:
        ser.write((str(cmd) + "#").encode())


def connected(client, usedata, flags, rc):
    if rc == 0:
        print("Thingsboard connected successfully!!")
        client.subscribe("v1/devices/me/rpc/request/+")
    else:
        print("Connection is failed")


client = mqttclient.Client("Gateway_Thingsboard")
client.username_pw_set(THINGS_BOARD_ACCESS_TOKEN)

client.on_connect = connected
client.connect(BROKER_ADDRESS, 1883)
client.loop_start()

client.on_subscribe = subscribed
client.on_message = recv_message


while True:

    if len(bbc_port) > 0:
        readSerial()

    time.sleep(0.5)
