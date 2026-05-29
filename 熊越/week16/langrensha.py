import random
import time
from typing import List, Dict

# 角色常量
ROLE_WOLF = "wolf"
ROLE_VILLAGER = "villager"
ROLE_SEER = "seer"
ROLE_WITCH = "witch"

# ==============================
# 核心AI智能体 Agent 类
# 具备记忆、身份策略、发言、投票、博弈能力
# ==============================
class WolfAgent:
    def __init__(self, idx: int, name: str, role: str):
        self.idx = idx
        self.name = name
        self.role = role
        self.alive = True
        self.memory: List[str] = []       # 对局记忆：死亡信息、发言记录、轮次
        self.trust: Dict[int, float] = {} # 信任度：对其他玩家的好感/怀疑值
        self.witch_has_potion = True      # 女巫专属：解药是否可用
        self.checked_player = None        # 预言家专属：昨夜查验玩家

    def _record_memory(self, info: str):
        """记录对局信息到记忆库"""
        self.memory.append(info)

    def init_trust(self, total_players: int):
        """初始化对所有玩家的信任值（0~10，越高越信任）"""
        for i in range(1, total_players + 1):
            if i != self.idx:
                self.trust[i] = 5.0

    # ----------------------
    # 夜间行动 分角色逻辑
    # ----------------------
    def night_action(self, all_agents: List["WolfAgent"], wolf_team: List["WolfAgent"]):
        """夜间行动，不同角色执行不同操作"""
        if not self.alive:
            return None, None

        alive_players = [p for p in all_agents if p.alive and p.idx != self.idx]
        target = None
        poison_target = None

        if self.role == ROLE_WOLF:
            # 狼人：集体选择一名好人击杀
            target = random.choice(alive_players)
            self._record_memory(f"【黑夜】狼人团队商议，目标：{target.name}")

        elif self.role == ROLE_SEER:
            # 预言家：随机查验一名存活玩家身份
            check_p = random.choice(alive_players)
            self.checked_player = check_p
            res = "好人" if check_p.role != ROLE_WOLF else "狼人"
            self._record_memory(f"【黑夜】查验 {check_p.name}，结果：{res}")

        elif self.role == ROLE_WITCH:
            # 女巫：默认保留解药，随机选择是否使用毒药
            killed_candidate = [p for p in alive_players if p.alive]
            if killed_candidate and random.random() < 0.3:
                poison_target = random.choice(killed_candidate)
                self._record_memory(f"【黑夜】女巫选择毒杀 {poison_target.name}")

        return target, poison_target

    # ----------------------
    # 白天发言 智能博弈
    # ----------------------
    def speak(self, round_info: str) -> str:
        """根据身份、记忆、信任度生成动态发言"""
        if not self.alive:
            return f"[{self.name}] 已死亡，无法发言"

        self._record_memory(f"【白天轮次】{round_info}")
        suspect = self._get_suspect()

        if self.role == ROLE_WOLF:
            return self._wolf_speak(suspect)
        elif self.role == ROLE_SEER:
            return self._seer_speak()
        elif self.role == ROLE_WITCH:
            return self._witch_speak(suspect)
        else:
            return self._villager_speak(suspect)

    def _get_suspect(self) -> int:
        """根据信任值，选出最可疑的玩家ID"""
        alive_ids = [p.idx for p in game.players if p.alive and p.idx != self.idx]
        suspect_id = min(alive_ids, key=lambda x: self.trust[x])
        return suspect_id

    def _wolf_speak(self, suspect_id: int) -> str:
        # 狼人伪装好人，诬陷他人、踩真神
        templates = [
            f"我是纯好人，本轮我怀疑 {suspect_id} 号玩家，发言很反常。",
            f"闭眼平民视角，目前信息不多，建议大家重点关注 {suspect_id} 号。",
            f"我认好人，场上有人悍跳，我站边好人团队，出 {suspect_id} 号。",
            f"全场划水的大概率是狼，我觉得 {suspect_id} 号嫌疑最大。"
        ]
        return f"[{self.name}] {random.choice(templates)}"

    def _seer_speak(self) -> str:
        # 预言家报查验、强势带队
        if self.checked_player:
            role_txt = "好人" if self.checked_player.role != ROLE_WOLF else "狼人"
            return f"[{self.name}] 全场唯一真预言家！昨夜查验 {self.checked_player.name}，他是{role_txt}，请好人跟我投票！"
        return f"[{self.name}] 我是预言家，目前查验信息不足，大家谨慎投票。"

    def _witch_speak(self, suspect_id: int) -> str:
        # 女巫暗示身份，引导投票
        templates = [
            f"[{self.name}] 我手握关键能力，相信我的就一起出 {suspect_id} 号。",
            f"[{self.name}] 场上局势明显，{suspect_id} 号铁狼无疑，全票冲他。",
            f"[{self.name}] 好人别分票，本轮目标明确，投 {suspect_id} 号。"
        ]
        return random.choice(templates)

    def _villager_speak(self, suspect_id: int) -> str:
        # 平民跟风、分析、质疑
        templates = [
            f"[{self.name}] 闭眼玩家，听前置位发言，我觉得 {suspect_id} 号不太对劲。",
            f"[{self.name}] 没有任何信息，跟着大部分好人走，怀疑 {suspect_id} 号。",
            f"[{self.name}] 大家理性分析，我个人偏向投 {suspect_id} 号。"
        ]
        return random.choice(templates)

    # ----------------------
    # 投票逻辑 动态博弈
    # ----------------------
    def vote(self, all_agents: List["WolfAgent"]) -> "WolfAgent":
        """根据信任值投票，狼人优先投神/平民，好人优先投怀疑对象"""
        if not self.alive:
            return None

        alive_others = [p for p in all_agents if p.alive and p.idx != self.idx]
        if not alive_others:
            return None

        # 狼人：优先投神职
        if self.role == ROLE_WOLF:
            god = [p for p in alive_others if p.role in (ROLE_SEER, ROLE_WITCH)]
            if god:
                return random.choice(god)
            return random.choice(alive_others)

        # 好人阵营：投信任值最低（最可疑）的玩家
        target_id = min([p.idx for p in alive_others], key=lambda x: self.trust[x])
        return next(p for p in alive_others if p.idx == target_id)

    def update_trust(self, speaker_idx: int, is_bad: bool = False):
        """根据他人发言更新信任值"""
        if speaker_idx not in self.trust:
            return
        if is_bad:
            self.trust[speaker_idx] -= 1.5
        else:
            self.trust[speaker_idx] += 0.8
        # 限制信任值区间
        self.trust[speaker_idx] = max(0, min(10, self.trust[speaker_idx]))

