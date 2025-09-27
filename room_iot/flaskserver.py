# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, url_for, session, copy_current_request_context, Response, redirect
from flask_socketio import SocketIO, emit, disconnect
from threading import Thread, Lock
import socket
import time
from urllib.request import urlopen
import json
import MySQLdb
import datetime
import pytz
#from urllib.parse import urlparse
from urllib.parse import unquote

utc_now = pytz.utc.localize(datetime.datetime.utcnow())
currentDT = utc_now.astimezone(pytz.timezone("Asia/Singapore"))
#DATE = currentDT.strftime("%Y-%m-%d")

HTTP_PORT = 5000
sqlIP = "localhost"
db = MySQLdb.connect(host=sqlIP, user="iotadmin", passwd="20Pooler", db="db_hvac")
cursor = db.cursor()

async_mode = None
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, async_mode=async_mode)
#thread = None
#thread_lock = Lock()


def get_station1():
    """ call openweathermap api"""
    response = urlopen('http://api.openweathermap.org/data/2.5/weather?q=singapore&appid=1060acc7e4b1d2666') #put your city ID number at the end
    mydata = response.read()
    print("Weather map: ", mydata)
    return mydata

#@app.route("/")
#def index():
#   return app.send_static_file("index2.html")

@app.route('/')
def index():
    
    return render_template('index_new.html', async_mode=socketio.async_mode)

@app.route('/set_temp')
def set_temp():
    #return "set temp"
    return render_template('set_temp.html', async_mode=socketio.async_mode)

@app.route('/set_comfort')
def set_comfort():
    #return "set comfort"
    return render_template('set_comfort.html', async_mode=socketio.async_mode)

@app.route('/view_prototype')
def view_prototype():
    return render_template('view_prototype.html', async_mode=socketio.async_mode) 

@app.route('/ahu_and_chiller')
def ahu_and_chiller():
    #return "set comfort"
    return render_template('ahu_and_chiller.html', async_mode=socketio.async_mode)

@app.route('/check_data')
def check_data():
    return render_template('check_data.html', async_mode=socketio.async_mode)

@app.route('/check_data_process', methods=['GET', 'POST'])
def check_data_process():
    if request.method == 'POST':
        titlelabel = "Temperature vs. Date-Time"
        db2 = MySQLdb.connect(host=sqlIP, user="iotadmin", passwd="20Pooler", db="db_hvac")
        cursor = db2.cursor()
        listdate = []
        result_date = []
        result_temp = []
        result_hum = []
        result_co2 = []
        result_lux = []
        result_occ = []
        result_av = []
        result_ap = []
        result_oat = []
        selected_dates = request.form.get('packeddates')
        selectedDateListStr = unquote(selected_dates)
        dataSplit = list(selectedDateListStr.split(','))
        print('Retrieved: ', dataSplit)
        if dataSplit==[''] or dataSplit==['none']:
            return redirect(url_for('check_data'))
        #data_split = dataSplit.sort(key=lambda date:dt.strptime(date, '%Y-%m-%d'))
        data_split = sorted(dataSplit, key=lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))
        for i in range(len(data_split)):
            listdate.append(data_split[i])
        print("User selected dates: ", listdate)
        for k in listdate:
            print(k)
            selectStatement = "SELECT * FROM db_sensors WHERE DATE(dateandtime)='%s'" % k
            cursor.execute(selectStatement)
            results = cursor.fetchall()
            for row in results:
                result_date.append(row[0])
                result_temp.append(row[2])
                result_hum.append(row[3])
                result_co2.append(row[4])
                result_lux.append(row[5])
                result_occ.append(row[6])
                result_av.append(row[7])
                result_ap.append(row[8])
                result_oat.append(row[9])
            
        return render_template('check_data_process.html', async_mode=socketio.async_mode, \
            values_temperature = result_temp, labels_temperature = result_date, \
            values_humidity = result_hum, labels_humidity = result_date, \
            values_co2 = result_co2, labels_co2 = result_date, \
            values_lux = result_lux, labels_lux = result_date, \
            values_occ = result_occ, labels_occ = result_date, \
            values_airvelocity = result_av, labels_airvelocity = result_date, \
            values_airpressure = result_ap, labels_airpressure = result_date, \
            values_outsideairtemperature = result_oat, labels_outsideairtemperature = result_date)
            

##@socketio.on('my_ahuchiller')
##def handle_message2():
##    #print('received message: ' + str(message))
##    db = MySQLdb.connect(host=sqlIP, user="iotadmin", passwd="@2021Pooler", db="db_hvac")
##    cursor = db.cursor()
##    while True:
##        selectStatement = "SELECT * FROM db_building"
##        cursor.execute(selectStatement)
##        results = cursor.fetchall()
##        for row in results:
##            print(row[1])
##            socketio.emit('my ahuchiller', {'sat': row[1], 'rat': row[2], 'raco2': row[3], 'chwst': row[4], 'chwrt': row[5], \
##                                                     'cwst': row[6], 'cwrt': row[7], 'chw_flow': row[8], 'cw_flow': row[9], 'chwp': row[10], \
##                                                     'cwp': row[11], 'fresht': row[12], 'ch_pwr': row[13], 'ahu_pwr': row[14], 'cooling_load': row[15], \
##                                                     'sap': row[16], 'ct_pwr': row[17]})
##
##            socketio.sleep(5)


