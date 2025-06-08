from typing import List
from player import Player
from random import choice, random, sample
from characters import *
import util


class GameState:
    def __init__(self):
        self.players: List[Player] = []
        self.reminders = { # these are Player objects
            "red_herring": None,
            "died_today": None,
            "poisoned": None,
            "protected": None,
            "imp_dead": None
        }
        self.bluffs = []
    
    def add_player(self, player: Player):
        self.players.append(player)
    
    def name_to_player(self, name: str, debug=False):
        names = [p for p in self.players if p.name.lower() == name.lower()]
        if len(names) == 0:
            # if debug:
            #     util.log(f"DEBUG: {name} not found in {[p.name for p in self.players]}")
            return None
        return names[0]

    def character_to_player(self, character: str):
        characters = [p for p in self.players if p.think == character]
        if len(characters) == 0:
            return None
        return characters[0]
    
    def check_win(self):
        # TODO handle mayor
        imps = [p for p in self.players if p.character == IMP and p.alive]
        mayor = self.character_to_player(MAYOR)
        if len(imps) == 0:
            print("Good wins!")
            exit()
        elif len([p for p in self.players if p.alive]) <= 2:
            print("Evil wins!")
            exit()
        elif len([p for p in self.players if p.alive]) == 3 and mayor is not None and mayor.character == MAYOR and self.reminders["poisoned"] != mayor:
            print("Good wins!")
            exit()
    
    def generate_info(self):
        # return a map from character name to that character's info
        return {
            WASHERWOMAN: self.generate_washerwoman_info(),
            LIBRARIAN: self.generate_librarian_info(),
            INVESTIGATOR: self.generate_investigator_info(),
            CHEF: self.generate_chef_info(),
            EMPATH: self.generate_empath_info(),
            FORTUNE_TELLER: self.generate_fortune_teller_info(),
            UNDERTAKER: self.generate_undertaker_info(),
            RAVENKEEPER: self.generate_ravenkeeper_info()
        }
        
    def generate_washerwoman_info(self):
        valid_townsfolk = [p for p in self.players if (util.registers_as_townsfolk(p.character)) and p.character != WASHERWOMAN]
        non_ww_players = [p for p in self.players if p.think != WASHERWOMAN]
        townsfolk_bluffs = [b for b in self.bluffs if b in TOWNSFOLK]
        p1 = choice(valid_townsfolk)
        p2 = choice(non_ww_players)
        while p1 == p2:
            p2 = choice(non_ww_players)
        
        char = p1.character
        if char == SPY:
            char = choice(TOWNSFOLK)
            if len(townsfolk_bluffs) > 0:
                char = choice(townsfolk_bluffs)
    
        # if drunk, two random players
        dp1 = choice(non_ww_players)
        dp2 = choice(non_ww_players)
        while dp1 == dp2:
            dp2 = choice(non_ww_players)
        
        # lean towards picking evils for drunk info
        if not (dp1.character in DEMONS or dp1.character in MINIONS or dp2.character in DEMONS or dp2.character in MINIONS):
            dp1 = choice(non_ww_players)
            dp2 = choice(non_ww_players)
            while dp1 == dp2:
                dp2 = choice(non_ww_players)
        
        dc = choice(TOWNSFOLK)
        # if evil is in drunk info, make the character a bluff
        if dp1.character in DEMONS or dp1.character in MINIONS or dp2.character in DEMONS or dp2.character in MINIONS:
            townsfolk_bluffs = [b for b in self.bluffs if util.registers_as_townsfolk(b)]
            if len(townsfolk_bluffs) > 0:
                dc = choice(townsfolk_bluffs)

        flip = random() < 0.5
        return {
            "sober": {
                "p1": p1.name if flip else p2.name,
                "p2": p2.name if flip else p1.name,
                "character": p1.character
            },
            "drunk": {
                "p1": dp1.name,
                "p2": dp2.name,
                "character": dc
            }
        }
        
    def generate_librarian_info(self):
        valid_outsiders = [p for p in self.players if (util.registers_as_outsider(p.character))]
        non_lib_players = [p for p in self.players if p.think != LIBRARIAN]
        outsider_bluffs = [b for b in self.bluffs if b in OUTSIDERS]
        sober = {
            "p1": None,
            "p2": None,
            "character": None
        }
        if len(valid_outsiders) > 0:
            p1 = choice(valid_outsiders)
            p2 = choice(non_lib_players)
            while p1 == p2 or p2.character == LIBRARIAN:
                p2 = choice(non_lib_players)
            char = p1.character
            if char == SPY:
                char = choice(OUTSIDERS)
                if len(outsider_bluffs) > 0:
                    char = choice(outsider_bluffs)
            flip = random() < 0.5
            sober = {
                "p1": p1.name if flip else p2.name,
                "p2": p2.name if flip else p1.name,
                "character": char
            }

        # if drunk, two random players
        dp1 = choice(non_lib_players)
        dp2 = choice(non_lib_players)
        while dp1 == dp2:
            dp2 = choice(non_lib_players)
        
        # lean towards picking evils for drunk info
        if not (dp1.character in DEMONS or dp1.character in MINIONS or dp2.character in DEMONS or dp2.character in MINIONS):
            dp1 = choice(non_lib_players)
            dp2 = choice(non_lib_players)
            while dp1 == dp2:
                dp2 = choice(non_lib_players)
        
        dc = choice(OUTSIDERS)
        # if evil is in drunk info, make the character a bluff
        if dp1.character in DEMONS or dp1.character in MINIONS or dp2.character in DEMONS or dp2.character in MINIONS:
            if len(outsider_bluffs) > 0:
                dc = choice(outsider_bluffs)

        return {
            "sober": sober,
            "drunk": {
                "p1": dp1.name,
                "p2": dp2.name,
                "character": dc
            }
        }
        
    def generate_investigator_info(self):
        valid_minions = [p for p in self.players if (util.registers_as_minion(p.character))]
        non_inv_players = [p for p in self.players if p.think != INVESTIGATOR]

        if not valid_minions:
            # Happens when minion becomes demon, doesn't matter after n1
            return None

        p1 = choice(valid_minions)
        p2 = choice(non_inv_players)
        while p1 == p2:
            p2 = choice(non_inv_players)
        
        char = p1.character
        if char == RECLUSE:
            char = choice(MINIONS)

        # if drunk, always see two good players
        # TODO: maybe rarely see an evil incorrectly?
        good_players = [p for p in non_inv_players if p.character not in DEMONS and p.character not in MINIONS]
        dp1, dp2 = sample(good_players, k=2)

        flip = random() < 0.5
        return {
            "sober": {
                "p1": p1.name if flip else p2.name,
                "p2": p2.name if flip else p1.name,
                "character": char
            },
            "drunk": {
                "p1": dp1.name,
                "p2": dp2.name,
                "character": choice(MINIONS)
            }
        }
    
    def generate_chef_info(self):
        pairs = 0
        for i, p in enumerate(self.players):
            p2 = self.players[(i+1) % len(self.players)]
            # TODO: should this sometimes include recluse?
            if (p.character in DEMONS or p.character in MINIONS) and (p2.character in DEMONS or p2.character in MINIONS):
                pairs += 1
        
        return {
            "sober": pairs,
            "drunk": 0 if pairs > 0 else 1
        }
        
    def generate_empath_info(self):
        alive_players = [p for p in self.players if p.alive]
        for i, p in enumerate(alive_players):
            if p.think == EMPATH:
                left = alive_players[i-1]
                right = alive_players[(i+1) % len(alive_players)]
                left_evil = 1 if util.registers_as_minion(left.character) or util.registers_as_demon(left.character) else 0
                right_evil = 1 if util.registers_as_minion(right.character) or util.registers_as_demon(right.character) else 0
                drunk = 0 if left_evil + right_evil > 0 else 1
                if drunk == 1 and random() < 0.05:
                    drunk = 2
                return {
                    "sober": {
                        "number": left_evil + right_evil,
                        "names": [left.name, right.name]
                    },
                    "drunk": {
                        "number": drunk,
                        "names": [left.name, right.name]
                    }
                }
        return None
    
    def generate_fortune_teller_info(self):
        # create a map from player to a number 0-2. If a fortune teller picks two players who add
        # to 2 or more, they get a Yes
        sober = {}
        drunk = {}
        # TODO: this could be infinitely more complex, e.g. scarlet woman depends on early vs late game
        for p in self.players:
            if p.character in DEMONS:
                sober[p.name] = 2
                drunk[p.name] = 0
            elif p.character == RECLUSE or self.reminders["red_herring"] == p:
                sober[p.name] = 2
                drunk[p.name] = 1
            elif p.character == SCARLET_WOMAN:
                sober[p.name] = 0
                drunk[p.name] = 0
            else:
                sober[p.name] = 0
                drunk[p.name] = 1
        return {
            "sober": sober,
            "drunk": drunk
        }
    
    def generate_undertaker_info(self):
        # TODO: support specific bluffs
        died_today: Player = self.reminders["died_today"]
        sober = None
        drunk = None
        if died_today is not None:
            sober = died_today.character
            if died_today.character in DEMONS or died_today.character in MINIONS:
                if died_today.character == SPY and random() < 0.5:
                    sober = choice(self.bluffs)
                drunk = choice(self.bluffs)
            else:
                if died_today.character == RECLUSE and random() < 0.5:
                    sober = choice(MINIONS + DEMONS)
                drunk = choice(MINIONS + DEMONS)
        return {
            "sober": sober,
            "drunk": drunk
        }
    
    def generate_ravenkeeper_info(self):
        # create a map from player name to the character the ravenkeeper would see
        # TODO: support specific bluffs
        sober = {}
        drunk = {}
        for p in self.players:
            if p.character == SPY and random() < 0.5:
                reg = choice(self.bluffs)
                sober[p.name] = reg
                drunk[p.name] = reg
            elif p.character == RECLUSE and random() < 0.5:
                reg = choice(MINIONS + DEMONS)
                sober[p.name] = reg
                drunk[p.name] = reg
            else:
                sober[p.name] = p.character
                if p.character in DEMONS or p.character in MINIONS:
                    drunk[p.name] = choice(self.bluffs)
                else:
                    drunk[p.name] = choice(MINIONS + DEMONS)
        return {
            "sober": sober,
            "drunk": drunk
        }