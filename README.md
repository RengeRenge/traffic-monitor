# traffic-monitor
stat and control day traffic
If the server traffic exceeds a certain value, the traffic-monitor will shut down nginx and restart nginx after several hours
# Dependency

#### [vnstat](https://github.com/vergoh/vnstat)

Install for ubuntu
```shell
sudo apt install vnstat
```
#### nginx

```shell
sudo apt install nginx
```

# Usage
- Running
```shell
git clone https://github.com/RengeRenge/traffic-monitor.git
cd traffic-monitor
sudo python3 -u traffic_monitor.py
```

- Running in background
```shell
sudo nohup python3 -u traffic_monitor.py >/dev/null 2>&1 &
```

- Kill background traffic_monitor
```shell
sudo ps aux | grep "traffic_monitor.py" | grep -v "grep" | awk '{print $2}' | xargs sudo kill
```

- If you are unwilling to use sudo, you can create a local user and add the user to the sudo list, as restarting nginx requires sudo
```shell
sudo visudo
username ALL=(ALL:ALL) NOPASSWD:ALL
```

- Log

The statistical logs will be generated in the same level directory as the **traffic_monitor.py**, which like traffic.log.1 traffic.log.2 ... traffic.log.10