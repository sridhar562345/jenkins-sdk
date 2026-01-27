#!/usr/bin/env python3
import os
import sys
import time

import jenkins
from colorama import Fore, Style, init

# ======== CONFIGURE THESE ========
JENKINS_URL = os.environ["JENKINS_URL"]
USERNAME = os.environ["JENKINS_USERNAME"]
API_TOKEN = os.environ["JENKINS_API_TOKEN"]

TARGET_JOBS = [
    "🌐 P360",
    "💻 Staff Web App",
    "💻 Member Web App",
    "🌐 Processor",
    "🌐 Integration",
    "Release Pipeline",
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

        while True:
            i = input("Type proceed to continue:")
            if not i:
                continue
            if i == "proceed":
                break
            elif i != "proceed":
                print("Invalid input. Aborting build.")
                return

        print(job_name)
        print(user_inputs)
        queue_id = server.build_job(job_name, parameters=user_inputs)

    print("Triggered build")

    # wait_for_build(server, job_name, queue_id)


def trigger_p360(params):
    required_params = set(
        {
            "environment": "MH STG",
            "tag": "2517",
            "migrate": True,
            "maintenance": False,
            "deploy_prebuilt_image": False,
            "build_only": False,
        }.keys()
    )
    if len(required_params) != len(params):
        print("Required params not found.")
    elif set(required_params) != set(params.keys()):
        print("Required params not matched.")

    server = connect_jenkins()
    print(params)
    print(
        f"\n<UNK> Triggering 🌐 P360 build:{params['environment']}  with parameters:"
    )
    i = input("Type proceed to continue:")
    if i != "proceed":
        return
    queue_id = server.build_job("🌐 P360", parameters=params)
    print("Triggered build for p360")


def trigger_staff(params):
    required_params = set(
        {
            "environment": "RAFFLES STG",
            "flutter_version": "3.38.3",
            "tag": "1127",
            "reyakit_tag": "1507",
            "version_no": "1.12.0",
            "build_no": "5",
            "maintenance": False,
        }.keys()
    )
    if len(required_params) != len(params):
        print("Required params not found.")
    elif set(required_params) != set(params.keys()):
        print("Required params not matched.")
    server = connect_jenkins()
    print(params)

    print(
        f"\n<UNK> Triggering 💻 Staff Web App build:{params['environment']}  with parameters:"
    )
    i = input("Type proceed to continue:")
    if i != "proceed":
        return
    queue_id = server.build_job("💻 Staff Web App", parameters=params)
    print("Triggered build for staff")


def trigger_member(params):
    required_params = set(
        {
            "environment": "RAFFLES STG",
            "flutter_version": "3.38.3",
            "tag": "1148",
            "reyakit_tag": "1507",
            "version_no": "1.12.0",
            "build_no": "5",
            "maintenance": False,
        }.keys()
    )
    if len(required_params) != len(params):
        print("Required params not found.")
    elif set(required_params) != set(params.keys()):
        print("Required params not matched.")
    server = connect_jenkins()
    print(params)
    print(
        f"\n<UNK> Triggering 💻 Member Web App:{params['environment']}  with parameters:"
    )
    i = input("Type proceed to continue:")
    if i != "proceed":
        return
    queue_id = server.build_job("💻 Member Web App", parameters=params)
    print("Triggered build for member")


# if __name__ == "__main__":

    # trigger_p360(
    #     params={
    #         "environment": "IHL STG",
    #         "tag": "2519",
    #         "migrate": True,
    #         "maintenance": False,
    #         "deploy_prebuilt_image": True,
    #         "build_only": False,
    #     }
    # )
    # trigger_staff(
    #     params={
    #         "environment": "RAFFLES STG",
    #         "flutter_version": "3.38.3",
    #         "tag": "1127",
    #         "reyakit_tag": "1510",
    #         "version_no": "1.12.0",
    #         "build_no": "7",
    #         "maintenance": False,
    #     }
    # )
    # trigger_member(
    #     params={
    #         "environment": "RAFFLES STG",
    #         "flutter_version": "3.38.3",
    #         "tag": "1148",
    #         "reyakit_tag": "1510",
    #         "version_no": "1.12.0",
    #         "build_no": "7",
    #         "maintenance": False,
    #     }
    # )
