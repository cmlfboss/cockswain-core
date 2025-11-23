#!/usr/bin/env python3
import ipaddress
import subprocess
import os
from datetime import datetime

BASE_DIR = "/srv/cockswain-core"
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "node_scan.log")
ALIVE_FILE = os.path.join(LOG_DIR, "node_alive.txt")


def log(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{now}] {msg}\n")


def pick_cidr():
    out = subprocess.check_output(["ip", "-4", "addr"], text=True)
    best = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("inet ") and "127.0.0.1" not in line:
            cidr = line.split()[1]
            ip = cidr.split("/")[0]
            # 跳過 169.254.x.x
            if ip.startswith("169.254."):
                continue
            # 優先用 192.168.x.x
            if ip.startswith("192.168."):
                return cidr
            best = cidr
    return best or "192.168.0.1/24"


def ping_host(ip):
    res = subprocess.call(
        ["ping", "-c", "1", "-W", "1", str(ip)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return res == 0


def main():
    cidr = pick_cidr()
    log(f"scan start cidr={cidr}")
    net = ipaddress.ip_network(cidr, strict=False)

    alive = []
    for i, host in enumerate(net.hosts()):
        if i >= 32:   # 只掃前 32 個，測試用
            break
        if ping_host(host):
            alive.append(str(host))

    # 寫結果
    log(f"scan done alive={len(alive)}")
    with open(ALIVE_FILE, "w") as f:
        for h in alive:
            f.write(h + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR {e}")
