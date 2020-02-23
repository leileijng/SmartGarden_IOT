import boto3
import botocore
from time import sleep
import time,sys,picamera
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep


def customCallback(client, userdata, message):
  print("Received a new message: ")
  print(message.payload)
  print("from topic: ")
  print(message.topic)
  print("--------------\n\n")
  if message.payload == 'flower':
    upload_flower_to_s3()
    
  
host = "a3nh2xwizsyh7i-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "rootca.pem"
certificatePath = "certificate.pem.crt"
privateKeyPath = "private.pem.key"

my_rpi = AWSIoTMQTTClient("jorinPubSub")
my_rpi.configureEndpoint(host, 8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi.connect()
my_rpi.subscribe("smartgarden/uploadpic/plant", 1, customCallback)
my_rpi.subscribe("telegram/takepicCommand", 1, customCallback)

camera = picamera.PiCamera()

s3 = boto3.client('s3')
bucket_name = 'smartgarden-wonderwoman' 
flowerfolder = 'flower/'


def flower_pic():
    timestring = time.strftime("%Y-%m-%dT%H_%M_%S", time.gmtime())
    filename = 'flower.jpg'
    camera.capture('/home/pi/Desktop/flower/'+filename)
    return filename



def upload_flower_to_s3():
    try:
        filename = flower_pic()
        response = s3.upload_file('/home/pi/Desktop/flower/'+filename, bucket_name, flowerfolder + 'tempPic', ExtraArgs={'ACL':'public-read'})
        print("File {} uploaded" .format(filename))
        return filename		
    except botocore.exceptions.ClientError as e:
        print(e)
        return False

		
while True:
    sleep(1) 
    
