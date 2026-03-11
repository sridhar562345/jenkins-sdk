import json

import ollama

SYSTEM_PROMPT = """
You are a configuration formatter.

Whenever I paste raw deployment details in a free-text format (tenant, environment, P360, Staff Web App, Member Web App), your task is to convert them into python Dictionary.

---

### 🧩 Parameter: environment

You must map the tenant + environment to **one of the following allowed values ONLY**. Ex: Tenant: *AL* + Environment: *Stg*/ *STG* = AURORLIFE STG.

1. LL QA
2. LL STG
3. LL PROD
4. REYA DEV
5. REYA QA
6. REYA PROD
7. IHL QA
8. IHL STG
9. IHL PROD
10. BIOPEAK STG
11. BIOPEAK PROD
12. AURORLIFE STG
13. AURORLIFE PROD
14. MH QA
15. MH STG
16. MH PROD
17. CORE PROD
18. ATTUNE STG
19. ATTUNE PROD
20. RAFFLES STG
21. RAFFLES PROD
22. CERENEO QA
23. CERENEO STG
24. CERENEO PROD

---

### 🚨 Strict Rules

* You **must** select the environment from the list above.
* If the correct environment **cannot be determined with certainty**, **DO NOT GUESS**.
* In that case, respond with **only this error message**:

```
ERROR: Unable to determine a valid environment from the provided input.
```

---

### General Rules

* Output **only JSON strings**, no explanations, no Python dictionaries.
* Always generate **three JSON strings**: `p360`, `staff_web_app`, and `member_web_app`.
* Remove leading `v` from version numbers.
* Convert `TRUE/FALSE` to JSON booleans (`true` / `false`).
* Use these defaults unless explicitly overridden:

  * `maintenance = false`
  * `deploy_prebuilt_image = false` (P360 only)
  * `build_only = false` (P360 only)
  * `flutter_version = "3.38.3"` (Staff & Member)

---

### Output Formats
1. If all deployments are given
```
{
    "p360": {
        "environment": "<ENV_FROM_ALLOWED_LIST>",
        "tag": <TAG>,
        "migrate": <true|false>,
        "maintenance": false,
        "deploy_prebuilt_image": false,
        "build_only": false
    },
    "staff_web_app": {
        "environment": "<ENV_FROM_ALLOWED_LIST>",
        "flutter_version": "3.38.3",
        "tag": "<TAG>,
        "reyakit_tag": "<REYAKIT_TAG>",
        "version_no": "<VERSION>",
        "build_no": <BUILD_NO>,
        "maintenance": false
    },
    "member_web_app": {
        "environment": "<ENV_FROM_ALLOWED_LIST>",
        "flutter_version": "3.38.3",
        "tag": <TAG>,
        "reyakit_tag": "<REYAKIT_TAG>",
        "version_no": "<VERSION>",
        "build_no": <BUILD_NO>,
        "maintenance": false
    },
}
```

2. specific deployment is not provided or given as No. Ex: p360 is no. Follow same for other deployment config.
```
{
    "staff_web_app": {
        "environment": "<ENV_FROM_ALLOWED_LIST>",
        "flutter_version": "3.38.3",
        "tag": "<TAG>,
        "reyakit_tag": "<REYAKIT_TAG>",
        "version_no": "<VERSION>",
        "build_no": <BUILD_NO>,
        "maintenance": false
    },
    "member_web_app": {
        "environment": "<ENV_FROM_ALLOWED_LIST>",
        "flutter_version": "3.38.3",
        "tag": <TAG>,
        "reyakit_tag": "<REYAKIT_TAG>",
        "version_no": "<VERSION>",
        "build_no": <BUILD_NO>,
        "maintenance": false
    },
}
```

If the tag is not present or P360/Staff Web App/Member web app : NO is given you can ignore that specific deployment_config like removing p360 key entirely from dict.

---

After this, I will paste raw text. Convert it accordingly into **JSON strings only**.
Output only VALID JSON.
Do not output python code or backticks.
"""


def convert_to_dict(text):
    response = ollama.chat(
        model="qwen2:7b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    response_string = (
        response["message"]["content"]
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    # print(response_string)
    # print(python_dict)
    python_dict = json.loads(response_string)
    return python_dict


raw_text = """
Tenant Name:Raffles 

Environment: Staging 

p360
	Required: Yes 
	Tag: 2636
	Is database migration required: yes

 

Member web app
	Required: Yes 
	Member web app tag: 1170
	Reyakit tag: 1573
	Version number: 1.13.0
	Build number: 12

[~accountid:557058:53b7ac09-9f07-44b2-88f3-da128a1b64aa] [~accountid:61f8a9048d9e3c00688e63cd] [~accountid:712020:596d07ff-07bd-401b-86ef-9f74a06e5830] 
"""

if __name__ == "__main__":
    r = convert_to_dict(raw_text)
    print(r)
