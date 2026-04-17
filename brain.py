import re
import sys

from openai import OpenAI
from sqlalchemy import select

from database import Incident, SessionLocal


def extract_bash_commands(text: str) -> str:
    matches = re.findall(
        r"```(?:bash|sh|shell)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE
    )

    if matches:
        return "\n".join(match.strip() for match in matches)

    if "MANUAL_INTERVENTION_REQUIRED" in text:
        return "MANUAL_INTERVENTION_REQUIRED"

    return text.strip()


db = SessionLocal()

first_log = db.scalar(select(Incident).where(Incident.status == "pending"))

if not first_log:
    print("No tasks")
    sys.exit(0)

first_log.status = "processing"
db.commit()
db.refresh(first_log)

print(f"[*] Analyzing log: {first_log.raw_log}\n")

prompt = f"""You are an Expert Linux DevOps Engineer resolving a production incident.

CRITICAL SRE RULES:
1. DIAGNOSE FIRST: 
   - If a port is in use, DO NOT just restart the service. Write commands to find the blocking PID (e.g., `ss -tulpn` or `lsof`) and kill it.
   - If the disk is full, DO NOT install new packages. Write safe cleanup commands (e.g., `apt-get clean`, `journalctl --vacuum-time=1d`).
   - If a dpkg lock is held, write a command to find the blocking process before removing the lock.
2. THINKING PROCESS: You MUST first write a brief text analysis of the root cause. Think step-by-step.
3. FINAL CODE: After your text analysis, output the executable bash commands wrapped in a SINGLE markdown block: ```bash ... ```.

System Log: 
{first_log.raw_log}"""

model = "qwen2.5:1.5b"

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

try:
    response = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], temperature=0.0
    )

    raw_response = response.choices[0].message.content
    clean_commands = extract_bash_commands(raw_response)
    first_log.ai_summary = clean_commands
    first_log.status = "resolved"
    db.commit()

    print("=== Pure commands ===")
    print(clean_commands)

except Exception as e:
    print(f"[-] AI's error: {e}")
    first_log.status = "pending"
    db.commit()
