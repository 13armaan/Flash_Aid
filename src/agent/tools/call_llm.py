import os
import sys
import requests
import traceback
from dotenv import load_dotenv

load_dotenv()

def call(prompt: str, model: str = "kimi-k2-0711-preview") -> str:
    try:
        api_key = os.getenv("MOONSHOT_API_KEY")
      
        if not api_key:
            return "(Moonshot LLM error) Missing API key. Set MOONSHOT_API_KEY."

        base_url = os.getenv("MOONSHOT_BASE_URI", "https://api.moonshot.ai/v1")
        endpoint = f"{base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "user",
                 "content": prompt
                 },
                
                 ]
        }

        resp = requests.post(endpoint, json=payload, headers=headers, timeout=60)
      
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("LLM ERROR OCCURED")
        print("Error:",e)
        traceback.print_exc()
        return f"(MOONSHOT LLM ERROR) {e}\n\nPrompt:\n{prompt[:1200]}"  

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/tools/call_llm.py \"your prompt here\"")
        sys.exit(1)

    prompt = sys.argv[1]
    output = call(prompt)
    print(output)

#This is now both executable from cli and can also be imported