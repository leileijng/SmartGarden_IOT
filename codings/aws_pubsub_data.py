# Import SDK packages
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import serial
from rpi_lcd import LCD
from time import sleep
import datetime as datetime
import json
from gpiozero import MCP3008
import sys
import boto3
from boto3.dynamodb.conditions import Key, Attr
import datetime as dt
from twilio.rest import Client

# Get serial to fetch data from arduino
ser = serial.Serial('/dev/ttyUSB0', 9600)
lcd = LCD()


# Your Account Sid and Auth Token from twilio.com/console
account_sid = 'ACb3a865f797efbffebae721bd693d69ec'
auth_token = '2f71fbc7ff3887815c5937e2067bad1d'
client = Client(account_sid, auth_token)

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
my_rpi.subscribe("smartgarden/user", 1, customCallback)
my_rpi.subscribe("smartgarden/data", 1, customCallback)
my_rpi.subscribe("sensor/moisture", 1, customCallback)
my_rpi.subscribe("sensor/light", 1, customCallback)
sleep(2)

# Publish to the same topic in a loop forever
loopCount = 0
update = True
while update:
  try:
    temp = ser.readline().strip('\r\n')
    hum = ser.readline().strip('\r\n')
    soil = ser.readline().strip('\r\n')
    light = ser.readline().strip('\r\n')
    cardUser = ser.readline().strip('\r\n')

    
    temp = float(temp)
    hum = float(hum)
    soil = float(soil)
    light = float(light)
	
    print("Temp: {}" .format(temp))
    print("Humidity: {}" .format(hum))
    print("Soil: {}" .format(soil))
    print("light: {}" .format(light))	
    print("card user is {}" .format(cardUser))

    if cardUser != "NoCard":
       lcd.text('Welcome', 1)
       lcd.text('{}' .format(cardUser), 2)	 
       messageTosend="Hi {}, now the temperature is {}, humidity is {}, soil moisture is {}, light level is {}".format(cardUser, temp, hum, soil, light)
       message = client.messages.create(body=messageTosend,from_='whatsapp:+14155238886',to='whatsapp:+6594235289')	   
       sleep(2)
       lcd.clear()
	   
    lcd.text('Temp: {}'.format(temp), 1)
    lcd.text('Humidity: {}'.format(hum), 2)
    sleep(1)
    lcd.clear()
	
    lcd.text('Soil: {}'.format(soil), 1)
    lcd.text('Light: {}'.format(light), 2)
    sleep(2)
    lcd.clear()

    loopCount = loopCount+1
    sleep(1)
    print('This is {} record'.format(loopCount))       
    print()

    message = {}
    message["id"] = "id_smartgarden"
    now = datetime.datetime.now()
    message["datetimeid"] = now.isoformat()      
    message["temperature"] = temp
    message["humidity"] = hum
    message["soil"] = soil
    message["light"] = light
    my_rpi.publish("smartgarden/data", json.dumps(message), 1)
    
    if soil >= 700:	
      msg = "Your plant is too dry now, the soil moisture value is " + str(soil) + ". Please on the water pump!"
      my_rpi.publish("sensor/moisture", msg, 1)  

    if light < 600:	
      msg = "There is not enough light for the plant, the light level value is " + str(light) + "."
      my_rpi.publish("sensor/light", msg, 1)  
	  
  except:
    print(sys.exc_info()[0])
    print(sys.exc_info()[1])