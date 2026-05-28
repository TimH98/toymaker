from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Union
from characters import DEMONS, MINIONS

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

class Player(ABC):
    @abstractmethod
    def add_history(self, text):
        pass

    def __init__(self, name, player_names, character, think=None, model=None):
        self.name = name
        # Track all the info that will be dumped into the next user message
        self.new_message = ""
        self.character = character
        # Same as self.character unless they are the Drunk
        self.think = think if think else character
        self.messages = []
        self.player_names = player_names
        self.alive = True
        self.has_ghost_vote = True
        # self.claim = None # what evil players want to misregister as - TODO will implement later
        self.model = model

        self.add_history(f"Your name is {self.name}. The full list of players, seated in order, is: {', '.join(player_names)}.")
        self.add_history(f"You are the {self.think}. " + get_alignment_message(character))
        self.add_history(f"A summary of your character follows:")
        with open(f"wiki/{self.think}.txt", "r") as f:
            self.add_history(f.read())

    @abstractmethod
    def get_choice(self, choice_type: ChoiceType, allowed_values: List[str] = None, reminder: bool = False) -> Union[str, List[str], int]:
        pass

    def _clean_response(self, response: str, choice_type: ChoiceType) -> Union[str, List[str], int]:
        if choice_type == ChoiceType.TEXT:
            # cut down to one paragraph in case they start yapping
            return response.strip("'\"\n").split("\n")[0]
        elif choice_type == ChoiceType.NAME:
            response = response.lower()
            players = [name for name in self.player_names if name.lower() in response]
            if len(players) < 1:
                print("Bad response: ", response)
                raise DataError("Respond with ONLY a player name.")
            return players[0]
        elif choice_type == ChoiceType.TWO_NAMES:
            response = response.lower()
            players = [name for name in self.player_names if name.lower() in response]
            if len(players) < 2:
                print("Bad response: ", response)
                raise DataError("Respond with ONLY two player names.")
            return players[0:2]
        elif choice_type == ChoiceType.NUMBER:
            # We won't have more than 20 options at any point right?
            resp = ""
            for i in range(20):
                if str(i) in response:
                    resp = i
            return resp
