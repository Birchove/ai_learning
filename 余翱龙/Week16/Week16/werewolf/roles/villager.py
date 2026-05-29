"""平民角色"""
from player_agent import PlayerAgent
from game_state import Role


class VillagerAgent(PlayerAgent):
    def __init__(self, player_id: int, name: str):
        super().__init__(player_id, name, Role.VILLAGER)

    def on_night_turn(self) -> None:
        return None

    def on_day_phase(self, is_first_day: bool) -> str:
        prompt = f"你是平民 Player {self.player_id}。当前是{'第一个' if is_first_day else '后续'}白天，\n"
        prompt += f"存活的玩家信息: {self.get_alive_players_info()}\n"
        prompt += "请以平民身份发表一段简短的发言，分析局势。"
        return self.call_llm(prompt)

    def on_vote_phase(self) -> int:
        prompt = f"你是平民 Player {self.player_id}。现在进入投票阶段。\n"
        prompt += f"存活的玩家信息: {self.get_alive_players_info()}\n"
        prompt += "请投票给最可疑的玩家（输入玩家ID）。"
        response = self.call_llm(prompt)
        return self._parse_vote_response(response)

    def _parse_vote_response(self, response: str) -> int:
        import re
        numbers = re.findall(r'\d+', response)
        for num in numbers:
            pid = int(num)
            if pid != self.player_id:
                player = self.game_state.get_player_by_id(pid)
                if player and player.alive:
                    return pid
        return self.player_id