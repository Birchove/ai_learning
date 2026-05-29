"""法官Agent - 游戏流程控制"""
from game_state import GameState, Player, Role, Phase
from message_queue import MessageBus, Message, MessageType
from roles.villager import VillagerAgent
from roles.seer import SeerAgent
from roles.witch import WitchAgent
from roles.hunter import HunterAgent
from roles.werewolf import WerewolfAgent


class JudgeAgent:
    def __init__(self):
        self.game_state = GameState()
        self.message_bus = MessageBus()
        self.player_agents: dict[int, PlayerAgent] = {}
        self.role_assignments: dict[int, Role] = {}

    def setup_game(self, player_names: list[str]):
        """初始化游戏，分配角色"""
        roles = [
            Role.SEER, Role.WITCH, Role.HUNTER, Role.VILLAGER,
            Role.WEREWOLF, Role.WEREWOLF
        ]

        for i, name in enumerate(player_names):
            player = Player(id=i, name=name, role=roles[i])
            self.game_state.players.append(player)

        self._create_agents()

    def _create_agents(self):
        """根据角色创建对应的Agent"""
        agent_classes = {
            Role.VILLAGER: VillagerAgent,
            Role.SEER: SeerAgent,
            Role.WITCH: WitchAgent,
            Role.HUNTER: HunterAgent,
            Role.WEREWOLF: WerewolfAgent,
        }

        for player in self.game_state.players:
            agent_class = agent_classes[player.role]
            agent = agent_class(player.id, player.name)
            agent.set_context(self.game_state, self.message_bus)
            self.player_agents[player.id] = agent
            self.role_assignments[player.id] = player.role

    def start_game(self):
        """开始游戏"""
        self._broadcast(f"===== 游戏开始 =====")
        self._broadcast(f"6人暗牌局：预言家、女巫、猎人、平民、狼人×2")
        self._reveal_roles()

        while True:
            winner = self.game_state.check_winner()
            if winner:
                self._broadcast(f"===== 游戏结束 =====")
                self._broadcast(f"胜利阵营: {'好人' if winner == 'good' else '狼人'}")
                break

            self._night_phase()

            winner = self.game_state.check_winner()
            if winner:
                self._broadcast(f"===== 游戏结束 =====")
                self._broadcast(f"胜利阵营: {'好人' if winner == 'good' else '狼人'}")
                break

            self._day_phase()

    def _reveal_roles(self):
        """私下通知各玩家自己的角色"""
        for player in self.game_state.players:
            msg = Message(
                msg_type=MessageType.PRIVATE,
                content=f"你的角色是: {player.role.value}",
                recipient_id=player.id,
                sender_id=0
            )
            self.message_bus.publish(msg)

    def _night_phase(self):
        """夜间阶段"""
        self.game_state.day_number += 1
        self.game_state.phase = Phase.NIGHT
        self.game_state.death_info.clear()
        self._broadcast(f"===== 第{self.game_state.day_number}夜 =====")
        self._broadcast("天黑请闭眼...")

        # 狼人刀人
        werewolf_kill = self._werewolf_kill()
        if werewolf_kill is not None:
            self._broadcast(f"狼人选择了玩家{werewolf_kill}")

        # 预言家验人
        seer_result = self._seer_check()
        if seer_result:
            self._broadcast(f"预言家查验了玩家{seer_result[0]}: {seer_result[1]}")

        # 女巫用药
        witch_action = self._witch_action()
        if witch_action:
            self._broadcast(f"女巫使用了{'救药' if witch_action == 'heal' else '毒药'}")

        # 结算死亡
        self._resolve_deaths()

    def _werewolf_kill(self) -> int | None:
        """狼人刀人环节"""
        werewolf_ids = [p.id for p in self.game_state.players
                       if p.role == Role.WEREWOLF and p.alive]

        targets = set()
        for wid in werewolf_ids:
            agent = self.player_agents[wid]
            target = agent.on_night_turn()
            if target:
                targets.add(target)

        if targets:
            killed = list(targets)[0]
            self.game_state.kill_player(killed, "被狼人杀害")
            return killed
        return None

    def _seer_check(self) -> tuple[int, str] | None:
        """预言家验人环节"""
        seer_ids = [p.id for p in self.game_state.players
                    if p.role == Role.SEER and p.alive]

        for sid in seer_ids:
            agent = self.player_agents[sid]
            target = agent.on_night_turn()
            if target:
                target_role = self.game_state.get_player_by_id(target).role
                is_werewolf = target_role == Role.WEREWOLF
                self.game_state.seer_results[sid] = (target, "狼人" if is_werewolf else "好人")
                return (target, "狼人" if is_werewolf else "好人")
        return None

    def _witch_action(self) -> str | None:
        """女巫用药环节"""
        witch_ids = [p.id for p in self.game_state.players
                     if p.role == Role.WITCH and p.alive]

        for wid in witch_ids:
            agent = self.player_agents[wid]
            action = agent.on_night_turn()
            if action:
                # 女巫agent返回的是被救治或被毒的玩家ID
                return "heal"
        return None

    def _resolve_deaths(self):
        """结算死亡"""
        deaths = []
        for info in self.game_state.death_info:
            import re
            numbers = re.findall(r'\d+', info)
            if numbers:
                pid = int(numbers[0])
                deaths.append(pid)

        hunter_deaths = []
        for pid in deaths[:]:
            player = self.game_state.get_player_by_id(pid)
            if player and player.role == Role.HUNTER and player.alive:
                agent = self.player_agents[pid]
                shot_target = agent.on_death(None)
                if shot_target:
                    hunter_deaths.append(shot_target)

        for pid in hunter_deaths:
            self.game_state.kill_player(pid, "被猎人带走")

    def _day_phase(self):
        """白天阶段"""
        self.game_state.phase = Phase.DAY
        self._broadcast(f"===== 第{self.game_state.day_number}天 =====")
        self._broadcast("天亮了...")

        if self.game_state.death_info:
            self._broadcast(f"昨夜死亡: {', '.join(self.game_state.death_info)}")
        else:
            self._broadcast("昨夜是平安夜")

        self._broadcast("各位玩家请发表遗言/发言...")

        is_first_day = self.game_state.day_number == 1
        for player in self.game_state.get_alive_players():
            agent = self.player_agents[player.id]
            speech = agent.on_day_phase(is_first_day)
            self._broadcast(f"{player.name}({player.role.value}): {speech}")

        self._vote_phase()

    def _vote_phase(self):
        """投票阶段"""
        self.game_state.phase = Phase.VOTE
        self._broadcast("===== 投票阶段 =====")

        votes = {}
        for player in self.game_state.get_alive_players():
            agent = self.player_agents[player.id]
            vote_target = agent.on_vote_phase()
            player.will_vote_for = vote_target
            votes[player.id] = vote_target
            self.game_state.vote_records.append((player.id, vote_target))

        for pid, target in votes.items():
            player = self.game_state.get_player_by_id(pid)
            target_player = self.game_state.get_player_by_id(target)
            self._broadcast(f"{player.name} 投票给了 {target_player.name}")

        # 统计票数
        vote_count: dict[int, int] = {}
        for target in votes.values():
            vote_count[target] = vote_count.get(target, 0) + 1

        max_votes = max(vote_count.values())
        candidates = [pid for pid, cnt in vote_count.items() if cnt == max_votes]

        if len(candidates) == 1:
            eliminated = candidates[0]
            eliminated_player = self.game_state.get_player_by_id(eliminated)
            self._broadcast(f"{eliminated_player.name}被投票出局")
            self.game_state.kill_player(eliminated, "被投票放逐")

            if eliminated_player.role == Role.HUNTER:
                agent = self.player_agents[eliminated]
                shot = agent.on_death(None)
                if shot:
                    self.game_state.kill_player(shot, "被猎人带走")
        else:
            self._broadcast(f"平票: {[self.game_state.get_player_by_id(pid).name for pid in candidates]}")

    def _broadcast(self, content: str):
        """广播消息"""
        try:
            print(content)
        except UnicodeEncodeError:
            print(content.encode('utf-8', errors='replace').decode('utf-8'))
        msg = Message(msg_type=MessageType.GLOBAL, content=content, sender_id=0)
        self.message_bus.publish(msg)