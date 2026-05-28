import datetime
from characters import RECLUSE, SPY, TOWNSFOLK, OUTSIDERS, MINIONS, DEMONS


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

