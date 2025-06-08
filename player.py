from enum import Enum, auto
import time
from typing import List, Union
from characters import DEMONS, MINIONS, OUTSIDERS, TOWNSFOLK
import util

class ChoiceType(Enum):
    TEXT = auto()
    NAME = auto()
    TWO_NAMES = auto()
    NUMBER = auto()

class DataError(Exception):
    pass

def get_alignment_message(character):
    if character in MINIONS or character in DEMONS:
        return "You are evil, and win by keeping the demon alive."
    return "You are good, and win by finding and executing the demon."

class Player:
    name = ""
    # Track all the info that will be dumped into the next user message
    new_message = ""
    character = ""
    # Same as self.character unless they are the Drunk
    think = ""
    messages = []
    player_names = []

    def add_history(self, text):
        util.log(f"{self.name:10} < {text}")
        if self.name == "Alice":
            print(text)
        self.new_message += '\n' + text

    def __init__(self, name, player_names, character, think=None):
        self.name = name
        self.character = character
        self.think = think if think else character
        self.player_names = player_names
        self.alive = True
        self.has_ghost_vote = True
        # self.claim = None # what evil players want to misregister as - will impl in v2

        self.add_history(f"Your name is {self.name}. The full list of players, seated in order, is: {', '.join(player_names)}.")
        self.add_history(f"You are the {self.think}. " + get_alignment_message(character))
        self.add_history(f"A summary of your character follows:")
        with open(f"wiki/{self.think}.txt", "r") as f:
            self.add_history(f.read())
        # self.add_history(f"As a reminder, YOUR NAME IS {self.name.upper()}.")

    def _clean_response(self, response: str, choice_type: ChoiceType) -> Union[str, List[str], int]:
        if choice_type == ChoiceType.TEXT:
            # cut down to one paragraph in case they start yapping
            return response.strip("'\"\n").split("\n")[0]
        elif choice_type == ChoiceType.NAME:
            response = response.lower()
            players = [name for name in self.player_names if name.lower() in response]
            if len(players) < 1:
                print("Bad response: ", response)
                raise DataError("Please respond with ONLY a player name.")
            return players[0]
        elif choice_type == ChoiceType.TWO_NAMES:
            response = response.lower()
            players = [name for name in self.player_names if name.lower() in response]
            if len(players) < 2:
                print("Bad response: ", response)
                raise DataError("Please respond with ONLY two player names.")
            return players[0:2]
        elif choice_type == ChoiceType.NUMBER:
            # We won't have more than 20 options at any point right?
            resp = ""
            for i in range(20):
                if str(i) in response:
                    resp = i
            return resp

    # TODO this should really exist in a subclass so I can have a separate human vs ai player
    def get_choice(self, choice_type: ChoiceType, allowed_values: List[str] = None):
        self.messages.append({
            "role": "user",
            "content": self.new_message
        })
        success = False
        wait_time = 1
        tries = 0
        errors = []
        while not success and tries < 10:
            try:
                resp = util.get_response(
                    history=self.messages,
                    name=self.name,
                )
                clean_resp = self._clean_response(resp, choice_type)
                if allowed_values and clean_resp not in allowed_values:
                    raise DataError(f"Please respond with a valid value. Valid values are: {', '.join(allowed_values)}.")
                success = True
            except util.ModelError as e:
                errors.append(e)
                time.sleep(wait_time)
                wait_time *= 2
                tries += 1
            except DataError as e:
                errors.append(e)
                tries += 1

        if not success:
            raise Exception("Failed to get a valid response from the model. Errors: " + ", ".join([str(e) for e in errors]))

        if self.name == "Alice":
            print(clean_resp)

        resp_text = str(clean_resp)
        if choice_type == ChoiceType.TWO_NAMES:
            resp_text = ", ".join(clean_resp)

        util.log(f"{self.name:10} > {resp_text}")
        self.messages.append({
            "role": "assistant",
            "content": resp_text
        })

        # Clear new message
        self.new_message = ""
        
        return clean_resp

    def reminder(self):
        good_or_evil = "You are good" if self.character in TOWNSFOLK or self.character in OUTSIDERS else "You are evil, but should try to appear good"
        self.add_history(f"[Reminder: Your name is {self.name}. You are the {self.think}. {good_or_evil}.]")
