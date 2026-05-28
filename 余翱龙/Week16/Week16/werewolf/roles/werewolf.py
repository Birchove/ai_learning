"""狼人角色"""
from player_agent import PlayerAgent
from game_state import Role


class WerewolfAgent(PlayerAgent):
    def __init__(self, player_id: int, name: str):
        super().__init__(player_id, name, Role.WEREWOLF)

    def on_night_turn(self) -> int | None:
        prompt = f"你是狼人 Player {self.player_id}。夜晚来临，请选择刀一名玩家。\n"
        prompt += f"存活的玩家信息: {self.get_alive_players_info()}\n"
        prompt += "请选择要杀害的玩家ID。"
        response = self.call_llm(prompt)
        return self._parse_kill_response(response)

    def on_day_phase(self, is_first_day: bool) -> str:
        prompt = f"你是狼人 Player {self.player_id}。当前是{'第一个' if is_first_day else '后续'}白天。\n"
        prompt += f"存活的玩家信息: {self.get_alive_players_info()}\n"
        prompt += "作为狼人，请假装好人发言，不要暴露身份。"
        return self.call_llm(prompt)

    def on_vote_phase(self) -> int:
        prompt = f"你是狼人 Player {self.player_id}。投票阶段。\n"
        prompt += f"存活的玩家信息: {self.get_alive_players_info()}\n"
        prompt += "作为狼人，请投票给好人阵营的玩家。"
        response = self.call_llm(prompt)
        return self._parse_vote_response(response)

    def _parse_kill_response(self, response: str) -> int | None:
        import re
        numbers = re.findall(r'\d+', response)
        for num in numbers:
            pid = int(num)
            if pid != self.player_id:
                player = self.game_state.get_player_by_id(pid)
                if player and player.alive:
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