import os
import sys
import requests
import traceback
from dotenv import load_dotenv
import httpx

load_dotenv()

async def call_llm_stream(prompt:str, model:str="kimi-k2-0711-preview")-> str:
    try:
        api_key = os.getenv("MOONSHOT_API_KEY")
      
        if not api_key:
            print("(Moonshot LLM error) Missing API key. Set MOONSHOT_API_KEY.")

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
                 }
                ],
                "stream": True
        }
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("POST",endpoint,json=payload,headers=headers) as resp:
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    if line.startswith("data: "):
                        data=line[len("data: "):]
                        if data.strip()=="[DONE]":
                            break
                        chunk=json.loads(data)
                        delta=chunk["choices"][0]["delta"]
                        if "content" in delta:
                            yield delta["content"]
    except Exception as e:
        print("LLM STREAM ERROR OCCURED")
        traceback.print_exc()
        yield f"(MOONSHOT LLM ERROR {e})"
async def call_llm_normal(prompt: str, model: str = "kimi-k2-0711-preview") -> str:
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
                #"stream": True
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(endpoint, json=payload, headers=headers)
      
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