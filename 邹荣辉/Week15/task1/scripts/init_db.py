"""初始化 SQLite：建表（幂等）。

用法：
    python scripts/init_db.py

读取 SQLITE_PATH 环境变量，缺省 ./data/app.db。
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine

from libs.common.db.models import Base


def main() -> None:
    sqlite_path = os.environ.get("SQLITE_PATH", "./data/app.db")
    Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(f"sqlite:///{sqlite_path}")
    Base.metadata.create_all(engine)

    print(f"[init_db] tables created at {sqlite_path}")


if __name__ == "__main__":
    main()
