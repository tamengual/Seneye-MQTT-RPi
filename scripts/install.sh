#!/usr/bin/env bash
set -euo pipefail
sudo install -D -m 0644 udev/99-seneye-hidraw.rules /etc/udev/rules.d/99-seneye-hidraw.rules
sudo udevadm control --reload
sudo udevadm trigger --attr-match=idVendor=24f7 --attr-match=idProduct=2204 || true
python3 -m venv ~/seneye-venv
~/seneye-venv/bin/pip install -U pip
~/seneye-venv/bin/pip install -r requirements.txt
sudo install -D -m 0644 systemd/seneye-mqtt.service /etc/systemd/system/seneye-mqtt.service
sudo systemctl daemon-reload
sudo systemctl enable --now seneye-mqtt.service
echo "Done. Check logs with: journalctl -u seneye-mqtt.service -f"
