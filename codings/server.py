from flask import Flask, render_template, jsonify,  url_for, redirect, request,Response, session

import mysql.connector
import sys

import json
import numpy
import datetime
import decimal

import dynamodb as awsdb
import gevent
import gevent.monkey
from gevent.pywsgi import WSGIServer
import os

							
app = Flask(__name__)
gevent.monkey.patch_all()
app.secret_key = os.urandom(12)

print('The server is running!')

class GenericEncoder(json.JSONEncoder):
  def default(self, obj):  
    if isinstance(obj, numpy.generic):
      return numpy.asscalar(obj) 
    elif isinstance(obj, datetime.datetime):  
      return obj.strftime('%Y-%m-%d %H:%M:%S') 
    elif isinstance(obj, decimal.Decimal):
      return float(obj)
    else:  
      return json.JSONEncoder.default(self, obj) 

def data_to_json(data):
  json_data = json.dumps(data,cls=GenericEncoder)
  return json_data

	
	
@app.route("/login.html")
def login():
  return render_template('login.html')
	

# pages
@app.route("/")
@app.route("/index.html")
def dashboard():
  if not session.get('logged_in'):
    return redirect(url_for('login'))
  else:
    return render_template('index.html')

  
  
@app.route("/charts.html")
def graph():
  if not session.get('logged_in'):
    return redirect(url_for('login'))
  else:
    return render_template('/charts.html')

  
@app.route("/tables.html")
def table():
  if not session.get('logged_in'):
    return redirect(url_for('login'))
  else:
    return render_template('/tables.html')
  
  
@app.route("/gallery.html")
def gallery():
  if not session.get('logged_in'):
    return redirect(url_for('login'))
  else:
    return render_template('/gallery.html')

	

@app.route("/api/verify/<name>/<password>", methods=['POST', 'GET'])
def verify(name,password):
  if request.method == 'POST':
    try:
      data = awsdb.login()
      loggedin = False
      for user in data:
        print(user['username'])
        print(user['password'])	
      	if user['username'] == name and user['password'] == password:
          loggedin = True
          session['logged_in'] = True
          return ("success")
      if loggedin == False:
        return ("fail")
    except:
      print(sys.exc_info()[0])
      print(sys.exc_info()[1])
      return None



@app.route("/logout")
def logout():
  session.pop('logged_in', None)
  return redirect(url_for('login')) 
  
# api routes
@app.route("/api/getData", methods=['POST', 'GET'])
def api_getData():
  if request.method == 'POST':
    try:
      data = data_to_json(awsdb.get_data())
      loaded_data = json.loads(data)
      print(loaded_data)
      return jsonify(loaded_data)
    except:
      print(sys.exc_info()[0])
      print(sys.exc_info()[1])
      return None


@app.route("/api/status", methods=['GET', 'POST'])
def status():
  if request.method == 'POST':
    try:
      data = data_to_json(awsdb.get_status())
      loaded_data = json.loads(data)
      print(loaded_data)
      return jsonify(loaded_data)
    except:
      print(sys.exc_info()[0])
      print(sys.exc_info()[1])
      return None


	  
	  
@app.route("/api/getChart", methods=['POST', 'GET'])
def api_getChartData():
  if request.method == 'POST':
    try:
      data = data_to_json(awsdb.get_chart_data())
      loaded_data = json.loads(data)
      print(loaded_data)
      return jsonify(loaded_data)
    except:
      print(sys.exc_info()[0])
      print(sys.exc_info()[1])
      return None
	  	
	
		
@app.route("/api/changeStatus/<status>", methods=['GET', 'POST'])
def changeStatus(status):
  if request.method == 'POST':
    try:
      awsdb.send_status(status)
      print(status)
      return status
    except:
      print(sys.exc_info()[0])
      print(sys.exc_info()[1])
      return None


	
    
@app.route("/api/getAllStatus", methods=['POST', 'GET'])
def getAllStatus():
  if request.method == 'POST':
    try:
      data = data_to_json(awsdb.get_all_status())
      loaded_data = json.loads(data)
      print(loaded_data)
      return jsonify(loaded_data)
    except:
      print(sys.exc_info()[0])
      print(sys.exc_info()[1])
      return None

  

@app.route("/api/getImg/<type>", methods=['POST', 'GET'])
def getImg(type):
  if request.method == 'POST':
    try:
      data = data_to_json(awsdb.get_Img_url(type))
      loaded_data = json.loads(data)
      print(loaded_data)
      return jsonify(loaded_data)
    except:
      print(sys.exc_info()[0])
      print(sys.exc_info()[1])
      return None
	


	
if __name__ == '__main__':
  try:
    http_server = WSGIServer(('0.0.0.0', 8009), app)
    app.debug = True
    http_server.serve_forever()
    print('Server waiting for requests')
  except:
    print("Exception")
    print(sys.exc_info()[0])
    print(sys.exc_info()[1])