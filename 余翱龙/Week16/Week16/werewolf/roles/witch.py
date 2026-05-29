"""女巫角色"""
from player_agent import PlayerAgent
from game_state import Role


class WitchAgent(PlayerAgent):
    def __init__(self, player_id: int, name: str):
        super().__init__(player_id, name, Role.WITCH)
        self.healed_last_night: int | None = None

    def on_night_turn(self) -> int | None:
        potions = self.game_state.witch_potions
        if not self.game_state.death_info:
            return None

        last_death = self.game_state.death_info[-1] if self.game_state.death_info else None
        if not last_death:
            return None

        prompt = f"你是女巫 Player {self.player_id}。夜晚来临。\n"
        prompt += f"药水量: 救药 {potions['heal']}, 毒药 {potions['poison']}\n"
        prompt += f"昨夜死讯: {last_death}\n"
        prompt += "你要采取什么行动？（1=救，2=毒，0=不行动）"
        response = self.call_llm(prompt)

        if "1" in response and potions['heal'] > 0:
            potions['heal'] -= 1
            self.healed_last_night = self._extract_player_id(last_death)
            return self.healed_last_night

        if "2" in response and potions['poison'] > 0:
            potions['poison'] -= 1
            alive = self.game_state.get_alive_players()
            for p in alive:
                if p.id != self.player_id and p.id != self.healed_last_night:
                    return p.id
        return None

    def on_day_phase(self, is_first_day: bool) -> str:
        prompt = f"你是女巫 Player {self.player_id}。当前是{'第一个' if is_first_day else '后续'}白天。\n"
        prompt += f"药水状态: 救药 {self.game_state.witch_potions['heal']}, 毒药 {self.game_state.witch_potions['poison']}\n"
        prompt += f"存活的玩家信息: {self.get_alive_players_info()}\n"
        prompt += "请以女巫身份发言，分析局势。"
        return self.call_llm(prompt)

    def on_vote_phase(self) -> int:
        prompt = f"你是女巫 Player {self.player_id}。投票阶段。\n"
        prompt += f"存活的玩家信息: {self.get_alive_players_info()}\n"
        response = self.call_llm(prompt)
        return self._parse_vote_response(response)

    def _extract_player_id(self, death_info: str) -> int | None:
        import re
        numbers = re.findall(r'\d+', death_info)
        return int(numbers[0]) if numbers else None

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