# traffic-monitor

English | [简体中文](README.zh-CN.md)

A small daemon that watches daily outbound traffic and stops nginx when the threshold is exceeded, then brings it back after a cooldown.

## Features

- Polls vnstat every 60 seconds and reads today's TX counter for one interface.
- Stops nginx when daily TX exceeds `THRESHOLD`.
- Waits 12 hours, then starts nginx again.
- Performs at most one shutdown per calendar day, so a threshold hit before noon does not become a ~24-hour outage.
- Rotates its own log file (600 KB x 10).

## How it works

1. Run `vnstat -i eth0 --json` and pick today's entry.
2. If `TX > THRESHOLD`, run `nginx -s stop`.
3. Check that nginx really stopped. If not, retry on the next poll instead of sleeping.
4. Sleep 12 hours, then run `nginx` to start it again.
5. `blocked_date` stops a second shutdown on the same day after the restart.

The day boundary follows the server's local timezone.

## Requirements

- Linux (tested on Ubuntu 24.04)
- Python 3.8+
- vnstat 2.x with the monitored interface enabled (`vnstat -i eth0`)
- nginx installed and available in `PATH`
- root privileges: the nginx master runs as root and binds port 443, so starting and stopping it requires root

## Configuration

Edit the constants at the top of `traffic_monitor.py`, then restart the process:

| Setting | Default | Description |
| --- | --- | --- |
| `THRESHOLD` | `1000 * 1024 * 1024` (1000 MiB, about 1.05 GB) | Daily TX limit |
| Interface | `eth0`, hard-coded in `check_traffic_exceeded()` | Interface to monitor |
| Poll interval | 60 s | How often vnstat is queried |
| Cooldown | 12 h | How long nginx stays down |
| `max_bytes` | 600 KB | Size at which the log rotates |
| `backup_count` | 10 | Number of rotated log files kept |

## Usage

Run in the foreground:

```shell
git clone https://github.com/RengeRenge/traffic-monitor.git
cd traffic-monitor
sudo python3 -u traffic_monitor.py
```

Run in the background:

```shell
sudo nohup python3 -u traffic_monitor.py >/dev/null 2>&1 &
```

Stop it:

```shell
sudo pkill -f traffic_monitor.py
```

## Logging

`traffic.log` is written next to `traffic_monitor.py`:

```text
2026-10-22 14:28:01,123 - INFO - RX: 121634816 bytes => 116.00 MB
2026-10-22 14:28:01,124 - INFO - TX: 77053952 bytes => 73.49 MB
2026-10-22 14:28:01,125 - WARNING - traffic threshold exceeded. stopping nginx...
```

Rotated files are named `traffic.log.1` through `traffic.log.10`. On rollover the handler sets the log to `0666` so other local users can read and write it; tighten this on a shared host.

## Notes and limitations

- **TX only.** RX is logged but never evaluated. Change `check_traffic_exceeded()` if your provider bills both directions.
- **vnstat granularity.** vnstat refreshes roughly every 5 minutes, so a short burst can cross the threshold between polls.
- **Unit.** `1000 * 1024 * 1024` is 1000 MiB, not 1000 MB.
- **In-memory state.** `blocked_date` is not persisted; restarting the monitor resets it for the current day.
- **Hard-coded interface.** Container and veth interfaces need a code change.
- **No lock file.** Run exactly one instance.
- **Process detection.** `nginx_status()` uses `ps aux | grep nginx`, which can match unrelated processes.
- **Missing binary.** If `nginx` is not in `PATH`, `stop_nginx()` raises an uncaught `FileNotFoundError`.

## Restricting sudo (optional)

Do not grant `NOPASSWD:ALL`. Allow only the commands this script needs:

```sudoers
username ALL=(root) NOPASSWD: /usr/sbin/nginx -s stop, /usr/sbin/nginx
```

Check the file with `sudo visudo -c` before relying on it.

## License

MIT
