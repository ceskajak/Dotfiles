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
    skip_prefixes = ("zram", "loop", "sr")
    return [
        parts[0] for line in out.splitlines()
        if (parts := line.split()) and len(parts) >= 2 and parts[1] == "disk"
        and not parts[0].startswith(skip_prefixes)
    ]


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
        def sata_attr_raw_int(attr_name_pattern):
            """Find a SMART attribute line by name, extract the leading integer
            from its RAW_VALUE (last column) — robust to non-plain-integer raw
            formats like '5849h+00m+00.000s' or '48 (Min/Max 32/37)'."""
            m = re.search(rf"^\s*\d+\s+{attr_name_pattern}\s.*$", text, re.MULTILINE)
            if not m:
                return None
            tokens = m.group(0).split()
            # temperature-style lines have trailing "(0 32 0 0 0)" detail —
            # the real current value is the token right before the first "("
            paren_idx = next((i for i, t in enumerate(tokens) if t.startswith("(")), None)
            raw = tokens[paren_idx - 1] if paren_idx else tokens[-1]
            mm = re.match(r"^(\d+)", raw)
            return int(mm.group(1)) if mm else None

        def sata_attr_normalized_value(attr_name_pattern):
            """For wear-style attributes, the vendor RAW_VALUE encoding varies
            and isn't a simple percentage — the normalized VALUE column (3rd
            field after id/name/flag) is the standardized 0-100 'health left'
            score and is what's actually meaningful here."""
            m = re.search(rf"^\s*\d+\s+{attr_name_pattern}\s+\S+\s+(\d+)", text, re.MULTILINE)
            return int(m.group(1)) if m else None

        info["power_on_hours"] = sata_attr_raw_int("Power_On_Hours")
        info["reallocated_sectors"] = sata_attr_raw_int("Reallocated_Sector_Ct")
        info["pending_sectors"] = sata_attr_raw_int("Current_Pending_Sector")
        info["uncorrectable"] = sata_attr_raw_int("Offline_Uncorrectable") or sata_attr_raw_int("Reported_Uncorrect")
        info["temperature_c"] = sata_attr_raw_int("Temperature_Celsius") or sata_attr_raw_int("Airflow_Temperature_Cel")
        info["ssd_life_left_pct"] = sata_attr_normalized_value("SSD_Life_Left")

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
    if "Unable to detect device type" in r.stdout:
        # SD/eMMC cards etc — most don't expose SMART at all, this isn't an
        # anomaly, just a device class smartctl can't talk to.
        return {"device": dev, "raw_ok": True, "health": "NOT_SUPPORTED",
                "model": "unknown", "anomalies": []}
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
