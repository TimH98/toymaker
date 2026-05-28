import argparse
import shutil
from llm import MODELS_LIST
from storyteller import Storyteller


PLAYER_NAMES = [
    "Alice",
    "Bob",
    "Charlie",
    "Daniel",
    "Edd",
    "Frank",
    "George"
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", help=f"LLM to use. Supported options are: {", ".join(MODELS_LIST)}.Note OpenAI models require the \"OPENAI_API_KEY\" env var, and Gemini models require the \"GEMINI_API_KEY\" env var.")
    parser.add_argument("--spectate", action=argparse.BooleanOptionalAction, help="Whether to have an LLM-only game (--spectate) or include one human player (--no-spectate). Default is --no-spectate.")
    args = parser.parse_args()
    shutil.copy("log.txt", "log.txt.old")
    open("log.txt", "w").close()
    storyteller = Storyteller(PLAYER_NAMES, args.model, args.spectate)
    storyteller.first_night()
    while True:
        storyteller.day()
        storyteller.nominations()
        storyteller.other_nights()

if __name__ == "__main__":
    main()

