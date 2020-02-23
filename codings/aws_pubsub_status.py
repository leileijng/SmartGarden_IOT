# Import SDK packages
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import boto3
from boto3.dynamodb.conditions import Key, Attr
import serial
from time import sleep
import datetime as dt
from datetime import date


# Get serial to fetch data from arduino
ser = serial.Serial('/dev/ttyUSB0', 9600)

def customCallback(client, userdata, message):
  print("Received a new message: ")
  print(message.payload)
  print("from topic: ")
  print(message.topic)
  print("--------------\n\n")


host = "a3nh2xwizsyh7i-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "rootca.pem"
certificatePath = "certificate.pem.crt"
privateKeyPath = "private.pem.key"

my_rpi = AWSIoTMQTTClient("basicPubSub")
my_rpi.configureEndpoint(host, 8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi.connect()
my_rpi.subscribe("smartgarden/statusTable", 1, customCallback)
sleep(1)

# Publish to the same topic in a loop forever
loopCount = 0
while True:
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('statusTable')
    response = table.query(KeyConditionExpression=Key('id').eq('id_status'),ScanIndexForward=False)
    items = response['Items']

    n=1
    data = items[:n]
    uStatus = data[0]['status']
    status = uStatus.encode('latin-1')
    print(status)
    ser.write(status)
    sleep(2)