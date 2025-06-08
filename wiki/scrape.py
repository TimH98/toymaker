from bs4 import BeautifulSoup
import requests

pages = [
        "https://wiki.bloodontheclocktower.com/Baron",
    "https://wiki.bloodontheclocktower.com/Butler",
    "https://wiki.bloodontheclocktower.com/Chef",
    "https://wiki.bloodontheclocktower.com/Drunk",
    "https://wiki.bloodontheclocktower.com/Empath",
    "https://wiki.bloodontheclocktower.com/Fortune_Teller",
    "https://wiki.bloodontheclocktower.com/Imp",
    "https://wiki.bloodontheclocktower.com/Investigator",
    "https://wiki.bloodontheclocktower.com/Librarian",
    "https://wiki.bloodontheclocktower.com/Mayor",
    "https://wiki.bloodontheclocktower.com/Monk",
    "https://wiki.bloodontheclocktower.com/Poisoner",
    "https://wiki.bloodontheclocktower.com/Ravenkeeper",
    "https://wiki.bloodontheclocktower.com/Recluse",
    "https://wiki.bloodontheclocktower.com/Saint",
    "https://wiki.bloodontheclocktower.com/Scarlet_Woman",
    "https://wiki.bloodontheclocktower.com/Slayer",
    "https://wiki.bloodontheclocktower.com/Soldier",
    "https://wiki.bloodontheclocktower.com/Spy",
    "https://wiki.bloodontheclocktower.com/Undertaker",
    "https://wiki.bloodontheclocktower.com/Virgin",
    "https://wiki.bloodontheclocktower.com/Washerwoman",
]

for page in pages[1:]:
    char_name = page.split("/")[-1].replace("_", " ").lower()
    response = requests.get(page)
    # look for a div with the classes ".small-12.large-9.large-pull-3.columns"
    soup = BeautifulSoup(response.text, "html.parser")
    columns = soup.find_all("div", class_="small-12 large-9 large-pull-3 columns")
    column = columns[0]
    output = column.text.split("How to Run")[0].strip()
    with open(f"{char_name}.txt", "w") as f:
        f.write(output)