@socketio.on('my_message')
def handle_message(message):
    #dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    currentDT = utc_now.astimezone(pytz.timezone("Asia/Singapore"))
    dt = currentDT.strftime("%Y-%m-%d %H:%M:%S")
    print('received message: ' + str(message))
    pr = (message['fr']/1.29)**2
    socketio.emit('my sensors', {'did': message['did'], 'tem': message['temp'], 'hum': message['humi'], 'co2': message['co2'], 'lux': message['lux'], 'occ': message['occ'], 'fr': message['fr'], 'pr': pr})
    
    try:
        weather = get_station1()
        w = json.loads(weather)
        otemperature = float(w['main']['temp'])
        ohumidity = float(w['main']['humidity'])
        otempmin = float(w['main']['temp_min'])
        otempmax = float(w['main']['temp_max'])
        otemp = round(otemperature - 273, 2)
        otempmin = round(otempmin - 273, 2)
        otempmax = round(otempmax - 273, 2)
        status = w['weather'][0]['main']
        desc = w['weather'][0]['description']
        opressure = float(w['main']['pressure'])
        ovisibility = float(w['visibility'])
        owindspeed = float(w['wind']['speed'])
        owinddirection= float(w['wind']['deg'])
        oclouds= float(w['clouds']['all'])
        odatetime = w['dt']

        osunrise = w['sys']['sunrise']
        orise = int(osunrise)
        osunrise_converted = datetime.datetime.fromtimestamp(orise, pytz.timezone("Asia/Singapore")).strftime('%H:%M:%S')
        
        osunset = w['sys']['sunset']
        oset = int(osunset)
        osunset_converted = datetime.datetime.fromtimestamp(oset, pytz.timezone("Asia/Singapore")).strftime('%H:%M:%S')
        
        print("Current SG weather (from openweather.org):")
        print("Temperature: ", otemp,", Humidity: ", ohumidity)
        print("Temp Min: ", otempmin,", Temp Max: ", otempmax)
        print("Status: ", status)
        print("Description: ", desc)
        print("Pressure: ", opressure)
        print("Visibility: ", ovisibility)
        print("Wind Speed: ", owindspeed)
        print("Wind Direction: ", owinddirection)
        print("Clouds: ", oclouds)
        print("Sunrise: ", osunrise_converted)
        print("Sunset: ", osunset_converted)
        socketio.emit('my weather', {'otemp': otemp, 'ohumidity': ohumidity, 'otempmin': otempmin, 'otempmax': otempmax, 
                                     'status': status, 'desc': desc, 'opressure': opressure, 'ovisibility': ovisibility, 
                                     'owindspeed':owindspeed, 'owinddirection':owinddirection, 'oclouds':oclouds})
        
        insertStatement = "INSERT INTO db_sensors VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, \
                                                                                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s, \
                                                                                      %s,%s)"

        dataval = (dt, message['did'], message['temp'], message['humi'], message['co2'], \
                       message['lux'], message['occ'], message['fr'], message['pr'], str(otemp), \
                       str(ohumidity), str(otempmin), str(otempmax), status, desc, \
                       str(opressure), str(ovisibility), str(owindspeed), str(owinddirection), str(oclouds), \
                       osunrise_converted, osunset_converted)
                                
        cursor.execute(insertStatement, dataval)

        db.commit()

        selectStatement = "SELECT * FROM db_building"
        cursor.execute(selectStatement)
        results = cursor.fetchall()
        for row in results:
            #print(row[1])
            socketio.emit('my ahuchiller', {'sat': row[1], 'rat': row[2], 'raco2': row[3], 'chwst': row[4], 'chwrt': row[5], \
                                                     'cwst': row[6], 'cwrt': row[7], 'chw_flow': row[8], 'cw_flow': row[9], 'chwp': row[10], \
                                                     'cwp': row[11], 'fresht': row[12], 'ch_pwr': row[13], 'ahu_pwr': row[14], 'cooling_load': row[15], \
                                                     'sap': row[16], 'ct_pwr': row[17]})

            socketio.sleep(3)


    #selectStatement = "SELECT dateandtime, temperature from db_sensors WHERE dateandtime=%s LIMIT 200"
    #cursor.execute(selectStatement)
    #results = cursor.fetchall()
    
    except Exception as e:
        print("ALERT: ", e)
        pass




@socketio.on("connect")
def connect():
    print("Client connected: ", request.sid)
    socketio.emit('my_event', 'Test msg from Server.')

@socketio.on("disconnect")
def disconnect():
    print("Client disconnected: ", request.sid)

if __name__ == "__main__":
    #thread = Thread(target=background_thread)
    #thread.daemon = True
    #thread.start()
  
    socketio.run(app, host="0.0.0.0", port=HTTP_PORT, debug=True, use_reloader=False)
