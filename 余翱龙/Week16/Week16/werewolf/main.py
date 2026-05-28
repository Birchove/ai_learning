"""游戏入口"""
from judge_agent import JudgeAgent


def main():
    player_names = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank"]

    judge = JudgeAgent()
    judge.setup_game(player_names)
    judge.start_game()


if __name__ == "__main__":
    main()