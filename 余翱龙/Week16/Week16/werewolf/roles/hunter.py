"""猎人角色"""
from player_agent import PlayerAgent
from game_state import Role


class HunterAgent(PlayerAgent):
    def __init__(self, player_id: int, name: str):
        super().__init__(player_id, name, Role.HUNTER)
        self.can_shoot: bool = True

    def on_night_turn(self) -> int | None:
        return None

    def on_day_phase(self, is_first_day: bool) -> str:
        prompt = f"你是猎人 Player {self.player_id}。当前是{'第一个' if is_first_day else '后续'}白天。\n"
        prompt += f"存活的玩家信息: {self.get_alive_players_info()}\n"
        prompt += "作为猎人，请分析局势并发言。"
        return self.call_llm(prompt)

    def on_vote_phase(self) -> int:
        prompt = f"你是猎人 Player {self.player_id}。投票阶段。\n"
        prompt += f"存活的玩家信息: {self.get_alive_players_info()}\n"
        prompt += "请投票给最可疑的玩家。"
        response = self.call_llm(prompt)
        return self._parse_vote_response(response)

    def on_death(self, killer_id: int | None) -> int | None:
        if not self.can_shoot:
            return None
        prompt = f"你是猎人 Player {self.player_id}。你死亡了！\n"
        prompt += f"杀你的人: {killer_id}\n"
        prompt += f"存活的玩家: {self.get_alive_players_info()}\n"
        prompt += "你要开枪带走一名玩家吗？（输入玩家ID或0表示不开枪）"
        response = self.call_llm(prompt)
        return self._parse_shoot_response(response)

    def _parse_shoot_response(self, response: str) -> int | None:
        import re
        numbers = re.findall(r'\d+', response)
        for num in numbers:
            pid = int(num)
            if pid != self.player_id and pid != 0:
                player = self.game_state.get_player_by_id(pid)
                if player and player.alive:
                    self.can_shoot = False
                    return pid
        return None

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