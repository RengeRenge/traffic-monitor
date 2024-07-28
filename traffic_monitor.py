import json
import subprocess
import time
from datetime import datetime, timedelta
import logging
import os
from logging.handlers import RotatingFileHandler

current_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(current_dir, 'traffic.log')

# log file size
max_bytes = 1024 * 600  # 600KB per file

# log file count.
# example: traffic.log.1 traffic.log.2 ... traffic.log.10
backup_count = 10

handler = RotatingFileHandler(log_file_path, maxBytes=max_bytes, backupCount=backup_count)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger = logging.getLogger('TrafficLog')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

THRESHOLD = 1000 * 1024 * 1024  # 1000MB

def check_traffic_exceeded():
    traffic_sent = get_vnstat_traffic_today('eth0')
    return traffic_sent > THRESHOLD

def get_vnstat_traffic_today(interface):
    try:
        command = [
            'vnstat', 
            '-i', 
            interface, 
            '--json'
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        vnstat_data = json.loads(result.stdout)
        interfaces = vnstat_data["interfaces"]
        interface_data = next((i for i in interfaces if i["name"] == interface), None)
        
        if interface_data:
            day_data = interface_data["traffic"]["day"]
            
            today_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_timestamp = int(today_date.timestamp())
            today_flow_data = next((day for day in day_data if day["timestamp"] == today_timestamp), None)
            if today_flow_data:
                tx = today_flow_data['tx']
                rx = today_flow_data['rx']
                logger.info(f"RX: {rx} bytes => {rx / (1024 ** 2):.2f} MB")
                logger.info(f"TX: {tx} bytes => {tx / (1024 ** 2):.2f} MB")
                return tx
            return 0
    except Exception as e:
        logger.error(f"error fetching vnstat data: {e}")
        return 0

def stop_nginx():
    try:
        nginx_check = subprocess.run("ps aux | grep -v grep | grep -c nginx", shell=True, capture_output=True, text=True)
        if int(nginx_check.stdout.strip()) > 0:
            subprocess.run(["nginx", "-s", "stop"], check=True)
            logger.info("nginx has been stopped")
        else:
            logger.info("nginx was not running")
    except subprocess.CalledProcessError as e:
        logger.error(f"failed to stop nginx: {e}")

def start_nginx():
    try:
        subprocess.run(["nginx"], check=True)
        logger.info("nginx has been started")
    except subprocess.CalledProcessError as e:
        logger.error(f"failed to start nginx: {e}")

def main():
    logger.info("starting traffic monitoring...")
    while True:
        if check_traffic_exceeded():
            logger.warning("traffic threshold exceeded. stopping nginx...")
            stop_nginx()
            
            twelve_hours_later = datetime.now() + timedelta(hours=12, seconds=1)
            logger.info(f"nginx will be restarted at {twelve_hours_later.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep((twelve_hours_later - datetime.now()).total_seconds())

            start_nginx()

        time.sleep(60)

if __name__ == "__main__":
    main()
