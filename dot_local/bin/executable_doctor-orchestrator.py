#!/usr/bin/env python3
"""[[doctor]] orchestrator — runs on pramen only (the fleet's one always-on
machine), triggered hourly. Reachability is checked every run; the actual
(heavier, sudo-gated) smartctl health check per host only runs when that
host is both reachable AND actually due (hasn't had a successful check in
CHECK_INTERVAL_DAYS) — decoupling "how often do we notice a device came
back online" from "how often do we actually want fresh drive data."
Per-host state persists in STATE_DIR so results survive across runs even
while other hosts stay unreachable for a long stretch.
"""
import datetime
import json
import pathlib
import subprocess

FLEET = ["ocean", "akvarium", "kapka"]  # pramen itself checked locally
CHECK_INTERVAL_DAYS = 7
STATE_DIR = pathlib.Path("/home/jakub/doctor/state")
REPORT_DIR = pathlib.Path("/home/jakub/doctor/reports")
HISTORY_FILE = pathlib.Path("/home/jakub/doctor/history.jsonl")


def load_state(host):
    f = STATE_DIR / f"{host}.json"
    if f.exists():
        return json.loads(f.read_text())
    return None


def save_state(host, data):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / f"{host}.json").write_text(json.dumps(data, indent=2))


def is_due(state):
    if state is None:
        return True
    last = datetime.datetime.fromisoformat(state["checked_at"])
    age = datetime.datetime.now(datetime.timezone.utc) - last
    return age >= datetime.timedelta(days=CHECK_INTERVAL_DAYS)


def ping_reachable(host):
    if host == "pramen":
        return True
    r = subprocess.run(["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", host, "true"],
                        capture_output=True, timeout=10)
    return r.returncode == 0


def run_check(host):
    if host == "pramen":
        r = subprocess.run(["/home/jakub/.local/bin/doctor-check.py"], capture_output=True, text=True, timeout=30)
    else:
        r = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", host, "~/.local/bin/doctor-check.py"],
            capture_output=True, text=True, timeout=30,
        )
    if r.returncode != 0 or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def process_host(host):
    state = load_state(host)
    reachable = ping_reachable(host)
    due = is_due(state)

    if reachable and due:
        fresh = run_check(host)
        if fresh is not None:
            fresh["checked_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            save_state(host, fresh)
            with open(HISTORY_FILE, "a") as hf:
                hf.write(json.dumps({"host": host, "checked_at": fresh["checked_at"],
                                      "disks": fresh.get("disks", [])}) + "\n")
            return fresh, reachable
    return state, reachable


def render_report(results):
    now = datetime.datetime.now(datetime.timezone.utc)
    lines = [f"# Doctor drive health report — generated {now.isoformat()}",
             f"*Per-host checks are refreshed at most every {CHECK_INTERVAL_DAYS} days when reachable — this is not a single point-in-time snapshot.*",
             ""]

    all_anomalies = []
    for host, (state, reachable) in results.items():
        if state is None:
            all_anomalies.append(f"**{host}**: never successfully checked yet"
                                  + ("" if reachable else " (currently unreachable)"))
            continue
        age = now - datetime.datetime.fromisoformat(state["checked_at"])
        staleness = f"{age.days}d old"
        if age.days > CHECK_INTERVAL_DAYS * 2:
            all_anomalies.append(f"**{host}**: data is {staleness} — hasn't been reachable for a check in a while")
        for disk in state.get("disks", []):
            if not disk.get("raw_ok", True):
                all_anomalies.append(f"**{host}**/{disk['device']}: check failed — {disk.get('error', 'unknown')}")
            for a in disk.get("anomalies", []):
                all_anomalies.append(f"**{host}**/{disk['device']} ({disk.get('model', '?')}): {a}")

    lines.append("## Anomalies" if all_anomalies else "## Anomalies — none, all clear")
    for a in all_anomalies:
        lines.append(f"- {a}")
    lines.append("")

    lines.append("## Full results")
    for host, (state, reachable) in results.items():
        lines.append(f"### {host} — {'reachable now' if reachable else 'unreachable now'}")
        if state is None:
            lines.append("No successful check yet.\n")
            continue
        age = now - datetime.datetime.fromisoformat(state["checked_at"])
        lines.append(f"*Last checked: {state['checked_at']} ({age.days}d ago)*\n")
        if not state.get("disks"):
            lines.append("No disks reported.\n")
            continue
        lines.append("| Device | Model | Health | Power-on hrs | Notes |")
        lines.append("|---|---|---|---|---|")
        for d in state["disks"]:
            if not d.get("raw_ok", True):
                lines.append(f"| {d['device']} | - | CHECK FAILED | - | {d.get('error', '')} |")
                continue
            notes = "; ".join(d.get("anomalies", [])) or "clean"
            lines.append(f"| {d['device']} | {d.get('model', '?')} | {d.get('health', '?')} | {d.get('power_on_hours', '?')} | {notes} |")
        lines.append("")

    return "\n".join(lines)


def main():
    results = {}
    for host in ["pramen"] + FLEET:
        results[host] = process_host(host)

    report = render_report(results)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "latest.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
