#!/usr/bin/env bash
apt-get update
echo '!!!!-----DONE WITH UPDATE----!!!!'
apt -y install python3-pip
echo '!!!!-----DONE WITH python3-pip----!!!!'
apt -y install python3-opencv
python3 -c "import cv2; print(cv2.__version__)"
pip3 install -r /vagrant/requirements.txt
apt-get -y install zbar-tools
echo '!!!!-----DONE WITH requirements----!!!!'
chmod 755 /vagrant/app.py
nohup python3 /vagrant/app.py > /dev/null 2>&1 &
