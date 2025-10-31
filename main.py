#!/usr/bin/env python3
import jenkins
import time
import sys
from colorama import init, Fore, Style
import os

# ======== CONFIGURE THESE ========
JENKINS_URL = os.environ["JENKINS_URL"]
USERNAME = os.environ["JENKINS_USERNAME"]
API_TOKEN = os.environ["JENKINS_API_TOKEN"]

TARGET_JOBS = [
    "🌐 Integration",
    "🌐 P360",
    "🌐 Processor",
    "💻 Member Web App",
    "💻 Staff Web App",
    "MH Member Web App",
    "MH Staff Web App",
]
# =================================

# Initialize colorama
init(autoreset=True)


def connect_jenkins():
    server = jenkins.Jenkins(
        JENKINS_URL, username=USERNAME, password=API_TOKEN
    )
    user = server.get_whoami()
    version = server.get_version()
    print(f"\n✅ Connected to Jenkins {version} as {user['fullName']}")
    return server


def choose_job(jobs):
    print("\nAvailable jobs:")
    for i, job in enumerate(jobs, 1):
        print(f"{i}. {job}")

    while True:
        try:
            choice = int(input("\nSelect a job number to trigger: "))
            if 1 <= choice <= len(jobs):
                return jobs[choice - 1]
            print("Invalid choice. Try again.")
        except ValueError:
            print("Enter a valid number.")


def get_job_parameters(server, job_name):
    """Fetch parameter definitions for both freestyle and pipeline jobs."""
    job_info = server.get_job_info(job_name)
    params = []

    # Freestyle jobs
    for action in job_info.get("actions", []):
        if "parameterDefinitions" in action:
            params = action["parameterDefinitions"]
            break

    # Pipeline jobs
    if not params:
        for prop in job_info.get("property", []):
            if "parameterDefinitions" in prop:
                params = prop["parameterDefinitions"]
                break

    return params


def prompt_for_parameters(params):
    """Ask the user for parameter values based on Jenkins job config."""
    user_inputs = {}

    for p in params:
        name = p["name"]
        desc = p.get("description", "")
        param_type = p.get("_class", "")
        default = p.get("defaultParameterValue", {}).get("value", "")

        print(f"\n🧩 Parameter: {Fore.CYAN}{name}{Style.RESET_ALL}")
        if desc and desc != "None":
            print(f"   ↳ {desc}")

        # Choice parameter
        if "ChoiceParameterDefinition" in param_type:
            choices = p.get("choices", [])
            print("   Choices:")
            for i, c in enumerate(choices, 1):
                print(f"     {i}. {c}")
            val = input(
                f"   Enter choice number [default={default}]: "
            ).strip()
            if val.isdigit() and 1 <= int(val) <= len(choices):
                user_inputs[name] = choices[int(val) - 1]
            else:
                user_inputs[name] = default

        # Boolean parameter
        elif "BooleanParameterDefinition" in param_type:
            val = (
                input(f"   Enter value [y/N] (default={default}): ")
                .strip()
                .lower()
            )
            if not val:
                user_inputs[name] = default
            else:
                user_inputs[name] = val in ("y", "yes", "true", "1")

        # String/other parameter
        else:
            val = input(f"   Enter value [{default}]: ").strip() or default
            user_inputs[name] = val

    return user_inputs


def wait_for_build(server, job_name, queue_id):
    """Wait for the build to start and complete, showing colored status."""
    print("\n⏳ Waiting for build to start...")
    build_number = None
    while not build_number:
        qi = server.get_queue_item(queue_id)
        if "executable" in qi:
            build_number = qi["executable"]["number"]
            print(f"🚀 Build #{build_number} started!")
        time.sleep(2)

    # Wait for build completion
    while True:
        build_info = server.get_build_info(job_name, build_number)
        if build_info["building"]:
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(5)
        else:
            result = build_info["result"]
            if result == "SUCCESS":
                color = Fore.GREEN
            elif result == "FAILURE":
                color = Fore.RED
            elif result == "UNSTABLE":
                color = Fore.YELLOW
            else:
                color = Fore.CYAN

            print(
                f"\n✅ Build #{build_number} completed with status: {color}{result}{Style.RESET_ALL}"
            )
            print(f"🔗 URL: {build_info['url']}")
            break


def main():
    server = connect_jenkins()
    job_name = choose_job(TARGET_JOBS)
    print(f"\n📦 Selected job: {Fore.CYAN}{job_name}{Style.RESET_ALL}")

    params = get_job_parameters(server, job_name)
    if not params:
        print(
            f"⚠️ No parameters found — Triggering build:{job_name} without parameters."
        )
        i = input("Type proceed to continue:")
        if i != "proceed":
            return
        queue_id = server.build_job(job_name)
    else:
        user_inputs = prompt_for_parameters(params)
        print(f"\n🚀 Triggering build:{job_name}  with parameters:")
        for k, v in user_inputs.items():
            print(
                f"   - {Fore.CYAN}{k}{Style.RESET_ALL}: {Fore.GREEN}{v}{Style.RESET_ALL}"
            )

        i = input("Type proceed to continue:")
        if i != "proceed":
            return

        queue_id = server.build_job(job_name, parameters=user_inputs)

    print("Triggered build")

    # wait_for_build(server, job_name, queue_id)


if __name__ == "__main__":
    main()
