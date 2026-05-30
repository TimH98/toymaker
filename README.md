# Toymaker: AI Storyteller & Player for Blood on the Clocktower

*Finally, I've fully automated my favorite game so I don't have to bother playing anymore*

This script will run a game of [Blood on the Clocktower](https://bloodontheclocktower.com/) from start to finish, with a programmatic Storyteller and LLM-powered players. It also provides the option to participate in the game, creating a single-player BotC experience.

## Usage

`python main.py model_name [--spectate]`

This starts a 7-player game of Trouble Brewing, with output to player 1 (named "Alice") being printed to the console. By default, the user plays as Alice and provides inputs for that player. Providing the `--spectate` arg allows an LLM to control Alice, with Alice's perspective being printed to the console.

All players' perspectives are logged to `log.txt`, giving a bird's-eye view of the game.

Supported `model_name` values are as follows. New models can be added in `llm.py`.
- gemma4:e4b
- llama3.2
- qwen3.5:4b
- qwen3:8b
- qwen3:4b
- qwen3.5:9b
- gpt-4.1-mini
- gpt-4o-mini
- gpt-4o
- gpt-5-nano
- gpt-5-mini
- gemini-2.0-flash-lite
- gemini-2.0-flash
- gemini-2.5-flash-lite
- gemini-2.5-flash
- gemini-2.5-flash-preview-05-20
- gemini-2.5-pro
- gemini-3-flash-preview

Note:
- `gpt` models require setting the `OPENAI_API_KEY` environment variable.
- `gemini` models require setting the `GEMINI_API_KEY` environment variable.
- All other models require a running ollama session on your device with the associated model.

## Architecture

### Storyteller

`storyteller.py`

Provides functionality for the main game loop.

- `select_characters()` - Choose the appropriate number of townsfolk, outsiders, minions, and demons for the game. Also selects 3 out-of-play good characters to give to the demon as bluffs, and determines what character the Drunk will think they are.
- `first_night()` and `other_nights()` - Prompt characters with night abilities on night 1 and subsequent nights, respectively
- `day()` - Run the day phase by giving each player a set number of turns. Each turn, a player may speak publicly or whisper privately to another player. The number of turns per day depends on player count and can be easily modified at the top of `storyteller.py`.
- `nominations()` - Run the nomination phase. Gives each player the opportunity to nominate another player and runs votes on players as required. At the end of the phase, the player with the most votes is executed. Note that no discussion happens during the nomination phase to save on context size.


### GameState

`gamestate.py`

Tracks which player is which character, ongoing status effects & reminders, and generates information for information-gathering characters.

`generate_info()` creates information for *all* townsfolk, returning a dict with all possible townsfolk info. Example usage:
```
info = gamestate.generate_info()
poisoned_ww_info = info[characters.WASHERWOMAN]["drunk"]
true_empath_info = info[characters.EMPATH]["sober"]
```

### Player

Abstract base class in `player.py`, implementations in `text_bot_player.py` and `human_player.py`

The `Player` object tracks everything related to a single player: Their name, character, whether they're alive, and whether they've used their dead vote. It also provides an interface for the program to communicate with the player.

- `add_history()` - Sends a message to the player. This is used for game announcements, night-time info, and messages between players.
- `get_choice()` - Prompt a response from the player. This is used for player turns during the day time, nominations, and abilities that require choices during the night.

`TextBotPlayer` sends choices to an LLM, determined using the CLI argument. `HumanPlayer` uses stdin to get choices from the user. Be warned that this program will send a high volume of large-context messages to your LLM of choice, so take care not to blow through your token budget.

## Roadmap

There are a number of places this codebase could be improved! I have no immediate plans to implement these so if you want to see them, feel free to submit a PR or fork the project.

- Better context management, e.g. condensing/summarizing the oldest messages
- Support for more than 7 players
- Support specific bluffs by asking evil players what they'd like to register as, or by using an additional LLM to read evil players' chat messages and discern what they're bluffing as
- Show Washerwoman/Librarian/Investigator/Butler reminder tokens to the Spy
- More nuanced Storyteller decisions, for example what to give a poisoned Fortune Teller or who to kill if the demon targets the Mayor
- Support for scripts other than Trouble Brewing
