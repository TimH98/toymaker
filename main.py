
import shutil
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
    shutil.copy("log.txt", "log.txt.old")
    open("log.txt", "w").close()
    storyteller = Storyteller(PLAYER_NAMES)
    storyteller.first_night()
    while True:
        storyteller.day()
        storyteller.nominations()
        storyteller.other_nights()

if __name__ == "__main__":
    main()

