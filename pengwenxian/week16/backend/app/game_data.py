from __future__ import annotations

import json
import os
import random
import threading
import time
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Literal

import httpx
from pydantic import BaseModel, Field

Camp = Literal["werewolf", "villager", "god"]
Visibility = Literal["public", "private"]
GameStatus = Literal["pending", "running", "summarizing", "completed", "failed", "stopped"]

ROLE_TO_CAMP: dict[str, Camp] = {
    "狼人": "werewolf",
    "预言家": "god",
    "女巫": "god",
    "猎人": "god",
    "平民": "villager",
}

ROLE_LAYOUT = ["狼人", "狼人", "狼人", "预言家", "女巫", "猎人", "平民", "平民", "平民"]

ROLE_GOALS = {
    "狼人": "隐藏身份并推动狼人阵营获胜，优先击杀高价值神职，白天发言避免暴露。",
    "预言家": "通过查验建立可信信息链，并在合适时机公开关键信息帮助好人获胜。",
    "女巫": "利用解药和毒药提升好人阵营收益，避免资源浪费。",
    "猎人": "通过发言、投票和死亡时的带人能力帮助好人阵营建立优势。",
    "平民": "根据公开发言与票型推理身份，协助好人阵营淘汰狼人。",
}


class PlayerSummary(BaseModel):
    id: str
    seat: int
    name: str
    role: str
    camp: Camp
    alive: bool
    tags: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    id: str
    day: int
    phase: str
    title: str
    summary: str
    visibility: Visibility = "public"


class DecisionTrace(BaseModel):
    id: str
    day: int
    phase: str
    seat: int
    player_name: str
    role: str
    camp: Camp
    action_type: str
    thought: str
    choice: str
    target_seat: int | None = None
    public_message: str | None = None
    raw_reason: str | None = None


class GameSummary(BaseModel):
    id: str
    title: str
    description: str
    current_phase: str
    day: int
    winner: str | None
    status: GameStatus


class GameDetail(GameSummary):
    players: list[PlayerSummary]
    timeline: list[TimelineEvent]
    decision_traces: list[DecisionTrace]
    camps_status: dict[str, int]
    created_at: str
    progress_message: str
    replay_ready: bool
    error_message: str | None = None


class Attribution(BaseModel):
    winning_reason: str
    losing_reason: str
    collaboration_note: str


class ReplayReport(BaseModel):
    game_id: str
    summary: str
    key_turning_points: list[str]
    attribution: Attribution
    metrics: dict[str, float | int | str]


@dataclass
class PlayerRuntime:
    seat: int
    name: str
    role: str
    camp: Camp
    alive: bool = True
    private_notes: list[str] = field(default_factory=list)
    speech_log: list[str] = field(default_factory=list)
    has_antidote: bool = True
    has_poison: bool = True

    @property
    def player_id(self) -> str:
        return f"player_{self.seat}"

    @property
    def tags(self) -> list[str]:
        tags: list[str] = []
        if self.role in {"预言家", "女巫", "猎人"}:
            tags.append("神职")
        if self.camp == "werewolf":
            tags.append("狼人阵营")
        if self.alive:
            tags.append("存活")
        else:
            tags.append("已出局")
        return tags


@dataclass
class GameRecord:
    detail: GameDetail
    runtime_players: list[PlayerRuntime]
    replay: ReplayReport | None = None
    internal_events: list[str] = field(default_factory=list)
    stop_requested: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)


class GameStoppedError(RuntimeError):
    pass


def _load_local_env() -> None:
    env_paths = [
        Path(__file__).resolve().parents[1] / ".env",
        Path(__file__).resolve().parents[2] / ".env",
    ]
    for env_path in env_paths:
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


class QwenChatClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 90.0,
    ) -> None:
        _load_local_env()
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        self.model = model or os.getenv("QWEN_MODEL", "qwen3.6-35b-a3b")
        self.base_url = base_url or os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.timeout = timeout

    def is_ready(self) -> bool:
        return bool(self.api_key)

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("未配置千问 API Key，请设置 DASHSCOPE_API_KEY 或 QWEN_API_KEY。")

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    def chat_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.6,
        max_tokens: int = 600,
    ) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        data = self._post(payload)
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)


def _camp_count(players: list[PlayerSummary]) -> dict[str, int]:
    counts = {"werewolf": 0, "villager": 0, "god": 0}
    for player in players:
        if player.alive:
            counts[player.camp] += 1
    return counts


def _winner_label(winner: str | None) -> str | None:
    mapping = {"werewolf": "狼人", "villager": "好人", "god": "神职"}
    return mapping.get(winner)


class LiveGameObserver:
    def __init__(
        self,
        *,
        on_phase: Callable[[int, str, str], None],
        on_event: Callable[[TimelineEvent], None],
        on_decision: Callable[[DecisionTrace], None],
        on_players_changed: Callable[[], None],
        on_internal: Callable[[str], None],
        on_status: Callable[[GameStatus, str, str | None], None],
        should_stop: Callable[[], bool],
    ) -> None:
        self.on_phase = on_phase
        self.on_event = on_event
        self.on_decision = on_decision
        self.on_players_changed = on_players_changed
        self.on_internal = on_internal
        self.on_status = on_status
        self.should_stop = should_stop


