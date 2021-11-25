pip3 install -r requirements.txt
cp ./raspberry-socket.service /etc/systemd/system/
sudo systemctl enable raspberry-socket.service
