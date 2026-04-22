import hashlib
import re

import requests


def generate_log_hash(log_text: str) -> str:
    # Delete the timestamps like Apr dd hh:mm:ss
    clean_log = re.sub(r"^[A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2}\s+", "", log_text)

    # delete process' PID
    clean_log = re.sub(r"\[\d+\]:", ":", clean_log)

    return hashlib.sha256(clean_log.encode("utf-8")).hexdigest()


def send_log(text):
    url = "http://127.0.0.1:8000/api/logs"
    payload = {"raw_log": text, "log_hash": generate_log_hash(text)}

    # proxies = {
    #     "http": None,
    #     "https": None,
    # }

    try:
        print(f"Sending log to {url} ...")
        response = requests.post(url, json=payload, timeout=5)
        print("Server response:", response.json())
    except Exception as e:
        print("Send error:", e)


if __name__ == "__main__":
    dummy_log = "FATAL: Postgres OOM killer invoked. Cannot allocate memory."
    send_log(dummy_log)
