import time
import ujson
import network
from machine import Pin, I2C
from umqtt.simple import MQTTClient
from microdot import Microdot, send_file
from microdot.websocket import with_websocket

from MPU6050 import MPU6050
from UPSB import INA219

# Fill these in to allow connection to local network
ssid = ""
password = ""

def connect():
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        time.sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip

# Connect to network
try:
    ip = connect()
except KeyboardInterrupt:
    machine.reset()
    
# Set up communication to Gyro/Accell
i2c = I2C(0, sda=Pin(20), scl=Pin(21), freq=400000)
mpu = MPU6050(i2c)
mpu.wake()

mpu.write_gyro_range(1)
mpu.write_accel_range(1)

print(mpu.get_accel_fs_range())
print(mpu.get_gyro_fs_range())

# Set up communication to UPS
ina219 = INA219(addr=0x43)

# Set up network app
app = Microdot()

@app.route('/')
async def index(request):
    return send_file('index.html')

@app.route('/gyro_data')
@with_websocket
async def gyro_socket(request, ws):
    while True:
        gx, gy, gz = mpu.read_gyro_data()
        ax, ay, az = mpu.read_accel_data()
        bus_voltage = ina219.getBusVoltage_V()
        current = ina219.getCurrent_mA()
        P = (bus_voltage -3)/1.2*100
        allData = {'gyro': {'x': gx, 'y': gy, 'z': gz},
                   'gyro_range': mpu.get_gyro_fs_range(),
                   'accel': {'x': ax, 'y': ay, 'z': az},
                   'accel_range': mpu.get_accel_fs_range(),
                   'bus_voltage': bus_voltage,
                   'current': current,
                   'p': P}
        await ws.send(ujson.dumps(allData))
        time.sleep(0.1)

app.run(debug=True);