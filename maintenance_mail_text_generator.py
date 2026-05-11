import os
import re
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pytz
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
    "Core",
]

SETUP_OPTIONS = ["USEAST-2", "WESTEUROPE", "ap-southeast-1"]

# Display label → IANA timezone name
# pytz resolves PST vs PDT, EST vs EDT, CET vs CEST etc. automatically from the date
TIMEZONE_MAP = {
    "IST": "Asia/Kolkata",
    "SGT": "Asia/Singapore",
    "UAE": "Asia/Dubai",  # Gulf Standard Time, UTC+4, no DST
    "EET": "Europe/Helsinki",  # Eastern European (handles EEST in summer)
    "CET": "Europe/Berlin",  # Central European (handles CEST in summer)
    "UTC": "UTC",
    "US/Pacific": "America/Los_Angeles",  # PST / PDT
}

# Timezone defaults per tenant
TENANT_DEFAULT_TZ = {
    "LL": ["IST", "US/Pacific"],  # PST / PDT
    "Reya": ["IST"],
    "IHL": ["IST", "UAE"],
    "Auroralife": ["IST", "US/Pacific"],  # PDT / PST
    "Biopeak": ["IST"],
    "Morrow Health": ["IST", "SGT"],
    "Core": ["IST"],
    "Attune": ["IST", "US/Pacific"],  # PST / PDT
    "Raffles": ["IST", "SGT"],
    "Cereneo": ["IST", "CET"],
    "Blue Bulgaria": ["IST", "EET"],
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

DATE_FORMATS = [
    "%d %b %Y",  # 12 May 2026
    "%d %B %Y",  # 12 May 2026 (full month name)
    "%d/%m/%Y",  # 12/05/2026
    "%Y-%m-%d",  # 2026-05-12
]

TIME_FORMATS = [
    "%I:%M %p",  # 9:00 AM
    "%I:%M%p",  # 9:00AM
    "%H:%M",  # 09:00 / 14:30
]


def parse_date(date_str: str) -> datetime.date:
    """Parse a date string, stripping ordinal suffixes like 'th', 'st', 'nd', 'rd'."""
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str.strip())
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    raise ValueError(
        f"Could not parse date: '{date_str}'. "
        "Try '12 May 2026', '12th May 2026', or '12/05/2026'."
    )


def parse_time(time_str: str) -> datetime.time:
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(time_str.strip(), fmt).time()
        except ValueError:
            continue
    raise ValueError(
        f"Could not parse time: '{time_str}'. Use '9:00 AM' or '14:30'."
    )


def make_aware(
    date: datetime.date, time: datetime.time, tz_label: str
) -> datetime:
    tz = pytz.timezone(TIMEZONE_MAP[tz_label])
    return tz.localize(datetime.combine(date, time))


def convert_and_format(
    dt_aware: datetime, to_tz_label: str
) -> tuple[str, str]:
    """Return (formatted time string, resolved abbreviation e.g. PDT)."""
    tz = pytz.timezone(TIMEZONE_MAP[to_tz_label])
    converted = dt_aware.astimezone(tz)
    abbrev = converted.strftime("%Z")  # PDT, EDT, CEST, etc.
    time_str = converted.strftime("%I:%M %p").lstrip("0")
    return time_str, abbrev


def build_timezone_block(
    date: datetime.date,
    start_str: str,
    end_str: str,
    tz_labels: list[str],
) -> str:
    start_ist = make_aware(date, parse_time(start_str), "IST")
    end_ist = make_aware(date, parse_time(end_str), "IST")

    lines = []
    for label in tz_labels:
        s_time, s_abbrev = convert_and_format(start_ist, label)
        e_time, _ = convert_and_format(end_ist, label)
        # Show the resolved abbreviation (PDT/PST, EDT/EST, CEST/CET…)
        display = s_abbrev if s_abbrev not in ("LMT", "") else label
        lines.append(f"{display} - {s_time} - {e_time}")

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

    try:
        parsed_date = parse_date(date_string)
    except ValueError as e:
        print(f"\n[!] {e}")
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

    # Timezone selection — pre-tick tenant defaults
    all_tz = list(TIMEZONE_MAP.keys())
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

    # IST always first
    selected_tz = ["IST"] + [tz for tz in selected_tz if tz != "IST"]

    start_end_time_string = f"{start_time_string} - {end_time_string}"

    try:
        timezone_block = build_timezone_block(
            parsed_date, start_time_string, end_time_string, selected_tz
        )
    except ValueError as e:
        print(f"\n[!] Timezone conversion failed: {e}")
        return

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
