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

```shell
git clone https://github.com/RengeRenge/traffic-monitor.git
cd traffic-monitor
python3 -u traffic_monitor.py
```

- Running in background
```shell
ps aux | grep "traffic_monitor.py" | grep -v "grep" | awk '{print $2}' | xargs kill
python3 -u traffic_monitor.py &
```

- Log

The statistical logs will be generated in the same level directory as the **traffic_monitor.py**, which like traffic.log.1 traffic.log.2 ... traffic.log.10