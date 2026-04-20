import requests


def send_log(text):
    url = "http://127.0.0.1:8000/docs"
    payload = {"raw_log": text}

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