class AIGameEngine:
    def __init__(self, llm_client: QwenChatClient, seed: int | None = None, step_delay: float = 0.0) -> None:
        self.llm_client = llm_client
        self.random = random.Random(seed)
        self.step_delay = step_delay

    def init_players(self) -> list[PlayerRuntime]:
        shuffled_roles = ROLE_LAYOUT[:]
        self.random.shuffle(shuffled_roles)
        players = [
            PlayerRuntime(
                seat=seat,
                name=f"{seat} 号玩家",
                role=role,
                camp=ROLE_TO_CAMP[role],
            )
            for seat, role in enumerate(shuffled_roles, start=1)
        ]
        for player in players:
            if player.camp == "werewolf":
                teammates = [str(other.seat) for other in players if other.camp == "werewolf" and other.seat != player.seat]
                player.private_notes.append(f"你的狼人队友座位号为：{', '.join(teammates)}。")
        return players

    def run_game(self, game_id: str, players: list[PlayerRuntime], observer: LiveGameObserver) -> ReplayReport:
        public_timeline: list[TimelineEvent] = []
        internal_events: list[str] = []
        day = 1
        winner: Camp | None = None

        while day <= 3 and winner is None:
            self._check_stop(observer)
            observer.on_phase(day, "night", f"第 {day} 夜开始，各角色正在做夜间决策。")
            self._pause(observer)
            night_deaths = self._run_night(day, players, observer, internal_events)
            self._pause(observer)

            self._check_stop(observer)
            observer.on_phase(day, "day_announce", f"第 {day} 天公布夜间结果。")
            if night_deaths:
                dead_text = "、".join(f"{seat} 号" for seat in sorted(night_deaths))
                event = self._make_event(day, "day_announce", f"第 {day} 天公布死亡信息", f"昨夜死亡玩家：{dead_text}。")
            else:
                event = self._make_event(day, "day_announce", f"第 {day} 天公布死亡信息", "昨夜为平安夜，没有玩家死亡。")
            public_timeline.append(event)
            observer.on_event(event)

            winner = self._check_winner(players)
            if winner:
                break

            self._check_stop(observer)
            observer.on_phase(day, "speech", f"第 {day} 天白天发言开始。")
            self._pause(observer)
            for event in self._run_speeches(day, players, observer):
                public_timeline.append(event)
                observer.on_event(event)
                self._pause(observer)

            self._check_stop(observer)
            observer.on_phase(day, "vote", f"第 {day} 天开始投票放逐。")
            vote_event, exiled_seat = self._run_vote(day, players, observer)
            public_timeline.append(vote_event)
            observer.on_event(vote_event)
            self._pause(observer)

            hunter_event = self._handle_hunter_if_needed(day, players, exiled_seat, "被放逐", observer, internal_events)
            if hunter_event:
                public_timeline.append(hunter_event)
                observer.on_event(hunter_event)

            winner = self._check_winner(players)
            day += 1

        if winner is None:
            winner = self._force_winner(players)

        observer.on_phase(day, "summarizing", "对局结束，正在生成 AI 复盘总结。")
        game_over_event = self._make_event(day, "game_over", "对局结束", f"{_winner_label(winner)}阵营获得胜利。")
        public_timeline.append(game_over_event)
        observer.on_event(game_over_event)
        observer.on_status("summarizing", "正在整理关键决策并生成赛后总结。", None)

        replay = self._build_replay(game_id, winner, players, public_timeline, internal_events)
        return replay

    def _pause(self, observer: LiveGameObserver) -> None:
        if self.step_delay <= 0:
            self._check_stop(observer)
            return
        elapsed = 0.0
        interval = 0.1
        while elapsed < self.step_delay:
            self._check_stop(observer)
            time.sleep(min(interval, self.step_delay - elapsed))
            elapsed += interval

    def _check_stop(self, observer: LiveGameObserver) -> None:
        if observer.should_stop():
            raise GameStoppedError("对局已被用户中止。")

    def _alive_players(self, players: list[PlayerRuntime]) -> list[PlayerRuntime]:
        return [player for player in players if player.alive]

    def _make_event(self, day: int, phase: str, title: str, summary: str) -> TimelineEvent:
        return TimelineEvent(id=f"event_{uuid.uuid4().hex[:10]}", day=day, phase=phase, title=title, summary=summary)

    def _make_trace(
        self,
        *,
        day: int,
        phase: str,
        player: PlayerRuntime,
        action_type: str,
        thought: str,
        choice: str,
        target_seat: int | None = None,
        public_message: str | None = None,
        raw_reason: str | None = None,
    ) -> DecisionTrace:
        return DecisionTrace(
            id=f"trace_{uuid.uuid4().hex[:10]}",
            day=day,
            phase=phase,
            seat=player.seat,
            player_name=player.name,
            role=player.role,
            camp=player.camp,
            action_type=action_type,
            thought=thought,
            choice=choice,
            target_seat=target_seat,
            public_message=public_message,
            raw_reason=raw_reason,
        )

    def _public_context(self, players: list[PlayerRuntime], day: int, phase: str, extra: str = "") -> str:
        alive = "、".join(f"{player.seat} 号" for player in self._alive_players(players))
        public_notes = extra or "暂无额外公共信息。"
        return f"当前是第 {day} 天的 {phase} 阶段。当前存活玩家：{alive}。公共信息：{public_notes}"

    def _player_context(self, player: PlayerRuntime, players: list[PlayerRuntime], day: int, phase: str, extra: str = "") -> str:
        private_notes = " ".join(player.private_notes[-8:]) if player.private_notes else "暂无私有信息。"
        return (
            f"你的身份是 {player.role}。你的目标：{ROLE_GOALS[player.role]} "
            f"{self._public_context(players, day, phase, extra)} 私有信息：{private_notes}"
        )

    def _ask_json(self, player: PlayerRuntime, players: list[PlayerRuntime], day: int, phase: str, task: str) -> dict[str, Any]:
        system_prompt = (
            "你正在参与一局 AI 狼人杀。你必须严格扮演给定身份，并仅输出合法 JSON。"
            "不要输出 Markdown，不要输出额外解释。"
        )
        user_prompt = f"{self._player_context(player, players, day, phase)} 任务要求：{task}"
        try:
            return self.llm_client.chat_json(system_prompt=system_prompt, user_prompt=user_prompt)
        except Exception as exc:
            return {"reason": f"模型调用失败，已回退默认动作：{exc}"}

    def _extract_valid_seat(self, value: Any, candidates: list[int]) -> int:
        if isinstance(value, int) and value in candidates:
            return value
        if isinstance(value, str):
            digits = "".join(ch for ch in value if ch.isdigit())
            if digits:
                seat = int(digits)
                if seat in candidates:
                    return seat
        return candidates[0]

    def _run_night(
        self,
        day: int,
        players: list[PlayerRuntime],
        observer: LiveGameObserver,
        internal_events: list[str],
    ) -> set[int]:
        alive_players = self._alive_players(players)
        wolves = [player for player in alive_players if player.camp == "werewolf"]
        non_wolf_candidates = [player.seat for player in alive_players if player.camp != "werewolf"]
        wolf_votes: list[int] = []

        for wolf in wolves:
            self._check_stop(observer)
            result = self._ask_json(
                wolf,
                players,
                day,
                "night",
                f"请从候选座位 {non_wolf_candidates} 中选择今晚击杀目标。返回 JSON："
                '{"target_seat": 数字, "reason": "一句话原因", "thought": "你的简短推理"}',
            )
            target = self._extract_valid_seat(result.get("target_seat"), non_wolf_candidates)
            reason = str(result.get("reason") or "优先处理看起来最像神职或最有带队能力的目标。")
            thought = str(result.get("thought") or f"狼队需要压缩好人信息空间，因此选择 {target} 号。")
            wolf_votes.append(target)
            observer.on_decision(
                self._make_trace(
                    day=day,
                    phase="night",
                    player=wolf,
                    action_type="击杀提名",
                    thought=thought,
                    choice=f"提名击杀 {target} 号",
                    target_seat=target,
                    raw_reason=reason,
                )
            )
            internal_events.append(f"狼人 {wolf.seat} 夜晚建议击杀 {target} 号，原因：{reason}")

        victim = max(set(wolf_votes), key=wolf_votes.count) if wolf_votes else None
        if victim is not None:
            internal_events.append(f"狼队最终决定夜间击杀 {victim} 号。")
            observer.on_internal(f"狼队夜晚合议决定击杀 {victim} 号。")

        seer = next((player for player in alive_players if player.role == "预言家"), None)
        if seer:
            self._check_stop(observer)
            candidates = [player.seat for player in alive_players if player.seat != seer.seat]
            result = self._ask_json(
                seer,
                players,
                day,
                "night",
                f'请从候选座位 {candidates} 中选择今晚查验目标。返回 JSON：{{"target_seat": 数字, "reason": "一句话原因", "thought": "简短推理"}}',
            )
            target = self._extract_valid_seat(result.get("target_seat"), candidates)
            target_player = next(player for player in players if player.seat == target)
            alignment = "狼人" if target_player.camp == "werewolf" else "好人"
            seer.private_notes.append(f"第 {day} 夜查验 {target} 号，结果为：{alignment}。")
            reason = str(result.get("reason") or "优先查验发言中最可能成为争议焦点的玩家。")
            thought = str(result.get("thought") or f"我需要尽快建立可信信息链，因此查验 {target} 号。")
            observer.on_decision(
                self._make_trace(
                    day=day,
                    phase="night",
                    player=seer,
                    action_type="查验",
                    thought=thought,
                    choice=f"查验 {target} 号，结果是 {alignment}",
                    target_seat=target,
                    raw_reason=reason,
                )
            )
            internal_events.append(f"预言家查验 {target} 号，得到结果：{alignment}。")

        witch = next((player for player in alive_players if player.role == "女巫"), None)
        saved = False
        poison_target: int | None = None
        if witch:
            self._check_stop(observer)
            candidates = [player.seat for player in alive_players if player.seat != witch.seat]
            result = self._ask_json(
                witch,
                players,
                day,
                "night",
                f"今晚狼人目标是 {victim} 号。你当前是否还有解药：{witch.has_antidote}；是否还有毒药：{witch.has_poison}。"
                f'可投毒候选为 {candidates}。返回 JSON：{{"use_antidote": true/false, "poison_target_seat": 数字或null, "reason": "一句话原因", "thought": "简短推理"}}',
            )
            reason = str(result.get("reason") or "根据当前局势谨慎决定是否使用药剂。")
            thought = str(result.get("thought") or "女巫需要兼顾局面节奏与资源收益。")
            saved = bool(result.get("use_antidote")) and witch.has_antidote and victim is not None
            if saved:
                witch.has_antidote = False
                witch.private_notes.append(f"第 {day} 夜使用了解药，救下了 {victim} 号。")
            poison_value = result.get("poison_target_seat")
            if witch.has_poison and poison_value is not None:
                poison_target = self._extract_valid_seat(poison_value, candidates)
                witch.has_poison = False
                witch.private_notes.append(f"第 {day} 夜使用毒药毒杀 {poison_target} 号。")
            choice_parts = [f"是否使用解药：{'是' if saved else '否'}"]
            if poison_target is not None:
                choice_parts.append(f"毒杀 {poison_target} 号")
            observer.on_decision(
                self._make_trace(
                    day=day,
                    phase="night",
                    player=witch,
                    action_type="用药",
                    thought=thought,
                    choice="；".join(choice_parts),
                    target_seat=poison_target,
                    raw_reason=reason,
                )
            )
            if poison_target is not None:
                internal_events.append(f"女巫在第 {day} 夜毒杀 {poison_target} 号。")

        deaths: set[int] = set()
        if victim is not None and not saved:
            deaths.add(victim)
        if poison_target is not None:
            deaths.add(poison_target)

        for seat in list(deaths):
            next(player for player in players if player.seat == seat).alive = False
        observer.on_players_changed()

        for seat in list(deaths):
            hunter_event = self._handle_hunter_if_needed(day, players, seat, "夜晚死亡", observer, internal_events)
            if hunter_event:
                observer.on_event(hunter_event)

        return deaths

    def _run_speeches(self, day: int, players: list[PlayerRuntime], observer: LiveGameObserver) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []
        for player in self._alive_players(players):
            self._check_stop(observer)
            result = self._ask_json(
                player,
                players,
                day,
                "speech",
                '请给出一段 40 到 80 字的白天发言，并返回 JSON：{"speech":"发言内容", "thought":"你的简短内心判断"}',
            )
            speech = str(result.get("speech") or f"我是 {player.seat} 号，当前更关注可疑发言和票型。")
            thought = str(result.get("thought") or "我会根据公开发言和票型继续判断。")
            player.speech_log.append(speech)
            observer.on_decision(
                self._make_trace(
                    day=day,
                    phase="speech",
                    player=player,
                    action_type="公开发言",
                    thought=thought,
                    choice="完成本轮发言",
                    public_message=speech,
                )
            )
            events.append(self._make_event(day, "speech", f"{player.seat} 号玩家发言", speech))
        return events

    def _run_vote(
        self,
        day: int,
        players: list[PlayerRuntime],
        observer: LiveGameObserver,
    ) -> tuple[TimelineEvent, int]:
        alive_players = self._alive_players(players)
        alive_seats = [player.seat for player in alive_players]
        votes: dict[int, int] = {}
        vote_lines: list[str] = []

        for player in alive_players:
            self._check_stop(observer)
            candidates = [seat for seat in alive_seats if seat != player.seat]
            result = self._ask_json(
                player,
                players,
                day,
                "vote",
                f'请从候选座位 {candidates} 中选择你今天要放逐的对象，并返回 JSON：{{"target_seat": 数字, "reason": "一句话原因", "thought": "简短推理"}}',
            )
            target = self._extract_valid_seat(result.get("target_seat"), candidates)
            reason = str(result.get("reason") or "根据当前票型和发言，优先投出最可疑目标。")
            thought = str(result.get("thought") or f"我倾向于把票投给 {target} 号。")
            votes[target] = votes.get(target, 0) + 1
            vote_lines.append(f"{player.seat} 号投给 {target} 号")
            observer.on_decision(
                self._make_trace(
                    day=day,
                    phase="vote",
                    player=player,
                    action_type="投票",
                    thought=thought,
                    choice=f"投给 {target} 号",
                    target_seat=target,
                    raw_reason=reason,
                )
            )

        exiled_seat = max(sorted(votes), key=lambda seat: votes[seat])
        next(player for player in players if player.seat == exiled_seat).alive = False
        observer.on_players_changed()
        summary = f"{'；'.join(vote_lines)}。最终 {exiled_seat} 号以最高票被放逐。"
        return self._make_event(day, "vote", f"第 {day} 天投票放逐", summary), exiled_seat

    def _handle_hunter_if_needed(
        self,
        day: int,
        players: list[PlayerRuntime],
        dead_seat: int,
        reason: str,
        observer: LiveGameObserver,
        internal_events: list[str],
    ) -> TimelineEvent | None:
        hunter = next((player for player in players if player.seat == dead_seat and player.role == "猎人"), None)
        if hunter is None:
            return None

        candidates = [player.seat for player in self._alive_players(players) if player.seat != hunter.seat]
        if not candidates:
            return None

        self._check_stop(observer)
        result = self._ask_json(
            hunter,
            players,
            day,
            "last_words",
            f'你因 {reason} 触发猎人技能，请从候选座位 {candidates} 中选择带走目标。返回 JSON：{{"target_seat": 数字, "reason": "一句话原因", "thought": "简短推理"}}',
        )
        target = self._extract_valid_seat(result.get("target_seat"), candidates)
        target_player = next(player for player in players if player.seat == target)
        target_player.alive = False
        observer.on_players_changed()
        thought = str(result.get("thought") or f"我希望在出局前换掉更可疑的 {target} 号。")
        reason_text = str(result.get("reason") or "猎人尽量带走自己最怀疑的目标。")
        observer.on_decision(
            self._make_trace(
                day=day,
                phase="last_words",
                player=hunter,
                action_type="猎人开枪",
                thought=thought,
                choice=f"带走 {target} 号",
                target_seat=target,
                raw_reason=reason_text,
            )
        )
        internal_events.append(f"猎人 {hunter.seat} 因 {reason} 带走 {target} 号。")
        return self._make_event(day, "last_words", "猎人发动技能", f"{hunter.seat} 号猎人因 {reason} 发动技能，带走了 {target} 号玩家。")

    def _check_winner(self, players: list[PlayerRuntime]) -> Camp | None:
        alive_players = self._alive_players(players)
        wolves = [player for player in alive_players if player.camp == "werewolf"]
        good = [player for player in alive_players if player.camp != "werewolf"]
        if not wolves:
            return "villager"
        if len(wolves) >= len(good):
            return "werewolf"
        return None

    def _force_winner(self, players: list[PlayerRuntime]) -> Camp:
        alive_players = self._alive_players(players)
        wolves = [player for player in alive_players if player.camp == "werewolf"]
        goods = [player for player in alive_players if player.camp != "werewolf"]
        return "werewolf" if len(wolves) >= len(goods) else "villager"

    def _build_replay(
        self,
        game_id: str,
        winner: Camp,
        players: list[PlayerRuntime],
        public_timeline: list[TimelineEvent],
        internal_events: list[str],
    ) -> ReplayReport:
        winner_text = _winner_label(winner) or winner
        timeline_text = "\n".join(f"- {event.title}：{event.summary}" for event in public_timeline)
        player_truth = "\n".join(f"- {player.seat} 号：{player.role}，阵营={player.camp}，存活={player.alive}" for player in players)
        internal_text = "\n".join(f"- {item}" for item in internal_events) or "- 无额外内部日志"

        try:
            summary_result = self.llm_client.chat_json(
                system_prompt="你是一名狼人杀复盘分析师。请根据完整对局日志生成结构化中文总结，只输出 JSON。",
                user_prompt=(
                    f"最终胜者：{winner_text}\n"
                    f"玩家真实身份：\n{player_truth}\n"
                    f"公共时间线：\n{timeline_text}\n"
                    f"内部日志：\n{internal_text}\n"
                    '请输出 JSON：{"summary":"总结","key_turning_points":["点1","点2","点3"],'
                    '"winning_reason":"胜利原因","losing_reason":"失败原因","collaboration_note":"协作观察"}'
                ),
                temperature=0.5,
                max_tokens=900,
            )
        except Exception:
            summary_result = {
                "summary": f"{winner_text}阵营取得胜利。",
                "key_turning_points": ["关键轮次票型改变了场上局势。"],
                "winning_reason": f"{winner_text}阵营在关键轮次做出了更高质量决策。",
                "losing_reason": "失败阵营在身份判断和资源使用上出现明显偏差。",
                "collaboration_note": "阵营协作质量直接影响了胜负走势。",
            }

        return ReplayReport(
            game_id=game_id,
            summary=str(summary_result.get("summary") or f"{winner_text}阵营取得胜利。"),
            key_turning_points=[str(item) for item in (summary_result.get("key_turning_points") or ["对局中形成了决定性票型优势。"])][:5],
            attribution=Attribution(
                winning_reason=str(summary_result.get("winning_reason") or f"{winner_text}阵营在关键轮次做出了更高质量决策。"),
                losing_reason=str(summary_result.get("losing_reason") or "失败阵营在身份判断和资源使用上出现明显偏差。"),
                collaboration_note=str(summary_result.get("collaboration_note") or "阵营协作质量直接影响了胜负走势。"),
            ),
            metrics={
                "round_count": max(event.day for event in public_timeline),
                "timeline_events": len(public_timeline),
                "alive_players": sum(player.alive for player in players),
                "model": self.llm_client.model,
            },
        )


