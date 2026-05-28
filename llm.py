import datetime
import json
import os
from typing import Dict, List
import requests

# enum for model types - ollama vs openai vs gemini
OLLAMA = "ollama"
OPENAI = "openai"
GEMINI = "gemini"
LLAMA_3_2 = "llama3.2"
QWEN_3_4B = "qwen3:4b"
QWEN_3_8B = "qwen3:8b"
QWEN_3_5_4B = "qwen3.5:4b"
QWEN_3_5_9B = "qwen3.5:9b"
GEMMA_4_E4B = "gemma4:e4b"
GPT_4O = "gpt-4o"
GPT_4O_MINI = "gpt-4o-mini"
GPT_4_1_MINI = "gpt-4.1-mini"
GPT_5_NANO = "gpt-5-nano"
GPT_5_MINI = "gpt-5-mini"
GEMINI_2_0_FLASH = "gemini-2.0-flash"
GEMINI_2_0_FLASH_LITE = "gemini-2.0-flash-lite"
GEMINI_2_5_FLASH_PREVIEW_05_20 = "gemini-2.5-flash-preview-05-20"
GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"
GEMINI_2_5_FLASH = "gemini-2.5-flash"
GEMINI_2_5_PRO = "gemini-2.5-pro"
GEMINI_3_FLASH_PREVIEW = "gemini-3-flash-preview"
MODELS = {
    OLLAMA: {LLAMA_3_2, QWEN_3_4B, QWEN_3_8B, QWEN_3_5_4B, QWEN_3_5_9B, GEMMA_4_E4B},
    OPENAI: {
        GPT_4O,         # expensive, haven't tried yet
        GPT_4O_MINI,    # gets lost eventually
        GPT_4_1_MINI,   # somewhat coherent? but gets repeaty and makes incorrect logical inferences
        GPT_5_NANO,     # immediately gets lost
        GPT_5_MINI,     # can't help but out itself as minion, but good players can deduce decently
    },
    GEMINI: {
        GEMINI_2_0_FLASH,
        GEMINI_2_0_FLASH_LITE,
        GEMINI_2_5_FLASH_PREVIEW_05_20,
        GEMINI_2_5_FLASH_LITE,
        GEMINI_2_5_FLASH,
        GEMINI_2_5_PRO,
        GEMINI_3_FLASH_PREVIEW
    },
}
MODELS_LIST = [model for values in MODELS.values() for model in values]

class ModelError(Exception):
    pass

with open("system_message.txt", "r") as f:
    SYSTEM_MESSAGE = f.read()

def get_response(model: str, history: List[Dict[str, str]], name: str) -> str:
    system_message = {
        "role": "system",
        "content": SYSTEM_MESSAGE.format(name=name)
    }
    messages = [system_message] + history

    data = { 
        "model": model,
        "messages": messages,
        # "think": False,
        "stream": False
    }

    if model in MODELS[GEMINI]:
        return get_gemini_response(data)
    elif model in MODELS[OPENAI]:
        return get_openai_response(data)
    elif model in MODELS[OLLAMA]:
        return get_ollama_response(data)
    else:
        raise ModelError(f"model {model} not supported")

def get_ollama_response(data: Dict[str, any]):
    resp = requests.post("http://localhost:11434/api/chat", json=data)
    if resp.status_code == 200:
        try:
            return resp.json()["message"]["content"]
        except json.JSONDecodeError as e:
            print(resp.text)
            raise e
    raise ModelError(f"error prompting model: {resp.text}")

def get_openai_response(data: Dict[str, any]):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    resp = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    with open("error_log.txt", "a") as f:
        f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {resp.text}\n")
    raise ModelError(f"error prompting model: {resp.text}")

def get_gemini_response(data: Dict[str, any]):
    headers = {
        "Content-Type": "application/json",
    }

    gemini_data = {
        "system_instruction": {
            "parts": [{
                "text": data["messages"][0]["content"]
            }]
        },
        "contents": [
            {
                "role": "user" if m["role"] == "user" else "model",
                "parts": [{
                    "text": m["content"]
                }]
            } for m in data["messages"][1:]
        ]
    }
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    resp = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{data['model']}:generateContent?key={gemini_api_key}", json=gemini_data, headers=headers)
    if resp.status_code == 200:
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    with open("error_log.txt", "a") as f:
        f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {resp.text}\n")
    raise ModelError(f"error prompting model: {resp.text}")