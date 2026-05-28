# Orchestrates the game

from math import ceil
from random import choice, sample, shuffle
import re
from typing import List, Optional, Tuple
from characters import *
from gamestate import GameState
from player.human_player import HumanPlayer
from player.player import ChoiceType, Player
from player.text_bot_player import TextBotPlayer
import util

# DAY_TIMES[i] = the total number of turns for a day where i players are alive
DAY_TIMES = [0, 0, 0, 2, 2, 2, 2, 3]

def is_slayer_shot(message: str) -> Tuple[bool, str]:
    slayer_regex = r"\*I shoot \[?(\w+)\]?\*"
    match = re.match(slayer_regex, message)
    if match:
        return True, match.group(1)
    return False, None

class Storyteller:
    def __init__(self, player_names: List[str], human_player: bool = False):
        self.gamestate = GameState()
        characters, bluffs, drunk = self.select_characters()
        for i, name in enumerate(player_names):
            think = None
            if characters[i] == DRUNK:
                think = drunk
            if human_player and i == 0:
                p = HumanPlayer(name, player_names, characters[i], think)
                self.gamestate.add_player(p)
            else:
                p = TextBotPlayer(name, player_names, characters[i], think)
                self.gamestate.add_player(p)
        self.gamestate.bluffs = bluffs
        self.gamestate.reminders["red_herring"] = self.select_red_herring()

        self.died_tonight = None # Who to announce as dead in the morning
        self.has_slayer_shot = []

    def broadcast(self, message: str, to: Optional[List[Player]] = None):
        if to is None:
            for p in self.gamestate.players:
                p.add_history(message)
        else:
            for p in to:
                p.add_history(message)
    
    def select_characters(self):
        # TODO: support player counts other than 7
        demons = sample(DEMONS, k=1)
        minions = sample(MINIONS, k=1)
        # fetch 1 extra townsfolk to use as the drunk, if needed
        if BARON in minions:
            outsiders = sample(OUTSIDERS, k=2)
            townsfolk = sample(TOWNSFOLK, k=4)
        else:
            outsiders = sample(OUTSIDERS, k=0)
            townsfolk = sample(TOWNSFOLK, k=6)
        bluffs = [x for x in TOWNSFOLK + OUTSIDERS if x not in townsfolk and x not in outsiders and x != DRUNK]
        shuffle(bluffs)
        bluffs = bluffs[:3]
        drunk = townsfolk[0]
        townsfolk = townsfolk[1:]
        chars = demons + minions + outsiders + townsfolk
        shuffle(chars)
        return (
            chars,
            bluffs,
            drunk
        )
    
    def select_red_herring(self):
        good_players = [p for p in self.gamestate.players if (p.character in TOWNSFOLK or p.character in OUTSIDERS) and p.character != RECLUSE]
        return choice(good_players)
    
    def day(self):
        turn_order = sample(self.gamestate.players, k=len(self.gamestate.players))
        alive_players = len([p for p in self.gamestate.players if p.alive])
        time = 0
        self.broadcast(f"=== DAY START ===")
        if alive_players == 7:
            # first day
            self.broadcast(f"The day begins. Use this opportunity to chat with other players and share information.")
        elif self.died_tonight:
            self.broadcast(f"The day begins, and the town wakes to discover that {self.died_tonight} is dead.")
        else:
            self.broadcast(f"The day begins, and the town wakes to discover that nobody died last night.")
        
        player_states = [f"{p.name} {'(alive)' if p.alive else '(dead)'}" for p in self.gamestate.players]
        self.broadcast(f"The following players are in the game:\n{'\n'.join(player_states)}")
        
        while time < DAY_TIMES[alive_players]:
            time += 1
            for p in turn_order:
                p.add_history(f"What would you like to do? Respond with a number:")
                p.add_history(f"[1] Whisper to a player privately (recommended)")
                p.add_history(f"[2] Say something publicly")
                p.add_history(f"[3] Pass")
                choice = p.get_choice(ChoiceType.NUMBER, reminder=True)
                if choice == 1:
                    p.add_history("Choose a player.")
                    target_name = p.get_choice(ChoiceType.NAME, allowed_values=[q.name for q in turn_order if q.name != p.name])
                    p.add_history(f"What would you like to say to {target_name}?")
                    message = p.get_choice(ChoiceType.TEXT)
                    target = self.gamestate.name_to_player(target_name)
                    target.add_history(f"{p.name} whispers to you, '{message}'")
                    other_players = [q for q in turn_order if q.name != p.name and q.name != target_name]
                    self.broadcast(f"{p.name} whispers to {target_name}.", to=other_players)
                elif choice == 2:
                    p.add_history("Enter your message.")
                    message = p.get_choice(ChoiceType.TEXT)
                    townsquare_without_p = [q for q in turn_order if q.name != p.name]
                    self.broadcast(f"{p.name} says, '{message}'", to=townsquare_without_p)
                    shot, target_name = is_slayer_shot(message)
                    if shot:
                        self.slayer_turn(p, target_name)

    def nominations(self):
        nominators = []
        nominees = []
        alive_count = len([p for p in self.gamestate.players if p.alive])
        on_the_block = (None, ceil(alive_count / 2) - 1) # Tuple of (name, vote_count)

        with open("nominations.txt", "r") as f:
            self.broadcast(f.read())
        remaining_turns = [p for p in self.gamestate.players if p.alive]
        while len(remaining_turns) > 0:
            p = remaining_turns.pop(0)
            p.add_history("Would you like to nominate a player for execution? Respond with a number:")
            p.add_history("[1] Yes")
            p.add_history("[2] No")
            choice = p.get_choice(ChoiceType.NUMBER)
            if choice == 1:
                p.add_history("Choose a player to nominate. Your options are:")
                p.add_history(f"{', '.join([p.name for p in self.gamestate.players if p.name not in nominees])}")
                target_name = p.get_choice(ChoiceType.NAME)
                target = self.gamestate.name_to_player(target_name)
                if target_name not in nominees:
                    # Virgin nominated!
                    if target.character == VIRGIN and p.character in TOWNSFOLK and not self.gamestate.reminders["poisoned"] == target:
                        on_the_block = (p.name, -1)
                        remaining_turns = []
                        break

                    # Normal nomination
                    vote_count = self.run_nomination(p, target)
                    if vote_count > on_the_block[1]:
                        # Enough votes to get on the block
                        on_the_block = (target.name, vote_count)
                        self.broadcast(f"{target.name} is on the block to die with {vote_count} votes.", to=self.gamestate.players)
                    elif vote_count == on_the_block[1] and on_the_block[0] is not None:
                        # Enough votes to tie
                        self.broadcast(f"The vote is tied with {on_the_block[0]}. Nobody is on the block.")
                        on_the_block = (None, vote_count)
                    else:
                        # Not enough votes to get on the block
                        self.broadcast("The nomination doesn't receive enough votes.")

                    # Update list of nominators and nominees, and remaining turns
                    nominators.append(p.name)
                    nominees.append(target_name)
                    player_index = self.gamestate.players.index(p)
                    tmp = self.gamestate.players[player_index:] + self.gamestate.players[:player_index]
                    remaining_turns = [p for p in tmp if p.alive and p.name not in nominators]
                else:
                    p.add_history(f"{target_name} has already been nominated today.")
        
        # Execute!
        if on_the_block[0] is not None:
            self.broadcast(f"{on_the_block[0]} is executed and dies.")
            executed = self.gamestate.name_to_player(on_the_block[0])
            executed.alive = False
            if executed.character == IMP:
                scarlet_woman = self.gamestate.character_to_player(SCARLET_WOMAN)
                # TODO handle poisoned scarlet woman when 10+ player games are possible
                if scarlet_woman is not None and scarlet_woman.alive:
                    scarlet_woman.character = IMP
                    scarlet_woman.think = IMP
                    scarlet_woman.add_history(f"The imp has died. You are now the imp.")
            self.gamestate.check_win()
            self.gamestate.reminders["died_today"] = executed
        else:
            self.broadcast(f"Nobody is executed.")
    
    def run_nomination(self, accuser: Player, defendant: Player):
        other_players = [p for p in self.gamestate.players if p.name != accuser.name and p.name != defendant.name]
        self.broadcast(f"{accuser.name} nominates {defendant.name} for execution.", to=other_players)
        accuser.add_history(f"You nominate {defendant.name} for execution.")
        defendant.add_history(f"{accuser.name} nominates you for execution.")

        # rotate list of players so defendant is at the end
        player_index = self.gamestate.players.index(defendant)
        tmp = self.gamestate.players[player_index:] + self.gamestate.players[:player_index]
        voting_order = tmp[1:] + [tmp[0]]
        vote_count = 0
        for p in voting_order:
            if p.alive or p.has_ghost_vote:
                if p == defendant:
                    name = "yourself"
                else:
                    name = defendant.name
                p.add_history(f"Do you vote for {name} to die?")
                p.add_history(f"[1] Yes")
                p.add_history(f"[2] No")
                choice = p.get_choice(ChoiceType.NUMBER)
                other_players = [p2 for p2 in self.gamestate.players if p2.name != p.name]
                if choice == 1:
                    vote_count += 1
                    if not p.alive:
                        p.has_ghost_vote = False
                    self.broadcast(f"{p.name} votes YES.", to=other_players)
                else:
                    self.broadcast(f"{p.name} votes NO.", to=other_players)
        return vote_count

    def slayer_turn(self, player: Player, target_name: str):
        target = self.gamestate.name_to_player(target_name)
        self.broadcast(f"{player.name} claims to be the slayer and attempts to kill {target.name}.")
        self.has_slayer_shot.append(player)
        if target.character in DEMONS and target.alive and player.character == SLAYER and self.gamestate.reminders["poisoned"] != target:
            target.alive = False
            self.broadcast(f"{target.name} dies!")
            scarlet_woman = self.gamestate.character_to_player(SCARLET_WOMAN)
            if scarlet_woman is not None and scarlet_woman.alive:
                scarlet_woman.character = IMP
                scarlet_woman.think = IMP
                scarlet_woman.add_history(f"The imp has died. You are now the imp.")
            self.gamestate.check_win()
        else:
            self.broadcast(f"There is no effect.")


    ### NIGHT ACTIONS ###

    def first_night(self):
        self.broadcast(f"=== NIGHT START ===")
        self.info = self.gamestate.generate_info()
        self.minion_info()
        self.demon_info()
        self.poison_turn()
        self.spy_turn()
        self.washerwoman_turn()
        self.librarian_turn()
        self.investigator_turn()
        self.chef_turn()
        self.empath_turn()
        self.fortune_teller_turn()
        self.butler_turn()

    def other_nights(self):
        self.broadcast(f"=== NIGHT START ===")
        self.info = self.gamestate.generate_info()
        self.poison_turn()
        self.monk_turn()
        self.spy_turn()
        self.imp_turn()
        self.ravenkeeper_turn()
        self.undertaker_turn()
        self.empath_turn()
        self.fortune_teller_turn()
        self.butler_turn()

    def minion_info(self):
        # TODO: support multiple minions
        for p in self.gamestate.players:
            if p.character in MINIONS:
                demon = [p.name for p in self.gamestate.players if p.character in DEMONS][0]
                p.add_history(f"You learn that your demon is {demon}.")

    def demon_info(self):
        # TODO: support multiple minions
        for p in self.gamestate.players:
            if p.character in DEMONS:
                minion = [p.name for p in self.gamestate.players if p.character in MINIONS][0]
                p.add_history(f"You learn that your minion is {minion}.")
                p.add_history(f"You learn that the {self.gamestate.bluffs[0]}, {self.gamestate.bluffs[1]}, and {self.gamestate.bluffs[2]} are not in play and are safe to bluff.")
    
    def poison_turn(self):
        player = self.gamestate.character_to_player(POISONER)
        if not player or not player.alive:
            return
        player.add_history("Choose a player to poison.")
        choice = player.get_choice(ChoiceType.NAME)
        self.gamestate.reminders["poisoned"] = self.gamestate.name_to_player(choice)

    def spy_turn(self):
        # TODO: This doesn't show WW/Lib/Inv/Butler info
        player = self.gamestate.character_to_player(SPY)
        if not player or not player.alive:
            return
        player.add_history("You see the grimoire and learn the following:")
        for p in self.gamestate.players:
            char_line = f"{p.name}: {p.think}"
            if p.character == DRUNK:
                char_line += " (drunk)"
            if self.gamestate.reminders["poisoned"] == p:
                char_line += " (poisoned)"
            if self.gamestate.reminders["red_herring"] == p and self.gamestate.character_to_player(FORTUNE_TELLER):
                char_line += " (Fortune Teller's red herring)"
            if self.gamestate.reminders["protected"] == p:
                char_line += " (protected by Monk)"
            player.add_history(char_line)

    def washerwoman_turn(self):
        player = self.gamestate.character_to_player(WASHERWOMAN)
        if not player or not player.alive:
            return
        if self.gamestate.reminders["poisoned"] == player or player.character == DRUNK:
            ww_info = self.info[WASHERWOMAN]["drunk"]
        else:
            ww_info = self.info[WASHERWOMAN]["sober"]

        player.add_history(f"You learn that either {ww_info['p1']} or {ww_info['p2']} are the {ww_info['character']}.")
    
    def librarian_turn(self):
        player = self.gamestate.character_to_player(LIBRARIAN)
        if not player or not player.alive:
            return
        if self.gamestate.reminders["poisoned"] == player or player.character == DRUNK:
            lib_info = self.info[LIBRARIAN]["drunk"]
        else:
            lib_info = self.info[LIBRARIAN]["sober"]
        if lib_info['p1']:
            player.add_history(f"You learn that either {lib_info['p1']} or {lib_info['p2']} are the {lib_info['character']}.")
        else:
            player.add_history(f"You learn that there are no outsiders in play.")

    def investigator_turn(self):
        player = self.gamestate.character_to_player(INVESTIGATOR)
        if not player or not player.alive:
            return
        if self.gamestate.reminders["poisoned"] == player or player.character == DRUNK:
            inv_info = self.info[INVESTIGATOR]["drunk"]
        else:
            inv_info = self.info[INVESTIGATOR]["sober"]
        player.add_history(f"You learn that either {inv_info['p1']} or {inv_info['p2']} are the {inv_info['character']}.")

    def chef_turn(self):
        player = self.gamestate.character_to_player(CHEF)
        if not player or not player.alive:
            return
        if self.gamestate.reminders["poisoned"] == player or player.character == DRUNK:
            chef_info = self.info[CHEF]["drunk"]
        else:
            chef_info = self.info[CHEF]["sober"]
        player.add_history(f"You learn that there is {chef_info} pair of evil players sitting next to each other.")

    def empath_turn(self):
        player = self.gamestate.character_to_player(EMPATH)
        if not player or not player.alive:
            return
        if self.gamestate.reminders["poisoned"] == player or player.character == DRUNK:
            emp_info = self.info[EMPATH]["drunk"]
        else:
            emp_info = self.info[EMPATH]["sober"]
        player.add_history(f"You learn that {emp_info['number']} of your alive neighbors ({', '.join(emp_info['names'])}) are evil.")

    def fortune_teller_turn(self):
        player = self.gamestate.character_to_player(FORTUNE_TELLER)
        if not player or not player.alive:
            return
        if self.gamestate.reminders["poisoned"] == player or player.character == DRUNK:
            ft_info = self.info[FORTUNE_TELLER]["drunk"]
        else:
            ft_info = self.info[FORTUNE_TELLER]["sober"]
        player.add_history("Choose two players.")
        choices = player.get_choice(ChoiceType.TWO_NAMES)
        is_demon = ft_info[choices[0]] + ft_info[choices[1]] >= 2
        if is_demon:
            player.add_history(f"You learn that one of {choices[0]} and {choices[1]} is the demon.")
        else:
            player.add_history(f"You learn that {choices[0]} and {choices[1]} are not the demon.")

    def butler_turn(self):
        # Is it morally right to throw this choice into the void? :thonk:
        player = self.gamestate.character_to_player(BUTLER)
        if not player or not player.alive:
            return
        player.add_history("Choose a player.")
        choice = player.get_choice(ChoiceType.NAME)
        player.add_history(f"Tomorrow, you may only vote if {choice} votes.")
    
    def monk_turn(self):
        player = self.gamestate.character_to_player(MONK)
        if not player or not player.alive:
            return
        player.add_history("Choose a player to protect (not yourself).")
        choice = player.get_choice(ChoiceType.NAME, allowed_values=[p.name for p in self.gamestate.players if p != player])
        if self.gamestate.reminders["poisoned"] != player and player.character != DRUNK:
            self.gamestate.reminders["protected"] = self.gamestate.name_to_player(choice)
        
    def imp_turn(self):
        self.died_tonight = None
        player = self.gamestate.character_to_player(IMP)
        if not player or not player.alive:
            return
        player.add_history("Choose a player to kill.")
        choice = player.get_choice(ChoiceType.NAME)
        dead = self.gamestate.name_to_player(choice)
        # TODO handle poisoned imp I guess lmao
        self.gamestate.reminders["imp_dead"] = dead
        if dead.alive and not (
            self.gamestate.reminders["protected"] == dead or 
            (
                dead.character == SOLDIER and 
                self.gamestate.reminders["poisoned"] != dead
            )
        ):
            dead.alive = False
            self.died_tonight = dead.name
            self.gamestate.check_win()

    def ravenkeeper_turn(self):
        player = self.gamestate.character_to_player(RAVENKEEPER)
        if not player:
            return
        if self.gamestate.reminders["imp_dead"] != player:
            return
        if self.gamestate.reminders["poisoned"] == player or player.character == DRUNK:
            rk_info = self.info[RAVENKEEPER]["drunk"]
        else:
            rk_info = self.info[RAVENKEEPER]["sober"]
        player.add_history("You have died. Choose a player.")
        choice = player.get_choice(ChoiceType.NAME)
        player.add_history(f"You learn that {choice} is the {rk_info[choice]}.")

    def undertaker_turn(self):
        player = self.gamestate.character_to_player(UNDERTAKER)
        if not player or not player.alive:
            return
        died_today = self.gamestate.reminders["died_today"]
        if not died_today:
            return
        if self.gamestate.reminders["poisoned"] == player or player.character == DRUNK:
            ut_info = self.info[UNDERTAKER]["drunk"]
        else:
            ut_info = self.info[UNDERTAKER]["sober"]
        player.add_history(f"You learn that {died_today.name} is the {ut_info}.")
