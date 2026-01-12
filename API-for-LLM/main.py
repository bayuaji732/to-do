from fastapi import FastAPI, Depends, HTTPException, Header
from ollama import Client
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY_CREDITS = {os.environ.get("API_KEY"): 5}
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
print(API_KEY_CREDITS)

app = FastAPI()

def verify_api_key(x_api_key: str = Header(None)):
    credits = API_KEY_CREDITS.get(x_api_key, 0)
    if credits <= 0:
        raise HTTPException(status_code=401, detail="Invalid API Key, or no credits")
    
    return x_api_key 

client = Client(host=OLLAMA_BASE_URL)

@app.post("/generate")
def generate(prompt: str, x_api_key: str = Depends(verify_api_key)):
    API_KEY_CREDITS[x_api_key] -= 1
    response = client.chat(model="mistral:7b", messages=[{"role": "user", "content": prompt}])
    return {"response": response["message"]["content"]}