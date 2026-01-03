import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI")

AUTH_CODE = "PASTE_CODE_FROM_REDIRECT_HERE"

token_url = "https://www.linkedin.com/oauth/v2/accessToken"

payload = {
    "grant_type": "authorization_code",
    "code": AUTH_CODE,
    "redirect_uri": REDIRECT_URI,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
}

res = requests.post(token_url, data=payload)
res.raise_for_status()

token_data = res.json()
ACCESS_TOKEN = token_data["access_token"]

print("ACCESS TOKEN:")
print(ACCESS_TOKEN)

#--
import requests

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

url = "https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee"

res = requests.get(url, headers=headers)
print(res.json())


#--
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = "PASTE_ACCESS_TOKEN_HERE"
ORG_URN = os.getenv("LINKEDIN_ORG_URN")

url = "https://api.linkedin.com/v2/ugcPosts"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "X-Restli-Protocol-Version": "2.0.0",
    "Content-Type": "application/json"
}

payload = {
    "author": ORG_URN,
    "lifecycleState": "PUBLISHED",
    "specificContent": {
        "com.linkedin.ugc.ShareContent": {
            "shareCommentary": {
                "text": "Audit berjalan lancar itu bukan kebetulan. Itu hasil sistem."
            },
            "shareMediaCategory": "NONE"
        }
    },
    "visibility": {
        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
    }
}

res = requests.post(url, headers=headers, data=json.dumps(payload))
print(res.status_code)
print(res.text)