# ==============================
# 游戏主控类
# ==============================
class WerewolfGame:
    def __init__(self):
        self.player_names = ["一号", "二号", "三号", "四号", "五号", "六号"]
        self.role_list = [ROLE_WOLF, ROLE_WOLF, ROLE_VILLAGER, ROLE_VILLAGER, ROLE_SEER, ROLE_WITCH]
        self.players: List[WolfAgent] = []
        self.round = 0
        self.game_over = False

    def init_game(self):
        """初始化游戏：分配身份、创建AI Agent"""
        random.shuffle(self.role_list)
        print("=" * 60)
        print("🎮 纯AI Agent 全自动狼人杀 对局开始")
        print("=" * 60)
        time.sleep(1)

        # 创建所有AI智能体
        for idx in range(6):
            agent = WolfAgent(idx + 1, self.player_names[idx], self.role_list[idx])
            self.players.append(agent)
            agent.init_trust(6)

        # 公示身份（观战用）
        print("\n📋 本局身份分配：")
        role_map = {
            ROLE_WOLF: "🐺 狼人",
            ROLE_VILLAGER: "👤 平民",
            ROLE_SEER: "🔮 预言家",
            ROLE_WITCH: "🧪 女巫"
        }
        for p in self.players:
            print(f"{p.name} → {role_map[p.role]}")
        print("-" * 60)
        time.sleep(2)

    def get_wolf_team(self) -> List[WolfAgent]:
        """获取存活狼人团队"""
        return [p for p in self.players if p.alive and p.role == ROLE_WOLF]

    def night_phase(self):
        """黑夜阶段：狼人刀人、预言家查验、女巫毒人"""
        self.round += 1
        print(f"\n🌙 【第{self.round}夜 · 黑夜行动】")
        time.sleep(1)

        wolf_team = self.get_wolf_team()
        kill_target = None
        poison_target = None

        # 全员执行夜间动作
        for agent in self.players:
            k_t, p_t = agent.night_action(self.players, wolf_team)
            if agent.role == ROLE_WOLF and k_t:
                kill_target = k_t
            if agent.role == ROLE_WITCH and p_t:
                poison_target = p_t

        # 执行击杀
        if kill_target and kill_target.alive:
            kill_target.alive = False
            print(f"💀 狼人击杀：{kill_target.name} 倒地")
        if poison_target and poison_target.alive:
            poison_target.alive = False
            print(f"☠️ 女巫毒杀：{poison_target.name} 倒地")

        alive_count = sum(1 for p in self.players if p.alive)
        print(f"📊 当前存活人数：{alive_count}")
        time.sleep(1.5)

    def day_phase(self):
        """白天阶段：全体AI轮流发言 + 更新信任值"""
        print(f"\n☀️ 【第{self.round}天 · 自由发言】")
        round_info = f"第{self.round}轮白天，场上存活玩家"

        for agent in self.players:
            talk = agent.speak(round_info)
            print(talk)
            # 其他AI根据发言更新信任
            for other in self.players:
                if other != agent and other.alive:
                    # 简单判定：狼人发言降低好人信任，好人发言提升信任
                    other.update_trust(agent.idx, is_bad=(agent.role == ROLE_WOLF))
            time.sleep(1)

    def vote_phase(self):
        """投票阶段：所有存活AI投票，处决玩家"""
        print(f"\n🗳️ 【投票放逐阶段】")
        vote_record: Dict[int, int] = {p.idx: 0 for p in self.players}

        # AI依次投票
        for agent in self.players:
            if not agent.alive:
                continue
            target = agent.vote(self.players)
            if target:
                vote_record[target.idx] += 1
                print(f"{agent.name} 投票 → {target.name}")

        # 统计票数，处决最高票玩家
        max_vote = max(vote_record.values())
        if max_vote == 0:
            print("⚖️ 本轮无人被投票，平安日")
            return

        dead_id = [k for k, v in vote_record.items() if v == max_vote][0]
        dead_agent = next(p for p in self.players if p.idx == dead_id)
        dead_agent.alive = False
        print(f"🔴 高票出局：{dead_agent.name}")
        time.sleep(1.5)

    def check_win(self):
        """胜负判定"""
        alive_wolf = [p for p in self.players if p.alive and p.role == ROLE_WOLF]
        alive_good = [p for p in self.players if p.alive and p.role != ROLE_WOLF]

        if len(alive_wolf) == 0:
            print("\n🎉 【对局结束】好人阵营全胜！狼人全部被淘汰！")
            self.game_over = True
        elif len(alive_wolf) >= len(alive_good):
            print("\n🐺 【对局结束】狼人阵营全胜！好人无力反抗！")
            self.game_over = True

    def run(self):
        """启动全自动对局"""
        self.init_game()
        while not self.game_over:
            self.night_phase()
            self.check_win()
            if self.game_over:
                break

            self.day_phase()
            self.vote_phase()
            self.check_win()

# 运行游戏
if __name__ == "__main__":
    game = WerewolfGame()
    game.run()
