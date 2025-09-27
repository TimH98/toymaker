from abc import ABC, abstractmethod
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

class Player(ABC):
    @abstractmethod
    def add_history(self, text):
        pass

    def __init__(self, name, player_names, character, think=None):
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

        self.add_history(f"Your name is {self.name}. The full list of players, seated in order, is: {', '.join(player_names)}.")
        self.add_history(f"You are the {self.think}. " + get_alignment_message(character))
        self.add_history(f"A summary of your character follows:")
        with open(f"wiki/{self.think}.txt", "r") as f:
            self.add_history(f.read())

    @abstractmethod
    def get_choice(self, choice_type: ChoiceType, allowed_values: List[str] = None, reminder: bool = False) -> Union[str, List[str], int]:
        pass
