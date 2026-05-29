"""Game phase management."""

from werewolf.config import Phase


class PhaseManager:
    """Manages game phase transitions."""

    # Phase order for each day
    DAY_PHASES = [Phase.DAY, Phase.VOTE, Phase.DEAD_SPEECH]

    def __init__(self):
        self.current_phase: str = Phase.WAITING
        self.current_day: int = 0
        self.is_night: bool = False

    def start_game(self):
        """Initialize phases for game start."""
        self.current_phase = Phase.NIGHT
        self.current_day = 1
        self.is_night = True

    def next_phase(self) -> tuple[int, str]:
        """Move to the next phase."""
        if self.current_phase == Phase.WAITING:
            self.current_phase = Phase.NIGHT
            self.current_day = 1
            self.is_night = True
        elif self.current_phase == Phase.NIGHT:
            # Night ends, start day
            self.current_phase = Phase.DAY
            self.is_night = False
        elif self.current_phase == Phase.DAY:
            self.current_phase = Phase.VOTE
        elif self.current_phase == Phase.VOTE:
            self.current_phase = Phase.DEAD_SPEECH
        elif self.current_phase == Phase.DEAD_SPEECH:
            # Dead speech ends, start new night
            self.current_phase = Phase.NIGHT
            self.current_day += 1
            self.is_night = True
        return self.current_day, self.current_phase

    def get_next_night_action_order(self) -> list[str]:
        """Get the order of night actions for werewolves."""
        return ["werewolf", "seer", "witch", "guard"]

    def is_voting_phase(self) -> bool:
        """Check if current phase is voting phase."""
        return self.current_phase == Phase.VOTE

    def is_night_phase(self) -> bool:
        """Check if current phase is night phase."""
        return self.current_phase == Phase.NIGHT

    def is_day_phase(self) -> bool:
        """Check if current phase is day phase."""
        return self.current_phase == Phase.DAY

    def __repr__(self):
        return f"PhaseManager(day={self.current_day}, phase={self.current_phase}, is_night={self.is_night})"