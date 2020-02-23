import boto3
import botocore
from time import sleep
import time,sys,picamera
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from time import sleep
import telepot
import dynamodb 
import tweepy

bot_token = '1086735494:AAG_wGblfAH61b_lFtyC-2_aEPBDM0AMa70' 

CONSUMER_KEY = 'rgqUM52O8aJiRTf098k8SsUEx'
CONSUMER_SECRET = 'XrtEvY7jalvm2NhQJgCiSdWkFSW6rFw1Ik69Ry5rCMxdfZOMHM'
ACCESS_KEY = '1191149145601372160-j2IrtLPDR20gGLZLvNcMNu6VSxcctq'
ACCESS_SECRET = 'YGGSnrkElfmNovl7o2K1sGaZyGVJ3I6v5w6mbbMKsmLS5'


auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.secure = True
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

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

my_rpi = AWSIoTMQTTClient("leiPubSub")
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
plantfolder = 'plant/'
flowerfolder = 'flower/'


def plant_pic():
    timestring = time.strftime("%Y-%m-%dT%H_%M_%S", time.gmtime())
    filename = 'plant'+timestring+'.jpg'
    camera.capture('/home/pi/Desktop/plant/'+filename)
    return filename



def upload_plant_to_s3(filename):
    try:
        response = s3.upload_file('/home/pi/Desktop/plant/'+filename, bucket_name, plantfolder + filename, ExtraArgs={'ACL':'public-read'})
        print("Plant File {} uploaded" .format(filename))
        return filename		
    except botocore.exceptions.ClientError as e:
        print(e)
        return False

    

def detect_labels(bucket, key, max_labels=10, min_confidence=60, region="us-east-1"):
    print("Now is detecting ... {} in {}" .format(key, bucket))
    rekognition = boto3.client("rekognition", region)
    response = rekognition.detect_labels(
        Image={
            "S3Object": {
                "Bucket": bucket,
                "Name": key,
            }
        },
        MaxLabels=max_labels,
        MinConfidence=min_confidence,
    )
    return response['Labels']


def plant_detect(file_name, teleUser):
      upload_plant_to_s3(file_name)
      try:
        highestconfidence = 0
        best_bet_item = "Unknown"
        bug_list = ["Insect", "Honey Bee", "Invertebrate", "Bee", "Arachnid", "Spider", "Tick", "Garden Spider", "Animal"]
        for label in detect_labels(bucket_name, plantfolder + file_name):
          print("{Name} - {Confidence}%".format(**label))
          if label["Name"] in bug_list:
             dynamodb.send_url("plant", file_name, teleUser) 
             return True
          else:
             s3.delete_object(Bucket=bucket_name, Key=plantfolder+file_name)
        sleep(1)
      except botocore.exceptions.ClientError as e:
        print(e)
      return False


  
  
  
def flower_detect(teleUser):
      try:
        highestconfidence = 0
        best_bet_item = "Unknown"
        bug_list = ["Insect", "Honey Bee", "Invertebrate", "Bee", "Arachnid", "Spider", "Tick", "Garden Spider", "Animal"]
        for label in detect_labels(bucket_name, flowerfolder + 'tempPic.jpg'):
          print("{Name} - {Confidence}%".format(**label))
          if label["Name"] in bug_list:
            timestring = time.strftime("%Y-%m-%dT%H_%M_%S", time.gmtime())
            filename = 'flower'+timestring+'.jpg'           
            s3.download_file(bucket_name, flowerfolder + 'tempPic.jpg', '/home/pi/Desktop/flower/flower.jpg')
            response = s3.upload_file('/home/pi/Desktop/flower/flower.jpg', bucket_name, flowerfolder + filename, ExtraArgs={'ACL':'public-read'})
            sleep(1)
            dynamodb.send_url("flower", filename, teleUser) 
            print("Flower File {} uploaded" .format(filename))
            return True
          else:
            s3.delete_object(Bucket=bucket_name, Key=flowerfolder + 'tempPic.jpg')
        sleep(1)
      except botocore.exceptions.ClientError as e:
        print(e)
      return False

  
def respondToMsg(msg): 
    chat_id = str(msg['chat']['id'])    
    command = msg['text']     
    teleUser = 'guest'
    if chat_id == '1052517193':
        teleUser = 'jiang lei'
    elif chat_id == '265066192':
        teleUser = 'jorin'	
    else:
        print(chat_id)


    print('Got command: {} from {}'.format(command, chat_id))

    if command == 'plant':
        #my_rpi.publish("telegram/takepicCommand", "plant", 1)
        plant_file = plant_pic()
        bot.sendPhoto(chat_id, photo=open('/home/pi/Desktop/plant/'+plant_file, 'rb'))
        msg = "This is the plant uploaded by {}" .format(teleUser)
        api.update_with_media('/home/pi/Desktop/plant/'+plant_file, status=msg)
    if command == 'flower':
        my_rpi.publish("telegram/takepicCommand", "flower", 1)	
        filename = 'flower.jpg'
        sleep(3)
        bot.sendMessage(chat_id, "Taking picture of flower now!")	 		
        s3.download_file(bucket_name, flowerfolder + 'tempPic.jpg', '/home/pi/Desktop/flower/'+filename)
        bot.sendPhoto(chat_id, photo=open('/home/pi/Desktop/flower/'+filename, 'rb'))
        msg = "This is the flower uploaded by {}" .format(teleUser)
        api.update_with_media('/home/pi/Desktop/flower/'+filename, status=msg)
    if command == 'detect':
        loop = 1
        noBug = True
        plantBug = False
        flowerBug = False
        while loop < 6:
          #detect plant bug
          if not plantBug:
            bot.sendMessage(chat_id, "Detecting plant now...({}/5)" .format(loop))
            plant_file = plant_pic()
            plant_bug = plant_detect(plant_file, teleUser)
            if plant_bug:
               noBug = False
               plantBug = True
               bot.sendMessage(chat_id, "Your plant is detected with a bug! Please be alert!")
               bot.sendPhoto(chat_id, photo=open('/home/pi/Desktop/plant/'+plant_file, 'rb'))

          sleep(3)
          
          #detect flower bug 
          if not flowerBug:
            my_rpi.publish("telegram/takepicCommand", "flower", 1)
            sleep(5)
            bot.sendMessage(chat_id, "Detecting flower now...({}/5)" .format(loop))
            flower_bug = flower_detect(teleUser)
            if flower_bug:
               noBug = False	 	
               flowerBug = True	
               sleep(1)			   
               bot.sendMessage(chat_id, "Your flower is detected with a bug! Please be alert!")
               bot.sendPhoto(chat_id, photo=open('/home/pi/Desktop/flower/flower.jpg', 'rb'))

          loop = loop + 1

        if noBug:
          bot.sendMessage(chat_id, "There is no bug bothering your plant and flower! Don't worry!")	
        else:
          bot.sendMessage(chat_id, "Detection is completed!")	

bot = telepot.Bot(bot_token)
bot.message_loop(respondToMsg)

while True:
    sleep(1) 



	



