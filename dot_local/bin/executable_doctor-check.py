#!/usr/bin/env python3
"""Local drive health check — run via `doctor-check.py`, outputs JSON to stdout.
Part of the [[doctor]] project. Requires the smartctl NOPASSWD sudoers rule
(run_once_after_30-doctor-sudoers.sh.tmpl) to run without a password prompt.
"""
import json
import re
import subprocess
import sys


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def list_disks():
    out = run(["lsblk", "-d", "-n", "-o", "NAME,TYPE"]).stdout
    return [line.split()[0] for line in out.splitlines() if line.split()[1] == "disk"]


def parse_smart(dev, text):
    info = {"device": dev, "raw_ok": True}

    m = re.search(r"Device Model:\s+(.+)|Model Number:\s+(.+)", text)
    info["model"] = (m.group(1) or m.group(2)).strip() if m else "unknown"

    m = re.search(r"health self-assessment test result:\s+(\w+)", text)
    info["health"] = m.group(1) if m else "UNKNOWN"

    is_nvme = "NVMe" in text or "nvme" in dev

    if is_nvme:
        for key, pattern in [
            ("power_on_hours", r"Power On Hours:\s+([\d,]+)"),
            ("unsafe_shutdowns", r"Unsafe Shutdowns:\s+([\d,]+)"),
            ("media_errors", r"Media and Data Integrity Errors:\s+([\d,]+)"),
            ("percentage_used", r"Percentage Used:\s+(\d+)%"),
            ("available_spare", r"Available Spare:\s+(\d+)%"),
            ("temperature_c", r"^Temperature:\s+(\d+) Celsius"),
        ]:
            mm = re.search(pattern, text, re.MULTILINE)
            info[key] = int(mm.group(1).replace(",", "")) if mm else None
    else:
        for key, pattern in [
            ("power_on_hours", r"^\s*9 Power_On_Hours.*?(\d+)$"),
            ("reallocated_sectors", r"^\s*5 Reallocated_Sector_Ct.*?(\d+)$"),
            ("pending_sectors", r"^\s*197 Current_Pending_Sector.*?(\d+)$"),
            ("uncorrectable", r"^\s*(?:198 Offline_Uncorrectable|187 Reported_Uncorrect).*?(\d+)$"),
            ("temperature_c", r"^\s*19[04] (?:Airflow_)?Temperature_Cel.*?\s(\d+)\s*\("),
            ("ssd_life_left_pct", r"^\s*231 SSD_Life_Left.*?\s(\d+)\s+\d+\s+\d+\s+\w"),
        ]:
            mm = re.search(pattern, text, re.MULTILINE)
            info[key] = int(mm.group(1)) if mm else None

    # anomaly flags — kept simple and conservative, meant to highlight, not diagnose
    anomalies = []
    if info["health"] != "PASSED":
        anomalies.append(f"health self-assessment is {info['health']}, not PASSED")
    if info.get("reallocated_sectors", 0):
        anomalies.append(f"{info['reallocated_sectors']} reallocated sectors")
    if info.get("pending_sectors", 0):
        anomalies.append(f"{info['pending_sectors']} pending sectors")
    if info.get("media_errors", 0):
        anomalies.append(f"{info['media_errors']} media/data integrity errors")
    if info.get("uncorrectable", 0):
        anomalies.append(f"{info['uncorrectable']} uncorrectable sectors")
    poh = info.get("power_on_hours") or 0
    us = info.get("unsafe_shutdowns")
    if us is not None and poh > 0 and us / poh > 0.02:
        anomalies.append(f"{us} unsafe shutdowns in {poh}h (~1 per {poh/us:.1f}h) — disproportionate")
    if info.get("percentage_used", 0) and info["percentage_used"] >= 80:
        anomalies.append(f"NVMe {info['percentage_used']}% of rated endurance used")
    if info.get("ssd_life_left_pct") is not None and info["ssd_life_left_pct"] <= 20:
        anomalies.append(f"only {info['ssd_life_left_pct']}% SSD life left")
    temp = info.get("temperature_c")
    if temp is not None and temp >= 55:
        anomalies.append(f"running hot at {temp}°C")
    info["anomalies"] = anomalies

    return info


def check_disk(dev):
    path = f"/dev/{dev}"
    r = run(["sudo", "-n", "smartctl", "-a", path])
    if r.returncode not in (0, 4) or "Permission denied" in r.stderr:
        # try SAT passthrough for USB-bridged drives
        r2 = run(["sudo", "-n", "smartctl", "-a", "-d", "sat", path])
        if r2.returncode in (0, 4):
            r = r2
    if "Permission denied" in r.stdout + r.stderr:
        return {"device": dev, "raw_ok": False, "error": "sudo permission denied — NOPASSWD rule missing?"}
    if not r.stdout.strip():
        return {"device": dev, "raw_ok": False, "error": r.stderr.strip() or "empty smartctl output"}
    return parse_smart(dev, r.stdout)


def main():
    result = {"hostname": subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip(),
              "disks": []}
    for dev in list_disks():
        result["disks"].append(check_disk(dev))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
