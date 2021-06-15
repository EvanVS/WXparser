import serial, codecs, threading, sys, requests, time, json
from flask import Flask, jsonify, request, Response, make_response, render_template
import numpy as np
from datetime import datetime


# ---------------{ CONFIGURATION }---------------

server_name = 'WX Telemetry Server'
com_port = "COM1"
host = "192.168.1.200"
port = 9092

# ---------------{ CONFIGURATION }---------------


# --------------{ INTITIALIZATION }--------------

data_retrieved = False
data_retrieved_boolen = "0"


json_api = {"metadata":{"updated":"","timestamp":{"utc":"","pacific":"","unix":""}},"data":{"temperature":{"fahrenheit":"","celsius":"","dewpoint":""},"humidity":"","barometer":{"inHg":"","mbar":""},"wind":{"bearing":"","heading":"","speed":"","speed_average":""},"rain":{"midnight":"","total":""}}}


data_retrieved_boolen = '0'
timestamp_utc = ''
timestamp_unix = ''
wx_temperature = ''
wx_temperature_celsius = ''
wx_dewpoint = ''
wx_humidity = ''
wx_barometer = ''
barometer_mbar = ''
wx_wind_bearing = ''
wx_wind_heading = ''
wx_wind_speed = ''
wx_average_wind_speed = ''
wx_today_rain = ''
wx_total_rain = ''



timestamp1 = "2021-05-19T16:30:00"
timestamp2 = "2021-05-19T16:00:00"

# --------------{ INTITIALIZATION }--------------


# ----------------{ WEB SERVER }-----------------

class localFlask(Flask):
	def process_response(self, response):
		#Every response will be processed here first
		response.headers['server'] = server_name
		super(localFlask, self).process_response(response)
		return(response)

app = localFlask(__name__)

@app.route('/metrics')
def flask_metrics_api():
	global data_retrieved
	now = datetime.now()
	timestamp1 = now.strftime("%Y-%m-%dT%H:%M:%S")
	t1 = datetime.strptime(timestamp1, "%Y-%m-%dT%H:%M:%S")
	t2 = datetime.strptime(timestamp2, "%Y-%m-%dT%H:%M:%S")
	difference = t1 - t2
	if difference.seconds < 60:
		return render_template('metrics.txt', wx_wind_speed=wx_wind_speed, wx_average_wind_speed=wx_average_wind_speed, wx_wind_bearing=wx_wind_bearing, wx_wind_heading=wx_wind_heading, wx_barometer=wx_barometer, wx_temperature=wx_temperature, wx_humidity=wx_humidity, wx_dewpoint=wx_dewpoint, wx_total_rain=wx_total_rain, wx_today_rain=wx_today_rain)
	else:
		return ('No Data'), 500

@app.route('/json')
def flask_json_api():
	global data_retrieved
	now = datetime.now()
	timestamp1 = now.strftime("%Y-%m-%dT%H:%M:%S")
	t1 = datetime.strptime(timestamp1, "%Y-%m-%dT%H:%M:%S")
	t2 = datetime.strptime(timestamp2, "%Y-%m-%dT%H:%M:%S")
	difference = t1 - t2
	if difference.seconds < 60:
		return json_api
	else:
		return ('No Data'), 500

if __name__ == '__main__':
	threading.Thread(target=app.run,kwargs={'host': host, 'port': port}).start()

# ----------------{ WEB SERVER }-----------------

# ------------------{ PARSER }-------------------
def update_timer():
   while True:
       threading.Thread(target=wunderground).start()
       time.sleep(15)
	   
threading.Thread(target=update_timer).start()
ser = serial.Serial(com_port,2400,timeout=1)

