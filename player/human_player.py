

from typing import List, Union
from player.player import ChoiceType, DataError, Player
import util


class HumanPlayer(Player):
    def add_history(self, text):
        util.log(f"{self.name:10} < {text}")
        print(text)
    
    def get_choice(self, choice_type: ChoiceType, allowed_values: List[str] = None, reminder: bool = False) -> Union[str, List[str], int]:
        success = False
        while not success:
            try:
                resp = input("")
                clean_resp = self._clean_response(resp, choice_type)
                if allowed_values and clean_resp not in allowed_values:
                    raise DataError(f"Respond with a valid value. Valid values are: {', '.join(allowed_values)}.")
                success = True
            except DataError as e:
                pass
        resp_text = str(clean_resp)
        if choice_type == ChoiceType.TWO_NAMES:
            resp_text = ", ".join(clean_resp)

        util.log(f"{self.name:10} > {resp_text}")
        return clean_resp