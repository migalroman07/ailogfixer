import json
import subprocess
import sys
import urllib.request


def get_system_logs():
    args = ["journalctl", "-p", "3", "--since", "5 minutes ago", "--no-pager"]
    return subprocess.run(args=args, capture_output=True, text=True)


result = get_system_logs()
log_text = result.stdout.strip()
print(result.stdout)

if log_text == "-- No entries --":
    print("No new logs.")
    sys.exit(0)

payload = {"raw_log": log_text}
json_bytes = json.dumps(payload).encode("utf-8")

log_request = urllib.request.Request(
    url="http://localhost:8000/api/logs", data=json_bytes, method="POST"
)
log_request.add_header("Content-Type", "application/json")

print(log_text)

try:
    urllib.request.urlopen(log_request)
except Exception as e:
    print(e)