while True:
	packet=ser.readline()
	header = packet[0:2]
	eom = packet[50:55]
	if header == b"!!" and eom == b"\r\n":
		print("===================================")
		print("Packet:")
		print(packet)
		print("Data:")
		print(int(codecs.decode(packet[2:6], 'UTF-8'), 16)) # Wind Speed (0.1 kph)
		print(int(codecs.decode(packet[6:10], 'UTF-8'), 16)) # Wind Direction (0-255)
		print(int(codecs.decode(packet[10:14], 'UTF-8'), 16)) # Outdoor Temp (0.1 deg F)
		print(int(codecs.decode(packet[14:18], 'UTF-8'), 16)) # Rain* Long Term Total (0.01 inches)
		print(int(codecs.decode(packet[18:22], 'UTF-8'), 16)) # Barometer (0.1 mbar)
		print(int(codecs.decode(packet[22:26], 'UTF-8'), 16)) # Indoor Temp (0.1 deg F)
		print(int(codecs.decode(packet[26:30], 'UTF-8'), 16)) # Outdoor Humidity (0.1%)
		print(int(codecs.decode(packet[30:34], 'UTF-8'), 16)) # Indoor Humidity (0.1%)
		print(int(codecs.decode(packet[34:38], 'UTF-8'), 16)) # Date (day of year)
		print(int(codecs.decode(packet[38:42], 'UTF-8'), 16)) # Time (minute of day)
		print(int(codecs.decode(packet[42:46], 'UTF-8'), 16)) # Today's Rain Total (0.01 inches)*
		print(int(codecs.decode(packet[46:50], 'UTF-8'), 16)) # 1 Minute Wind Speed Average (0.1kph)*
		print("====================================")
		print(" ")
		
		# Wind Speed Calculations
		wind_speed = int(codecs.decode(packet[2:6], 'UTF-8'), 16)
		wind_speed = (wind_speed / 10)
		wind_speed = (wind_speed / 1.609344)
		wind_speed = round(wind_speed , 1)
		wx_wind_speed = wind_speed
		
		# Average Wind Speed Calculations
		average_wind_speed = int(codecs.decode(packet[46:50], 'UTF-8'), 16)
		average_wind_speed = (average_wind_speed / 10)
		average_wind_speed = (average_wind_speed / 1.609344)
		average_wind_speed = round(average_wind_speed , 1)
		wx_average_wind_speed = average_wind_speed
		
		# Wind Bearing Calculations
		x = int(codecs.decode(packet[6:10], 'UTF-8'), 16)
		y = ((int(x) / 255.0) * 360)
		wind_bearing = round(y)
		wx_wind_bearing = wind_bearing
		y = None
		
		# Wind Direction Calculations
		compass_brackets = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
		compass_lookup = round(wind_bearing / 45)
		wind_direction = compass_brackets[compass_lookup]
		wx_wind_heading = wind_direction
		
		# Barometer Calculations
		barometer = int(codecs.decode(packet[18:22], 'UTF-8'), 16)
		barometer_mbar = (barometer / 10)
		barometer_inhg = (barometer_mbar / 33.8639)
		barometer_inhg = round(barometer_inhg, 2)
		wx_barometer = barometer_inhg
		
		# Temperature Calculations
		temperature = int(codecs.decode(packet[10:14], 'UTF-8'), 16)
		temperature = (temperature / 10)
		wx_temperature = temperature
		wx_temperature_celsius = round((wx_temperature - 32) / 1.8, 2)
		
		# Humidity Calculations
		humidity = int(codecs.decode(packet[26:30], 'UTF-8'), 16)
		humidity = (humidity / 10)
		wx_humidity = humidity
		
		# Dewpoint Calculations
		T = wx_temperature_celsius
		RH = wx_humidity
		a = 17.271
		b = 237.7
		def dewpoint_approximation(T,RH):
			Td = (b * gamma(T,RH)) / (a - gamma(T,RH))
			return Td
		def gamma(T,RH):
			g = (a * T / (b + T)) + np.log(RH/100.0)
			return g
		Td = dewpoint_approximation(T,RH)
		DewPoint = 9.0/5.0 * Td + 32
		wx_dewpoint = round(DewPoint + 0.01, 2)

		# Total Rain Calculations
		total_rain = int(codecs.decode(packet[14:18], 'UTF-8'), 16)
		total_rain = (total_rain / 100)
		wx_total_rain = total_rain
		
		# Today Rain Calculations
		today_rain = int(codecs.decode(packet[42:46], 'UTF-8'), 16)
		today_rain = (today_rain / 100)
		wx_today_rain = today_rain
		
		now = datetime.now()
		now_utc = datetime.utcnow()
		timestamp2 = now.strftime("%Y-%m-%dT%H:%M:%S")
		timestamp_utc = now_utc.strftime("%Y-%m-%dT%H:%M:%S")
		timestamp_unix = str(int(time.time()))
		
		data_retrieved = True
		data_retrieved_boolen = "1"
		
		print("Wind Speed: " + str(wx_wind_speed) + " MPH")
		print("Average Wind Speed: " + str(wx_average_wind_speed)+ " MPH")
		print("Wind Bearing: " + str(wx_wind_bearing) + "°")
		print("Wind Heading: " + str(wx_wind_heading))
		print("Barometer: " + str(wx_barometer) + " inHg")
		print("Temperature: " + str(wx_temperature) + "°F")
		print("Dew Point: " + str(wx_dewpoint) + "°F")
		print("Humidity: " + str(wx_humidity) + "%")
		print("Total Rain: " + str(wx_total_rain) + " inches")
		print("Today Rain: " + str(wx_today_rain) + " inches")
	else:
		data_retrieved = False
		data_retrieved_boolen = "0"
	
	now = datetime.now()
	timestamp1 = now.strftime("%Y-%m-%dT%H:%M:%S")
	t1 = datetime.strptime(timestamp1, "%Y-%m-%dT%H:%M:%S")
	t2 = datetime.strptime(timestamp2, "%Y-%m-%dT%H:%M:%S")
	difference = t1 - t2
	if difference.seconds < 60:
		data_retrieved = True
		data_retrieved_boolen = "1"
	else:
		data_retrieved = False
		data_retrieved_boolen = "0"
	json_api["metadata"]["updated"] = str(data_retrieved_boolen)
	json_api["metadata"]["timestamp"]["utc"] = str(timestamp_utc)
	json_api["metadata"]["timestamp"]["pacific"] = str(timestamp2)
	json_api["metadata"]["timestamp"]["unix"] = str(timestamp_unix)
	json_api["data"]["temperature"]["fahrenheit"] = str(wx_temperature)
	json_api["data"]["temperature"]["celsius"] = str(wx_temperature_celsius)
	json_api["data"]["temperature"]["dewpoint"] = str(wx_dewpoint)
	json_api["data"]["humidity"] = str(wx_humidity)
	json_api["data"]["barometer"]["inHg"] = str(wx_barometer)
	json_api["data"]["barometer"]["mbar"] = str(barometer_mbar)
	json_api["data"]["wind"]["bearing"] = str(wx_wind_bearing)
	json_api["data"]["wind"]["heading"] = str(wx_wind_heading)
	json_api["data"]["wind"]["speed"] = str(wx_wind_speed)
	json_api["data"]["wind"]["speed_average"] = str(wx_average_wind_speed)
	json_api["data"]["rain"]["midnight"] = str(wx_today_rain)
	json_api["data"]["rain"]["total"] = str(wx_total_rain)
	 
	with open('api.json', 'w') as fp:
		json.dump(json_api, fp)
	fp.close()

# ------------------{ PARSER }-------------------
