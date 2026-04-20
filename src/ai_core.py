import os
import re

import httpx
from openai import OpenAI

PROMPT_TEMPLATE = """You are an Expert Linux DevOps Engineer resolving a production incident.
CRITICAL SRE RULES:
1. DIAGNOSE FIRST: 
   - If a port is in use, DO NOT just restart the service. Write commands to find the blocking PID (e.g., `ss -tulpn` or `lsof`) and kill it.
   - If the disk is full, DO NOT install new packages. Write safe cleanup commands (e.g., `apt-get clean`, `journalctl --vacuum-time=1d`).
   - If a dpkg lock is held, write a command to find the blocking process before removing the lock.
2. AVOID DUPLICATION: Do not write raw commands first and then repeat them with comments. Formulate ONE final cohesive script.
3. THINKING PROCESS: You MUST first write a brief text analysis of the root cause. Think step-by-step. DO NOT use markdown code blocks (```) during your analysis.
4. FINAL CODE: Output your entire solution wrapped in EXACTLY ONE markdown block: ```bash ... ```. Put all your explanations as bash comments (`#`) INSIDE this single block.
System Log:\n"""


def extract_bash_commands(text: str) -> str:
    matches = re.findall(
        r"```(?:bash|sh|shell)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE
    )

    if matches:
        return matches[-1].strip()

    if "MANUAL_INTERVENTION_REQUIRED" in text:
        return "MANUAL_INTERVENTION_REQUIRED"

    return text.strip()


def generate_solution(raw_log: str, config: dict, prev_error: str = "") -> str:
    provider = config["ai_provider"]
    provider_settings = config["providers"][provider]

    base_url = provider_settings["base_url"]
    model = provider_settings["model"]
    api_key = provider_settings["api_key"]

    proxy_url = (
        os.environ.get("ALL_PROXY")
        or os.environ.get("all_proxy")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
    )

    if proxy_url and proxy_url.startswith("socks://"):
        proxy_url = proxy_url.replace("socks://", "socks5://")

    if base_url and ("localhost" in base_url or "127.0.0.1" in base_url):
        proxy_url = None

    custom_http_client = httpx.Client(
        proxy=proxy_url if proxy_url else None, trust_env=False
    )

    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
        http_client=custom_http_client,
    )

    max_len = config["system"].get("max_log_length", 2000)

    trimmed_log = raw_log[-max_len:]
    prompt = f"{PROMPT_TEMPLATE}\n{trimmed_log}"

    if prev_error:
        prompt += f"\n\n[USER FEEDBACK] The previous generated script failed with the following error:\n{previous_error}\n\nAnalyze this error and provide a fully updated and corrected bash script."

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    raw_response = response.choices[0].message.content
    return extract_bash_commands(raw_response)