class GameService:
    def __init__(
        self,
        llm_client: QwenChatClient | None = None,
        *,
        background: bool = True,
        step_delay: float = 0.6,
    ) -> None:
        self.llm_client = llm_client or QwenChatClient()
        self.background = background
        self.step_delay = step_delay
        self._games: dict[str, GameRecord] = {}
        self._counter = 0
        self._service_lock = threading.Lock()

    def list_games(self) -> list[GameSummary]:
        records = sorted(self._games.values(), key=lambda item: item.detail.created_at, reverse=True)
        return [self._to_summary(record.detail) for record in records]

    def create_ai_game(self) -> GameSummary:
        with self._service_lock:
            self._counter += 1
            game_index = self._counter
        engine = AIGameEngine(self.llm_client, step_delay=self.step_delay)
        runtime_players = engine.init_players()
        game_id = f"game_ai_{game_index:03d}"
        detail = GameDetail(
            id=game_id,
            title=f"AI 对局 {game_index:03d}",
            description=f"由千问模型驱动的 9 人标准局实时自动对战，模型为 {self.llm_client.model}。",
            current_phase="init",
            day=1,
            winner=None,
            status="running",
            players=self._player_summaries(runtime_players),
            timeline=[],
            decision_traces=[],
            camps_status=_camp_count(self._player_summaries(runtime_players)),
            created_at=datetime.now(UTC).isoformat(),
            progress_message="对局已创建，正在分配身份并准备夜间行动。",
            replay_ready=False,
        )
        record = GameRecord(detail=detail, runtime_players=runtime_players)
        self._games[game_id] = record

        if self.background:
            thread = threading.Thread(target=self._run_game, args=(game_id,), daemon=True)
            thread.start()
        else:
            self._run_game(game_id)
        return self._to_summary(detail)

    def _player_summaries(self, runtime_players: list[PlayerRuntime]) -> list[PlayerSummary]:
        return [
            PlayerSummary(
                id=player.player_id,
                seat=player.seat,
                name=player.name,
                role=player.role,
                camp=player.camp,
                alive=player.alive,
                tags=player.tags,
            )
            for player in runtime_players
        ]

    def _to_summary(self, detail: GameDetail) -> GameSummary:
        return GameSummary(
            id=detail.id,
            title=detail.title,
            description=detail.description,
            current_phase=detail.current_phase,
            day=detail.day,
            winner=detail.winner,
            status=detail.status,
        )

    def _run_game(self, game_id: str) -> None:
        record = self._games[game_id]
        engine = AIGameEngine(self.llm_client, step_delay=self.step_delay)

        def on_phase(day: int, phase: str, message: str) -> None:
            with record.lock:
                record.detail.day = day
                record.detail.current_phase = phase
                record.detail.progress_message = message

        def on_event(event: TimelineEvent) -> None:
            with record.lock:
                record.detail.timeline.append(event)
                record.detail.day = max(record.detail.day, event.day)

        def on_decision(trace: DecisionTrace) -> None:
            with record.lock:
                record.detail.decision_traces.append(trace)

        def on_players_changed() -> None:
            with record.lock:
                record.detail.players = self._player_summaries(record.runtime_players)
                record.detail.camps_status = _camp_count(record.detail.players)

        def on_internal(message: str) -> None:
            with record.lock:
                record.internal_events.append(message)

        def on_status(status: GameStatus, progress_message: str, error_message: str | None) -> None:
            with record.lock:
                record.detail.status = status
                record.detail.progress_message = progress_message
                record.detail.error_message = error_message

        observer = LiveGameObserver(
            on_phase=on_phase,
            on_event=on_event,
            on_decision=on_decision,
            on_players_changed=on_players_changed,
            on_internal=on_internal,
            on_status=on_status,
            should_stop=lambda: record.stop_requested.is_set(),
        )

        try:
            replay = engine.run_game(game_id, record.runtime_players, observer)
            with record.lock:
                winner_event = next((event for event in reversed(record.detail.timeline) if event.phase == "game_over"), None)
                record.replay = replay
                record.detail.replay_ready = True
                record.detail.status = "completed"
                record.detail.progress_message = "对局已结束，可查看完整复盘。"
                record.detail.players = self._player_summaries(record.runtime_players)
                record.detail.camps_status = _camp_count(record.detail.players)
                if winner_event and "狼人" in winner_event.summary:
                    record.detail.winner = "werewolf"
                elif winner_event and "好人" in winner_event.summary:
                    record.detail.winner = "villager"
                record.detail.current_phase = "game_over"
        except GameStoppedError:
            with record.lock:
                record.detail.status = "stopped"
                record.detail.current_phase = "game_over"
                record.detail.progress_message = "对局已由用户中止。"
                record.detail.error_message = None
                record.detail.replay_ready = False
                record.detail.winner = None
                record.detail.timeline.append(
                    TimelineEvent(
                        id=f"event_{uuid.uuid4().hex[:10]}",
                        day=record.detail.day,
                        phase="game_over",
                        title="对局已中止",
                        summary="用户主动停止了本局 AI 对战，当前结果不计入胜负。",
                    )
                )
        except Exception as exc:
            with record.lock:
                record.detail.status = "failed"
                record.detail.error_message = str(exc)
                record.detail.progress_message = "对局生成失败，请重新发起。"

    def get_game(self, game_id: str) -> GameDetail | None:
        record = self._games.get(game_id)
        if record is None:
            return None
        with record.lock:
            return deepcopy(record.detail)

    def get_replay(self, game_id: str) -> ReplayReport | None:
        record = self._games.get(game_id)
        if record is None:
            return None
        with record.lock:
            return deepcopy(record.replay)

    def stop_game(self, game_id: str) -> GameDetail | None:
        record = self._games.get(game_id)
        if record is None:
            return None
        with record.lock:
            if record.detail.status in {"completed", "failed", "stopped"}:
                return deepcopy(record.detail)
            record.stop_requested.set()
            record.detail.progress_message = "正在中止对局，等待当前角色动作安全结束。"
        return self.get_game(game_id)
