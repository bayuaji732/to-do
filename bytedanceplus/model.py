from openai import OpenAI
import os

from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    # Replace with the Base Url of the model service you need to call
    base_url="https://ark.ap-southeast.bytepluses.com/api/v3",
    # Configure your API Key in the environment variable
    api_key=os.environ.get("ARK_API_KEY")
)

print("----- standard request -----")
completion = client.chat.completions.create(
    # Replace <Model> with Endpoint ID（or Model ID）
    model="deepseek-v3-2-251201",
    messages = [
        {"role": "system", "content": "You are Skylark, an AI assistant developed by BytePlus"},
        {"role": "user", "content": "What are the common cruciferous plants?"},
    ],
)
print(completion.choices[0].message.content)