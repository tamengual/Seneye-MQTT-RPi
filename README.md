# Seneye → MQTT (Raspberry Pi)

Small Python daemon that reads a **Seneye SUD (24f7:2204)** over HID and publishes readings to MQTT for Home Assistant.

- **Library:** `pyseneye` (HID mode via `/dev/hidraw*`)
- **Topics:** single JSON state topic (default `seneye/state`)
- **Fields:** `temperature_c`, `ph`, `nh3_mg_l`, plus `lux`, `par` when available

> ✅ This repo reflects a working configuration that’s been verified on a Pi with kernel 6.12+rpt, `hid-generic` bound, and `hidraw` nodes present.

---

## 1) Prereqs on the Pi

```bash
sudo apt update
sudo apt install -y python3-venv python3-full                     mosquitto-clients udev
```

Ensure the device enumerates and creates a `hidraw` node:

```bash
lsusb | grep -i 24f7
# expect: 24f7:2204 Seneye SUD

ls -l /dev/hidraw*   # expect something like /dev/hidraw0
```

If `/dev/hidraw*` is missing but `lsusb` shows `24f7:2204`, rebind the USB port once:

```bash
echo '1-1.4' | sudo tee /sys/bus/usb/drivers/usb/unbind
sleep 2
echo '1-1.4' | sudo tee /sys/bus/usb/drivers/usb/bind
```

(Replace `1-1.4` with your actual bus path if different.)

---

## 2) Udev permissions (so the service can read hidraw)

```bash
sudo install -D -m 0644 udev/99-seneye-hidraw.rules   /etc/udev/rules.d/99-seneye-hidraw.rules

sudo udevadm control --reload
sudo udevadm trigger --attr-match=idVendor=24f7 --attr-match=idProduct=2204
```

You should now see readable `hidraw`:

```bash
ls -l /dev/hidraw*
# e.g. crw-rw-rw- 1 root root 242, 0 ... /dev/hidraw0
```

---

## 3) App install (venv)

```bash
# from repo root
python3 -m venv ~/seneye-venv
~/seneye-venv/bin/pip install -U pip
~/seneye-venv/bin/pip install -r requirements.txt
```

---

## 4) Configure systemd service

Edit **systemd/seneye-mqtt.service** (or set env in the unit below) for your broker:

- `MQTT_HOST` (e.g. `192.168.7.253`)
- `MQTT_USERNAME` (e.g. `mqtt-user`)
- `MQTT_PASSWORD` (your password)
- optional: `MQTT_TOPIC` (default `seneye/state`), `MQTT_PORT` (default `1883`)

Install & enable:

```bash
# Adjust `User` and paths if your username differs
sudo install -D -m 0644 systemd/seneye-mqtt.service   /etc/systemd/system/seneye-mqtt.service

sudo systemctl daemon-reload
sudo systemctl enable --now seneye-mqtt.service
journalctl -u seneye-mqtt.service -f
```

You should see logs like:

```
INFO: Entering interactive mode…
INFO: Published: {'ts': '...', 'temperature_c': 27.5, 'ph': 8.17, 'nh3_mg_l': 0.007}
```

---

## 5) Home Assistant (simple sensors)

Add to your `configuration.yaml` (or equivalent package):

```yaml
mqtt:
  sensor:
    - name: "Seneye Temperature (°C)"
      state_topic: "seneye/state"
      value_template: "{{ value_json.temperature_c }}"
      unit_of_measurement: "°C"
      device_class: temperature
      state_class: measurement
      unique_id: seneye_temp_c

    - name: "Seneye pH"
      state_topic: "seneye/state"
      value_template: "{{ value_json.ph }}"
      unit_of_measurement: "pH"
      state_class: measurement
      unique_id: seneye_ph

    - name: "Seneye NH3 (mg/L)"
      state_topic: "seneye/state"
      value_template: "{{ value_json.nh3_mg_l }}"
      unit_of_measurement: "mg/L"
      state_class: measurement
      unique_id: seneye_nh3_mg_l
```

---

## 6) Troubleshooting

- **No `/dev/hidraw*`** but `lsusb` shows the device:
  - Check `ls -1 /sys/bus/hid/devices | grep -i 24f7` exists and is bound to `hid-generic`.
  - Rebind USB (see step 1) or reboot once.
- **Permissions**: ensure the udev rule is installed and re-triggered, then replug or rebind.
- **MQTT**: test creds/topic quickly:
  ```bash
  mosquitto_pub -h $MQTT_HOST -u $MQTT_USERNAME -P '…'     -t 'seneye/state' -m '{"temperature_c":25.0,"ph":8.10,"nh3_mg_l":0.001}'
  ```

---

## 7) Uninstall / disable

```bash
sudo systemctl disable --now seneye-mqtt.service
sudo rm -f /etc/systemd/system/seneye-mqtt.service
sudo rm -f /etc/udev/rules.d/99-seneye-hidraw.rules
```
