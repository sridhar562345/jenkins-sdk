import subprocess

# subprocess.run(["say", "Your 🌐 P360 job is finished"])
subprocess.run(
    [
        "osascript",
        "-e",
        'display notification "Notification text" with title "Notification Title" sound name "Glass"',
    ]
)
