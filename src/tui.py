import os
import sys

import questionary as q
from questionary import Choice
from sqlalchemy import select

from src.ai_core import generate_solution
from src.config import load_config, save_config
from src.database import Incident, SessionLocal


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
                            Choice("2. Language", value="lang"),
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
                    elif sys_opt == "lang":
                        new_lang = q.text("Enter language (e.g. en, ru): ").ask()
                        if new_lang:
                            config["system"]["language"] = new_lang
                            save_config(config)
                            print(f"\nLanguage changed to {new_lang}.")
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

    try:
        clean_commands = generate_solution(log.raw_log, config)

        log.ai_summary = clean_commands
        log.status = "resolved"
        db.commit()

        print("=== Generated Bash Script ===")
        print(clean_commands)
        print("=============================\n")

        if clean_commands != "MANUAL_INTERVENTION_REQUIRED" and clean_commands.strip():
            script_dir = "data/scripts"
            os.makedirs(script_dir, exist_ok=True)
            script_path = os.path.join(script_dir, f"fix_incident_{log.id}.sh")

            with open(script_path, "w", encoding="utf-8") as f:
                if not clean_commands.startswith("#!"):
                    f.write("#!/bin/bash\n\n")
                f.write(clean_commands)
                f.write("\n")

            os.chmod(script_path, 0o755)

            print(f"[+] Script saved successfully: {script_path}")
            print(f"    Execute it via: ./{script_path}\n")

    except Exception as e:
        print(f"[-] AI error: {e}")
        log.status = "pending"
        db.commit()

    input("Press Enter to return to menu...")


def main_menu():
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
