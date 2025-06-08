import datetime
import json
import os
from typing import Dict, List
import requests
from characters import RECLUSE, SPY, TOWNSFOLK, OUTSIDERS, MINIONS, DEMONS

# enum for model types - ollama vs openai vs gemini
OLLAMA = "ollama"
OPENAI = "openai"
GEMINI = "gemini"
LLAMA_3_2 = "llama3.2"
QWEN_3_4B = "qwen3:4b"
GPT_4O = "gpt-4o"
GPT_4O_MINI = "gpt-4o-mini"
GEMINI_2_0_FLASH = "gemini-2.0-flash"
GEMINI_2_0_FLASH_LITE = "gemini-2.0-flash-lite"
GEMINI_2_5_FLASH_PREVIEW_05_20 = "gemini-2.5-flash-preview-05-20"
MODELS = {
    OLLAMA: {LLAMA_3_2, QWEN_3_4B},
    OPENAI: {GPT_4O, GPT_4O_MINI}, # these names are unchecked
    GEMINI: {GEMINI_2_0_FLASH, GEMINI_2_0_FLASH_LITE, GEMINI_2_5_FLASH_PREVIEW_05_20},
}

MODEL = GEMINI_2_5_FLASH_PREVIEW_05_20

class ModelError(Exception):
    pass

with open("system_message.txt", "r") as f:
    SYSTEM_MESSAGE = f.read()

def get_response(history: List[Dict[str, str]], name: str) -> str:
    system_message = {
        "role": "system",
        "content": SYSTEM_MESSAGE.format(name=name)
    }
    messages = [system_message] + history
    
    data = { 
        "model": MODEL,
        "messages": messages,
        "stream": False
    }
    
    # json.dump(data, open("data.json", "w"))
    if MODEL in MODELS[GEMINI]:
        return get_gemini_response(data)
    elif MODEL in MODELS[OPENAI]:
        return get_openai_response(data)
    elif MODEL in MODELS[OLLAMA]:
        return get_ollama_response(data)
    else:
        raise ModelError(f"model {MODEL} not supported")

def get_ollama_response(data: Dict[str, any]):
    resp = requests.post("http://localhost:11434/api/chat", json=data)
    if resp.status_code == 200:
        return resp.json()["message"]["content"]
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
    resp = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key=AIzaSyCUnE7aaR-R0pj15GiIGycqxql0EhxC6pM", json=gemini_data, headers=headers)
    if resp.status_code == 200:
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    with open("error_log.txt", "a") as f:
        f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {resp.text}\n")
    raise ModelError(f"error prompting model: {resp.text}")

def registers_as_townsfolk(character: str) -> bool:
    return character.lower() in TOWNSFOLK or character.lower() == SPY

def registers_as_outsider(character: str) -> bool:
    # TODO: spy probably shouldn't register 100% of the time,
    # otherwise in 0-outsider spy games, lib always sees the spy
    return character.lower() in OUTSIDERS or character.lower() == SPY

def registers_as_minion(character: str) -> bool:
    # TODO: should spy be false here sometimes?? Likewise with recluse in registers_as_outsider
    return character.lower() in MINIONS or character.lower() == RECLUSE

def registers_as_demon(character: str) -> bool:
    return character.lower() in DEMONS or character.lower() == RECLUSE

def log(message: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a") as f:
        f.write(f"{timestamp} {message}\n")

