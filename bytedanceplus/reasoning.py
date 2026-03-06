import os
# Update Byteplus SDK to the latest version
# pip install -U 'byteplus-python-sdk-v2'
from byteplussdkarkruntime import Ark
from dotenv import load_dotenv

load_dotenv()


client = Ark(
    # Make sure that you have stored the API Key in the environment variable ARK_API_KEY
    api_key=os.environ.get("ARK_API_KEY"), 
    # The deep thinking model will take a relatively long time. Please set a longer timeout period to avoid a timeout, with 30 minutes or more recommended.
    timeout=1800,
    )
response = client.chat.completions.create(
    # Replace <Model> with the actual model name you are using.
    model="deepseek-v3-2-251201",
    messages=[
        {"role": "user", "content": "I need to research the topic of the distinction between deep thought models and non-deep thought models, demonstrating my professional expertise."}
    ],
     thinking={
         "type": "disabled" # default setting,
         # "type": "enabled"
     },
)
print(response)
