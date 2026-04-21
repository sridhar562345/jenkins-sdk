import os

import requests
import re

BASE_URL = "https://reyahealth.atlassian.net/wiki"


def get_page(page_id, auth):
    """Fetch page with content, title, space, ancestors"""
    url = f"{BASE_URL}/rest/api/content/{page_id}?expand=body.storage,ancestors,space,title"
    res = requests.get(url, auth=auth)
    res.raise_for_status()
    return res.json()


def extract_parent_id(page_data):
    """Get parent page ID (for sibling creation)"""
    return (
        page_data["ancestors"][-1]["id"]
        if page_data.get("ancestors")
        else None
    )


def increment_version(text):
    """
    Finds x.y.z and increments patch version
    Returns: new_text, old_version, new_version
    """
    match = re.search(r"(\d+\.\d+\.\d+)", text)
    if not match:
        return text, None, None

    old_version = match.group(1)
    parts = list(map(int, old_version.split(".")))
    parts[-1] += 1

    new_version = ".".join(map(str, parts))
    new_text = text.replace(old_version, new_version)

    return new_text, old_version, new_version


def update_content_version(content, old_version, new_version):
    """Replace version everywhere in body"""
    if not old_version:
        return content
    return content.replace(old_version, new_version)


def create_page(title, content, space_key, parent_id, auth):
    """Create a new Confluence page"""
    url = f"{BASE_URL}/rest/api/content"

    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "ancestors": [{"id": parent_id}] if parent_id else [],
        "body": {"storage": {"value": content, "representation": "storage"}},
    }

    res = requests.post(url, json=payload, auth=auth)
    res.raise_for_status()
    return res.json()


if __name__ == "__main__":

    auth = (os.environ["JIRA_USERNAME"], os.environ["JIRA_API_KEY"])
    TENANT_SIBLING_MAP = {
        "IHL": "4117004289",
        "Reya": "4117037057",
        "Biopeak": "4117004297",
        "Aurora": "4117004305",
        "LL": "4117037065",
        "MH": "4117004313",
        "Attune": "4117037073",
        "Raffles": "4117037081",
        "Core": "4117037089",
        "Cereneo": "4117004321",
        "BLBG": "4125851651",
    }
    SOURCE_PAGE_ID = "4069228553"

    # Step 1: Fetch source page
    page = get_page(SOURCE_PAGE_ID, auth)

    title = page["title"]
    content = page["body"]["storage"]["value"]
    space_key = page["space"]["key"]

    version = input("Enter version:")

    print("@here Release Checklist for 1.14.0\n")
    for tenant, tenant_ref_page in TENANT_SIBLING_MAP.items():
        title = f"{tenant} Release {version} Checklist"
        tenant_ref_page = get_page(tenant_ref_page, auth)
        parent_id = extract_parent_id(tenant_ref_page)
        # Step 4: Create cloned page
        new_page = create_page(
            title=title,
            content=content,
            space_key=space_key,
            parent_id=parent_id,
            auth=auth,
        )
        links = new_page["_links"]

        print(f"{tenant}: {links['base']}{links['webui']}\n")
