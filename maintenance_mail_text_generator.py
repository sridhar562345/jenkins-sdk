import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import questionary
from questionary import Style

cli_style = Style(
    [
        ("qmark", "fg:#5F5E5A bold"),
        ("question", "bold"),
        ("answer", "fg:#185FA5 bold"),
        ("pointer", "fg:#185FA5 bold"),
        ("highlighted", "fg:#185FA5 bold"),
        ("selected", "fg:#185FA5"),
        ("separator", "fg:#B4B2A9"),
        ("instruction", "fg:#B4B2A9"),
    ]
)

TENANT_OPTIONS = [
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

SETUP_OPTIONS = ["USEAST-2", "WESTEUROPE", "ap-southeast-1"]

# IST offset from UTC in hours
TIMEZONE_OFFSETS_FROM_UTC = {
    "IST": 5.5,
    "EET": 3.0,
    "CET": 2.0,
    "UTC": 0.0,
    "EST": -4.0,
    "PST": -7.0,
    "SGT": 8.0,
}

# Timezone defaults per tenant — add more zones alongside IST as needed
TENANT_DEFAULT_TZ = {
    "Morrow Health": ["IST", "SGT"],
    "Reya": ["IST"],
    "IHL": ["IST", ""],
    "Biopeak": ["IST"],
    "Auroralife": ["IST"],
    "Attune": ["IST"],
    "Raffles": ["IST"],
    "LL": ["IST"],
    "Cereneo": ["IST"],
    "Blue Bulgaria": ["IST"],
}

EMAIL_BODY_TEMPLATE = """\
Hi All,

We plan to upgrade our azure {setup_name} setup with the {release_version} version of the {tenant_name} application on {date_string}, around {start_time_string} IST. The servers will be down and under maintenance for {maintenance_string}.

Date: {date_string}
Time: {start_end_time_string} IST
Reason: {release_version} release

Time zones are as follows:
{timezone_block}

Regards,
Sridhar
"""


def parse_time(time_str: str) -> datetime:
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
        try:
            return datetime.strptime(time_str.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(
        f"Could not parse time: '{time_str}'. Use format like '9:00 AM' or '14:30'."
    )


def convert_time(dt: datetime, from_tz: str, to_tz: str) -> datetime:
    from_offset = TIMEZONE_OFFSETS_FROM_UTC[from_tz]
    to_offset = TIMEZONE_OFFSETS_FROM_UTC[to_tz]
    delta_hours = to_offset - from_offset
    return dt + timedelta(hours=delta_hours)


def build_timezone_block(
    start_str: str, end_str: str, timezones: list[str]
) -> str:
    start_dt = parse_time(start_str)
    end_dt = parse_time(end_str)
    lines = []
    for tz in timezones:
        s = convert_time(start_dt, "IST", tz)
        e = convert_time(end_dt, "IST", tz)
        lines.append(
            f"{tz} - {s.strftime('%I:%M %p').lstrip('0')} - {e.strftime('%I:%M %p').lstrip('0')}"
        )
    return "\n".join(lines)


def send_email(subject: str, body: str, recipients: list[str]) -> None:
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    sender_email = os.environ.get("GMAIL_EMAIL")
    sender_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not sender_email or not sender_password:
        print(
            "\n[!] Set GMAIL_EMAIL and GMAIL_APP_PASSWORD environment variables to send."
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
            server.sendmail(sender_email, recipients, msg.as_string())
        print("\n✓ Email sent successfully.")
    except Exception as e:
        print(f"\n[!] Failed to send email: {e}")


def main() -> None:
    print()

    tenant_name = questionary.select(
        "Tenant:",
        choices=TENANT_OPTIONS,
        style=cli_style,
    ).ask()
    if not tenant_name:
        return

    setup_name = questionary.select(
        "Setup / Region:",
        choices=SETUP_OPTIONS,
        style=cli_style,
    ).ask()
    if not setup_name:
        return

    release_version = questionary.text(
        "Release version:",
        placeholder="e.g. 1.14.0",
        style=cli_style,
    ).ask()
    if not release_version:
        return

    date_string = questionary.text(
        "Date:",
        placeholder="e.g. 12th May 2026",
        style=cli_style,
    ).ask()
    if not date_string:
        return

    start_time_string = questionary.text(
        "Start time (IST):",
        placeholder="e.g. 9:00 AM",
        style=cli_style,
    ).ask()
    if not start_time_string:
        return

    end_time_string = questionary.text(
        "End time (IST):",
        placeholder="e.g. 11:00 AM",
        style=cli_style,
    ).ask()
    if not end_time_string:
        return

    maintenance_string = questionary.text(
        "Maintenance duration:",
        placeholder="e.g. 2 hrs",
        style=cli_style,
    ).ask()
    if not maintenance_string:
        return

    # Timezone selection — pre-tick defaults for the chosen tenant
    all_tz = list(TIMEZONE_OFFSETS_FROM_UTC.keys())
    default_tz = TENANT_DEFAULT_TZ.get(tenant_name, ["IST"])
    selected_tz = questionary.checkbox(
        "Timezones to include in email:",
        choices=[
            questionary.Choice(tz, checked=(tz in default_tz)) for tz in all_tz
        ],
        style=cli_style,
    ).ask()
    if not selected_tz:
        selected_tz = default_tz

    # Always keep IST first
    if "IST" not in selected_tz:
        selected_tz = ["IST"] + selected_tz
    else:
        selected_tz = ["IST"] + [tz for tz in selected_tz if tz != "IST"]

    start_end_time_string = f"{start_time_string} - {end_time_string}"

    try:
        timezone_block = build_timezone_block(
            start_time_string, end_time_string, selected_tz
        )
    except ValueError as e:
        print(f"\n[!] Timezone conversion failed: {e}")
        timezone_block = "\n".join(
            f"{tz} - (could not compute)" for tz in selected_tz
        )

    body = EMAIL_BODY_TEMPLATE.format(
        tenant_name=tenant_name,
        setup_name=setup_name,
        date_string=date_string,
        start_time_string=start_time_string,
        maintenance_string=maintenance_string,
        start_end_time_string=start_end_time_string,
        release_version=release_version,
        timezone_block=timezone_block,
    )

    subject = (
        f"Alert Regarding Downtime for {tenant_name} Release {release_version}"
    )

    print("\n" + "─" * 60)
    print(f"Subject: {subject}\n")
    print(body)
    print("─" * 60)

    recipients_raw = questionary.text(
        "Recipients (comma-separated):",
        placeholder="alice@example.com, bob@example.com",
        style=cli_style,
    ).ask()
    if not recipients_raw:
        return

    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    confirm = questionary.confirm(
        f"Send to {len(recipients)} recipient(s)?",
        default=False,
        style=cli_style,
    ).ask()

    if confirm:
        send_email(subject, body, recipients)
    else:
        print("Email not sent.")


if __name__ == "__main__":
    main()
