# traffic-monitor

[English](README.md) | 简体中文

一个轻量守护脚本：监控当天的出网流量，超过阈值时停止 nginx，冷却一段时间后自动恢复。

## 功能

- 每 60 秒调用一次 vnstat，读取指定网卡当天的 TX 计数
- 当天 TX 超过 `THRESHOLD` 时执行 `nginx -s stop`
- 等待 12 小时后自动启动 nginx
- 每个自然日最多执行一次停机，避免中午前触发变成近 24 小时中断
- 日志自动轮转（600 KB × 10）

## 工作原理

1. 执行 `vnstat -i eth0 --json`，取当天那条记录
2. 若 `TX > THRESHOLD`，执行 `nginx -s stop`
3. 校验 nginx 是否真的停止；如果没停，下一轮继续重试，不进入长时间休眠
4. 休眠 12 小时后执行 `nginx` 恢复
5. 恢复后由 `blocked_date` 保证当天不会再次停机

“当天”以服务器本地时区的 0 点为界。

## 依赖

- Linux（在 Ubuntu 24.04 上验证）
- Python 3.8+
- vnstat 2.x，且已启用被监控的网卡（`vnstat -i eth0`）
- nginx 已安装并在 `PATH` 中
- root 权限：nginx master 以 root 运行并监听 443，启停都需要 root

## 配置

修改 `traffic_monitor.py` 顶部的常量后重启进程：

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `THRESHOLD` | `1000 * 1024 * 1024`（1000 MiB，约 1.05 GB） | 每日 TX 上限 |
| 网卡 | `eth0`，写死在 `check_traffic_exceeded()` | 被监控的网卡 |
| 轮询间隔 | 60 秒 | vnstat 查询频率 |
| 冷却时间 | 12 小时 | nginx 停机时长 |
| `max_bytes` | 600 KB | 日志轮转阈值 |
| `backup_count` | 10 | 保留的轮转日志数量 |

## 使用

前台运行：

```shell
git clone https://github.com/RengeRenge/traffic-monitor.git
cd traffic-monitor
sudo python3 -u traffic_monitor.py
```

后台运行：

```shell
sudo nohup python3 -u traffic_monitor.py >/dev/null 2>&1 &
```

停止：

```shell
sudo pkill -f traffic_monitor.py
```

## 日志

日志写在 `traffic_monitor.py` 同目录的 `traffic.log`：

```text
2026-10-22 14:28:01,123 - INFO - RX: 121634816 bytes => 116.00 MB
2026-10-22 14:28:01,124 - INFO - TX: 77053952 bytes => 73.49 MB
2026-10-22 14:28:01,125 - WARNING - traffic threshold exceeded. stopping nginx...
```

轮转文件为 `traffic.log.1` 到 `traffic.log.10`。轮转时会把日志权限设为 `0666`，便于其他本地用户读写；多人共用的机器上建议收紧。

## 已知限制

- **只统计 TX。** RX 仅记录、不参与判断；如果运营商按上下行计费，需要修改 `check_traffic_exceeded()`。
- **vnstat 精度。** vnstat 大约每 5 分钟更新一次，两次轮询之间的突发流量可能晚发现。
- **单位。** `1000 * 1024 * 1024` 是 1000 MiB，不是 1000 MB。
- **状态不持久化。** `blocked_date` 只存在内存里，重启监控进程会让当天状态重置。
- **网卡写死。** 容器或 veth 环境需要改代码。
- **没有锁文件。** 只能运行一个实例。
- **进程检测较粗。** `nginx_status()` 使用 `ps aux | grep nginx`，可能匹配到无关进程。
- **命令缺失。** `nginx` 不在 `PATH` 时，`stop_nginx()` 会抛出未被捕获的 `FileNotFoundError`。

## 收窄 sudo 权限（可选）

不要使用 `NOPASSWD:ALL`，只授权脚本真正需要的命令：

```sudoers
username ALL=(root) NOPASSWD: /usr/sbin/nginx -s stop, /usr/sbin/nginx
```

修改后用 `sudo visudo -c` 校验。

## 许可证

MIT
