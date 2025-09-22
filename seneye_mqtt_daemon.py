#!/usr/bin/env python3
# full daemon code as provided above

import json, os, socket, sys, time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from pyseneye import sud

MQTT_HOST=os.getenv("MQTT_HOST","192.168.7.253")
MQTT_PORT=int(os.getenv("MQTT_PORT","1883"))
MQTT_USERNAME=os.getenv("MQTT_USERNAME","mqtt-user")
MQTT_PASSWORD=os.getenv("MQTT_PASSWORD","changeme")
MQTT_TOPIC=os.getenv("MQTT_TOPIC","seneye/state")
MQTT_QOS=int(os.getenv("MQTT_QOS","1"))
CLIENT_ID=os.getenv("MQTT_CLIENT_ID",f"seneye-pi-{socket.gethostname()}")
POLL_SECONDS=int(os.getenv("POLL_SECONDS","10"))

def log(level,msg): print(f"{datetime.now().isoformat()} {level}: {msg}",flush=True)

def to_float(x):
    try: return float(x)
    except: return None

def connect_mqtt():
    c=mqtt.Client(client_id=CLIENT_ID)
    if MQTT_USERNAME: c.username_pw_set(MQTT_USERNAME,MQTT_PASSWORD or "")
    c.connect(MQTT_HOST,MQTT_PORT,60)
    return c

def open_device():
    try: return sud.SUDevice()
    except Exception as e:
        log("WARN",f"No Seneye: {e}")
        return None

def enter_interactive(d):
    try: d.action(sud.Action.ENTER_INTERACTIVE_MODE)
    except: pass

def read_once(d):
    r=d.action(sud.Action.SENSOR_READING)
    return {
      "ts": datetime.now(timezone.utc).isoformat(),
      "temperature_c": to_float(getattr(r,"temperature",None)),
      "ph": to_float(getattr(r,"ph",None)),
      "nh3_mg_l": to_float(getattr(r,"nh3",None)),
      "lux": to_float(getattr(r,"lux",None)),
      "par": to_float(getattr(r,"par",None)),
    }

def main():
    c=None
    while not c:
        try: c=connect_mqtt()
        except Exception as e: log("WARN",f"MQTT fail {e}"); time.sleep(5)
    d=None
    while not d:
        d=open_device(); 
        if not d: time.sleep(5)
    enter_interactive(d)
    while True:
        try:
            p=read_once(d)
            c.publish(MQTT_TOPIC,json.dumps(p),qos=MQTT_QOS)
            log("INFO",f"Published: {p}")
        except Exception as e:
            log("WARN",f"Loop fail {e}")
            try: d.close()
            except: pass
            d=None
            while not d:
                d=open_device(); 
                if not d: time.sleep(5)
            enter_interactive(d)
        time.sleep(POLL_SECONDS)

if __name__=="__main__": main()
