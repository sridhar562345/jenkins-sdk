US_EAST_2_BODY = """
Alert Regarding Downtime for {tenant_name} Release {release_version}

Hi All,

We plan to upgrade our azure USEAST-2 setup with the {release_version} version of the {tenant_name} application on {date_string}, around {start_time_string} IST. The servers will be down and under maintenance for {maintenance_string}.

Date: {date_string}
Time: {start_end_time_string} IST
Reason: {release_version} release

Regards,
Sridhar
"""


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
    print(
        US_EAST_2_BODY.format(
            tenant_name=tenant_name,
            date_string=date_string,
            start_time_string=start_time_string,
            maintenance_string=maintenance_string,
            start_end_time_string=start_end_time_string,
            release_version=release_version,
        )
    )


if __name__ == "__main__":
    main()
