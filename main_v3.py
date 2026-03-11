#!/usr/bin/env python3
import json
import os
import sys
import time
from urllib.parse import quote

import jenkins
import requests
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor

from jira_issue_tracker import get_issue_by_ticket
from text_to_dict import convert_to_dict

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


def is_input_action_pending(job_name, build_number):
    url = f"{JENKINS_URL}/job/{job_name}/{build_number}/wfapi/pendingInputActions"
    r = requests.get(url, auth=(USERNAME, API_TOKEN))
    # print(r.json())
    r.raise_for_status()

    return bool(r.json())


def input_proceed(job_name, build_number):
    # Send approval with parameter
    data = {
        "json": '{"parameter":[{"name":"confirm","value":true}]}',
    }
    params = {
        "inputId": "UserConfirmation",
    }
    response = requests.post(
        url=f"{JENKINS_URL}/job/{job_name}/{build_number}/wfapi/inputSubmit",
        auth=(USERNAME, API_TOKEN),
        data=data,
        params=params,
    )
    response.raise_for_status()
    print("Input proceed successful")


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

    # Wait for input step
    while True:
        is_input_pending = is_input_action_pending(
            job_name=job_name, build_number=build_number
        )
        if is_input_pending:
            break
        else:
            time.sleep(3)

    # Send input
    input_proceed(job_name=job_name, build_number=build_number)

    # Wait for build completion
    print("Waiting for build to complete")
    while True:
        build_info = server.get_build_info(job_name, build_number)
        if build_info["building"]:
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(30)
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
        raise Exception("Required params not found.")
    elif set(required_params) != set(params.keys()):
        raise Exception("Required params not matched.")

    server = connect_jenkins()
    print(
        f"\n Triggering {Fore.RED}🌐 P360 build:{params['environment']} {Style.RESET_ALL}  with parameters:"
    )
    for k, v in params.items():
        print(
            f"   - {Fore.CYAN}{k}{Style.RESET_ALL}: {Fore.GREEN}{v}{Style.RESET_ALL}"
        )

    i = input("Type proceed to continue:")
    if i != "proceed":
        return
    job_name = "🌐 P360"
    queue_id = server.build_job(job_name, parameters=params)
    print("Triggered build for p360")

    wait_for_build(job_name=job_name, queue_id=queue_id, server=server)


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
        raise Exception("Required params not found.")
    elif set(required_params) != set(params.keys()):
        raise Exception("Required params not matched.")
    server = connect_jenkins()
    job_name = "💻 Staff Web App"

    print(
        f"\n {Fore.RED}Triggering {job_name} build:{params['environment']}  with parameters:{Style.RESET_ALL}"
    )
    for k, v in params.items():
        print(
            f"   - {Fore.CYAN}{k}{Style.RESET_ALL}: {Fore.GREEN}{v}{Style.RESET_ALL}"
        )

    # i = input("Type proceed to continue:")
    # if i != "proceed":
    #     return
    queue_id = server.build_job(job_name, parameters=params)
    print("Triggered build for staff")
    wait_for_build(server=server, queue_id=queue_id, job_name=job_name)


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
        raise Exception("Required params not found.")
    elif set(required_params) != set(params.keys()):
        raise Exception("Required params not matched.")
    job_name = "💻 Member Web App"
    server = connect_jenkins()
    print(
        f"\n {Fore.RED}Triggering {job_name}:{params['environment']}  with parameters:{Style.RESET_ALL}"
    )
    for k, v in params.items():
        print(
            f"   - {Fore.CYAN}{k}{Style.RESET_ALL}: {Fore.GREEN}{v}{Style.RESET_ALL}"
        )
    # i = input("Type proceed to continue:")
    # if i != "proceed":
    #     return
    queue_id = server.build_job(job_name, parameters=params)
    print("Triggered build for member")
    wait_for_build(server=server, queue_id=queue_id, job_name=job_name)


def trigger_release_pipeline(params):
    job_name = "Release Pipeline"
    required_params = set(
        {
            "applications": "staff-web-app",
            "region": "centralindia",
            "environment": "qa",
            "tenant": "reya",
            "maintenance": "end",
            "backup": False,
        }.keys()
    )
    if len(required_params) != len(params):
        raise Exception("Required params not found.")
    elif set(required_params) != set(params.keys()):
        raise Exception("Required params not matched.")
    server = connect_jenkins()
    print(
        f"\n {Fore.RED}Triggering {job_name}:{params['environment']}  with parameters:{Style.RESET_ALL}"
    )
    for k, v in params.items():
        print(
            f"   - {Fore.CYAN}{k}{Style.RESET_ALL}: {Fore.GREEN}{v}{Style.RESET_ALL}"
        )
    i = input("Type proceed to continue:")
    if i != "proceed":
        return
    queue_id = server.build_job(job_name, parameters=params)
    print(f"Triggered build for {job_name}")
    wait_for_build(server=server, queue_id=queue_id, job_name=job_name)


def main():
    ticket_id = input("Enter ticket ID:")
    description = get_issue_by_ticket(ticket_id=ticket_id)
    print(description)

    deployment_config = convert_to_dict(text=description)
    print("*" * 100)
    print(json.dumps(deployment_config, indent=4))

    i = input("Type proceed to continue:")
    if i != "proceed":
        return

    # Run p360 first
    if "p360" in deployment_config:
        if deployment_config["p360"]:
            i = input("Deploy with prebuilt image (y/n):")
            params = deployment_config["p360"]
            if i == "y":
                params["deploy_prebuilt_image"] = True
            trigger_p360(params=params)

    parallel_tasks = []

    if "staff_web_app" in deployment_config:
        if deployment_config["staff_web_app"]:
            parallel_tasks.append(
                lambda: trigger_staff(
                    params=deployment_config["staff_web_app"]
                )
            )

    if "member_web_app" in deployment_config:
        if deployment_config["member_web_app"]:
            parallel_tasks.append(
                lambda: trigger_member(
                    params=deployment_config["member_web_app"]
                )
            )

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(task) for task in parallel_tasks]
        for f in futures:
            f.result()


if __name__ == "__main__":
    main()
