import requests
from dotenv import load_dotenv
import os

load_dotenv()



url = "http://localhost:8000/generate?prompt=\"tell me about python\""

payload = {}
headers = {
  'x-api-key': os.environ.get("API_KEY")
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
