import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

US_EAST_2_BODY = """
Hi All,

We plan to upgrade our azure {setup_name} setup with the {release_version} version of the {tenant_name} application on {date_string}, around {start_time_string} IST. The servers will be down and under maintenance for {maintenance_string}.

Date: {date_string}
Time: {start_end_time_string} IST
Reason: {release_version} release

Regards,
Sridhar
"""


def send_email(subject, body, recipients):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    sender_email = os.environ.get("GMAIL_EMAIL")
    sender_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not sender_email or not sender_password:
        print(
            "Please set GMAIL_EMAIL and GMAIL_APP_PASSWORD environment variables."
        )
        return

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(sender_email, sender_password)

            server.sendmail(
                sender_email,
                recipients,
                msg.as_string(),
            )

        print("Email sent successfully.")

    except Exception as e:
        print(f"Failed to send email: {e}")


def main():
    # select tenant name from available options
    tenant_options = [
        "Morrow Health",
        "Reya",
        "IHL",
        "Biopeak",
        "Auroralife",
        "Attune",
        "Raffles",
        "LL",
        "Cereneo",
        "Blue Bulgaria",
    ]
    for i, tenant_name in enumerate(tenant_options, 1):
        print(f"{i}. {tenant_name}")

    tenant_name = input("select tenant number: ")
    if not tenant_name.isdigit() or int(tenant_name) not in range(
        1, len(tenant_options) + 1
    ):
        print("Invalid tenant number.")
        return

    tenant_name = tenant_options[int(tenant_name) - 1]

    setup_options = ["USEAST-2", "WESTEUROPE", "ap-southeast-1"]
    for i, setup_name in enumerate(setup_options, 1):
        print(f"{i}. {setup_name}")

    setup_name = input("Select setup number: ")

    if not setup_name.isdigit() or int(setup_name) not in range(
        1, len(setup_options) + 1
    ):
        print("Invalid setup number.")
        return

    setup_name = setup_options[int(setup_name) - 1]

    date_string = input("Enter date string (e.g. 28th Jan 2026): ")
    start_time_string = input(
        "Enter start time string in IST (e.g. 3:00 PM): "
    )
    maintenance_string = input(
        "Enter maintenance string (e.g. one and half hours): "
    )
    start_end_time_string = input(
        "Enter start and end time string (e.g. 3:00 PM - 4:30 PM): "
    )
    release_version = input("Enter release version (e.g. 1.12.0): ")

    body = US_EAST_2_BODY.format(
        tenant_name=tenant_name,
        setup_name=setup_name,
        date_string=date_string,
        start_time_string=start_time_string,
        maintenance_string=maintenance_string,
        start_end_time_string=start_end_time_string,
        release_version=release_version,
    )

    subject = (
        f"Alert Regarding Downtime for "
        f"{tenant_name} Release {release_version}"
    )

    print("\nGenerated Email:\n")
    print(body)

    recipients_input = input("\nEnter recipient emails separated by comma: ")

    recipients = [
        email.strip() for email in recipients_input.split(",") if email.strip()
    ]

    send_now = input("Do you want to send the email? (y/n): ")

    if send_now.lower() == "y":
        send_email(subject, body, recipients)
    else:
        print("Email not sent.")


if __name__ == "__main__":
    main()
