import json
import os
import re
import sys

import httpx
import questionary as q
from openai import OpenAI
from questionary import Choice
from sqlalchemy import select

from database import Incident, SessionLocal


def load_config():
    with open("config.json") as f:
        return json.load(f)


def save_config(updated_config):
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(updated_config, f, indent=4, ensure_ascii=False)


def extract_bash_commands(text: str) -> str:
    matches = re.findall(
        r"```(?:bash|sh|shell)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE
    )

    if matches:
        return matches[-1].strip()

    if "MANUAL_INTERVENTION_REQUIRED" in text:
        return "MANUAL_INTERVENTION_REQUIRED"

    return text.strip()


def configure_menu(config):
    while True:
        os.system("clear" if os.name == "posix" else "cls")

        aspect = q.select(
            "=========== What you'd like to change? ==========",
            choices=[
                Choice("1. Mode", value="mode"),
                Choice("2. AI Provider/Model", value="provider"),
                Choice("3. System setup", value="system"),
                Choice("<- Back", value="back"),
            ],
        ).ask()

        if not aspect or aspect == "back":
            return

        match aspect:
            case "mode":
                while True:
                    os.system("clear" if os.name == "posix" else "cls")
                    new_mode = q.select(
                        "========== Select mode ==========",
                        choices=[
                            Choice("1. Manual call", value="manual"),
                            Choice("2. Auto call (choose interval)", value="auto"),
                            Choice("<- Back", value="back"),
                        ],
                    ).ask()

                    if not new_mode or new_mode == "back":
                        break

                    if new_mode == "manual":
                        config["system"]["interval"] = 0
                        save_config(config)
                        print("\nMode changed to Manual.")
                        input("Press Enter to continue...")
                        break
                    elif new_mode == "auto":
                        while True:
                            new_interval = q.text(
                                "Enter an interval in minutes (0 for constant checks): "
                            ).ask()

                            if not new_interval:
                                break

                            if new_interval.isdigit():
                                config["system"]["interval"] = int(new_interval)
                                save_config(config)
                                print(f"\nInterval changed to {new_interval} minutes.")
                                input("Press Enter to continue...")
                                break
                        break

            case "provider":
                while True:
                    os.system("clear" if os.name == "posix" else "cls")
                    providers = list(map(Choice, config["providers"].keys())) + [
                        Choice("New provider (Manual enter)", value="new"),
                        Choice("<- Back", value="back"),
                    ]
                    new_provider = q.select(
                        "========== Select provider ==========", choices=providers
                    ).ask()

                    if not new_provider or new_provider == "back":
                        break

                    if new_provider == "new":
                        provider = q.text("Enter provider name: ").ask()
                        if not provider:
                            continue

                        base_url = q.text("Enter base URL: ").ask()
                        if not base_url:
                            continue

                        api_key = q.text("Enter API key: ").ask()
                        if not api_key:
                            continue

                        config["providers"][provider] = {
                            "base_url": base_url,
                            "api_key": api_key,
                            "model": "",
                            "available_models": [],
                        }
                    else:
                        provider = new_provider

                    config["ai_provider"] = provider

                    os.system("clear" if os.name == "posix" else "cls")
                    models = list(
                        map(
                            Choice,
                            config["providers"][provider].get("available_models", []),
                        )
                    ) + [
                        Choice("New model (Manual enter)", value="new"),
                        Choice("<- Back", value="back"),
                    ]

                    new_model = q.select(
                        f"========== Select model for {provider} ==========",
                        choices=models,
                    ).ask()

                    if not new_model or new_model == "back":
                        continue

                    if new_model == "new":
                        model = q.text("Enter exact model name: ").ask()
                        if not model:
                            continue

                        if (
                            model
                            not in config["providers"][provider]["available_models"]
                        ):
                            config["providers"][provider]["available_models"].append(
                                model
                            )
                    else:
                        model = new_model

                    config["providers"][provider]["model"] = model
                    save_config(config)
                    print(f"\nConfiguration saved: {provider} -> {model}")
                    input("Press Enter to continue...")
                    break

            case "system":
                while True:
                    os.system("clear" if os.name == "posix" else "cls")
                    sys_opt = q.select(
                        "========== System Setup ==========",
                        choices=[
                            Choice("1. Max log length", value="max_log"),
                            Choice("<- Back", value="back"),
                        ],
                    ).ask()

                    if not sys_opt or sys_opt == "back":
                        break

                    if sys_opt == "max_log":
                        new_len = q.text("Enter max log length: ").ask()
                        if new_len and new_len.isdigit():
                            config["system"]["max_log_length"] = int(new_len)
                            save_config(config)
                            print(f"\nMax log length changed to {new_len}.")
                            input("Press Enter to continue...")


