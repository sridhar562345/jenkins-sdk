import json

import ollama

SYSTEM_PROMPT = """
You are a deployment configuration formatter.

Your task is to convert raw deployment text into a json:

The input text contains:
- Tenant Name
- Environment
- P360
- Staff Web App
- Member Web App

You must extract the values and construct the json.

--------------------------------------------------

TENANT → ENVIRONMENT MAPPING

Use the following tenant mappings:

Love.Life OR LL → LL
Aurora Life OR AL → AURORLIFE
Attune → ATTUNE
Raffles → RAFFLES
MH OR Morrow → MH
Biopeak → BIOPEAK
Cereneo → CERENEO
IHL → IHL
Reya -> REYA

--------------------------------------------------

ENVIRONMENT NORMALIZATION

Environment values in input may appear as:

STG
Stg
Staging
stage
PROD
Production
Prod
QA
Dev

Normalize them to:

STG
PROD
QA
DEV

--------------------------------------------------

FINAL ENVIRONMENT FORMAT

Combine tenant + environment using:

<TENANT_CODE> <ENV>

Examples:

Love.Life + STG → LL STG
Aurora Life + STG → AURORLIFE STG
Raffles + Production → RAFFLES PROD
MH + Staging → MH STG
Cereneo + QA → CERENEO QA

--------------------------------------------------

DATA EXTRACTION RULES

1. Remove leading "v" from version numbers.
Example:
v1.13.0 → 1.13.0

2. Convert TRUE / YES → true

3. Convert FALSE / NO → false

4. Default values:

maintenance = False  
deploy_prebuilt_image = False  
build_only = False  
flutter_version = "3.38.3"

--------------------------------------------------


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
        "version_no": "<VERSION>", # Remove leading v
        "build_no": <BUILD_NO>,
        "maintenance": false
    },
    "member_web_app": {
        "environment": "<ENV_FROM_ALLOWED_LIST>",
        "flutter_version": "3.38.3",
        "tag": <TAG>,
        "reyakit_tag": "<REYAKIT_TAG>",
        "version_no": "<VERSION>", # remove leading v
        "build_no": <BUILD_NO>,
        "maintenance": false
    }
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
    }
}
```

If the tag is not present or P360/Staff Web App/Member web app : NO is given you can ignore that specific deployment_config like removing p360 key entirely from json.

IMPORTANT RULES

• Output only VALID JSON.
• Do not output python code or backticks.  
• Do NOT explain anything  
• Do NOT add markdown  
• Do NOT add comments  
• If a section (P360 / Staff / Member) is missing, omit that block from the json
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

    print(response_string)
    # print(python_dict)
    python_dict = json.loads(response_string)
    return python_dict


raw_text = """
Tenant Name:  AL 
Environment : STG 

P360 : 
Tag : 2641
Is database migration required: TRUE

Staff Web App:
Staff web app tag: 1141
Reyakit tag: 1576
Version number: v1.13.0
Build number: 8
 
Member web app : 
Member web app tag: 1170
Reyakit tag: 1576
Version number: v1.13.0
Build number: 8

[~accountid:557058:53b7ac09-9f07-44b2-88f3-da128a1b64aa] [~accountid:61f8a9048d9e3c00688e63cd] [~accountid:712020:596d07ff-07bd-401b-86ef-9f74a06e5830] 
"""

if __name__ == "__main__":
    r = convert_to_dict(raw_text)
    print(r)
