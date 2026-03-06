import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


# Make sure that you have stored the API Key in the environment variable ARK_API_KEY
# Initialize the Openai client to read your API Key from the environment variable
client = OpenAI(
    # This is the default path. You can configure it based on the service location
    base_url="https://ark.ap-southeast.bytepluses.com/api/v3",
    # Get your API Key from the environment variable
    api_key=os.environ.get("ARK_API_KEY"),
)
response = client.chat.completions.create(
    # Specify the Ark Inference Point ID that you created, which has been changed for you here to your Endpoint ID
    model="seed-2-0-mini-260215",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-doc.tos-ap-southeast-1.bytepluses.com/see_i2v.jpeg"
                    },
                },
                {"type": "text", "text": "Where is this？"},
            ],
        }
    ],
)
print(response.choices[0])