def run_fixer(config):
    os.system("clear" if os.name == "posix" else "cls")
    db = SessionLocal()

    pending_logs = db.scalars(
        select(Incident).where(Incident.status == "pending")
    ).all()

    if not pending_logs:
        print("\nNo pending incidents to fix.")
        input("Press Enter to return...")
        return

    ui_choices = [
        Choice(
            title=f"ID {log.id} | {log.raw_log[:70].replace('\n', ' ')}...", value=log
        )
        for log in pending_logs
    ]
    ui_choices.append(Choice("<- Back", value="back"))

    log = q.select(
        "========== Select an incident to fix ==========", choices=ui_choices
    ).ask()

    if not log or log == "back":
        return

    log.status = "processing"
    db.commit()
    db.refresh(log)

    os.system("clear" if os.name == "posix" else "cls")
    print(f"\n[*] Analyzing log ID {log.id}...\n")

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

    prompt = f"{PROMPT_TEMPLATE}\n{log.raw_log}"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )

        raw_response = response.choices[0].message.content
        clean_commands = extract_bash_commands(raw_response)

        log.ai_summary = clean_commands
        log.status = "resolved"
        db.commit()

        print("=== Generated Bash Script ===")
        print(clean_commands)
        print("=============================\n")

        # Saving script logic
        if clean_commands != "MANUAL_INTERVENTION_REQUIRED" and clean_commands.strip():
            os.makedirs("scripts", exist_ok=True)
            script_path = f"scripts/fix_incident_{log.id}.sh"

            with open(script_path, "w", encoding="utf-8") as f:
                if not clean_commands.startswith("#!"):
                    f.write("#!/bin/bash\n\n")
                f.write(clean_commands)
                f.write("\n")

            os.chmod(script_path, 0o755)  # Makes the file executable

            print(f"[+] Script saved successfully: {script_path}")
            if not q.confirm("Execute it now?").ask():
                print(f"You can execute it youself with:   ./{script_path}\n")
                input("Press Enter to continue...")
                return
            else:
                os.system(f"./{script_path}")
                input("Press Enter to continue...")
                return

    except Exception as e:
        print(f"[-] AI error: {e}")
        log.status = "pending"
        db.commit()

    input("Press Enter to return to menu...")


PROMPT_TEMPLATE = """You are an Expert Linux DevOps Engineer resolving a production incident.
CRITICAL SRE RULES:
1. DIAGNOSE FIRST: 
   - If a port is in use, DO NOT just restart the service. Write commands to find the blocking PID (e.g., `ss -tulpn` or `lsof`) and kill it.
   - If the disk is full, DO NOT install new packages. Write safe cleanup commands (e.g., `apt-get clean`, `journalctl --vacuum-time=1d`).
   - If a dpkg lock is held, write a command to find the blocking process before removing the lock.
2. THINKING PROCESS: You MUST first write a brief text analysis of the root cause. Think step-by-step.
3. FINAL CODE: After your text analysis, output the executable bash commands wrapped in a SINGLE markdown block: ```bash ... ```.
System Log:\n"""


def main():
    while True:
        os.system("clear" if os.name == "posix" else "cls")

        config = load_config()

        provider = config["ai_provider"]
        model = config["providers"][provider].get("model", "Unknown")

        option = q.select(
            f"=========== AI system fixer | Current model: {model} ==========\n",
            choices=[
                Choice(title="1. Fix issues", value="fix"),
                Choice(title="2. Configure", value="configure"),
                Choice(title="3. Exit", value="exit"),
            ],
        ).ask()

        match option:
            case "fix":
                run_fixer(config)
            case "configure":
                configure_menu(config)
            case _:
                os.system("clear" if os.name == "posix" else "cls")
                print("Bye")
                sys.exit(0)


if __name__ == "__main__":
    main()
