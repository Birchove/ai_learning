# 狼人杀多Agent协作系统

基于多 Agent 协作框架的狼人杀游戏系统，支持纯 AI 对战和人机混战。

## 项目结构

```
week16/
├── werewolf/                 # 后端
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置文件
│   ├── engine/              # 对局引擎
│   │   ├── game_engine.py   # 核心游戏引擎
│   │   ├── rules.py         # 游戏规则
│   │   └── phase.py         # 阶段状态机
│   ├── agents/              # Agent 实现
│   │   ├── base.py          # 基础 Agent 类
│   │   ├── factory.py       # Agent 工厂
│   │   ├── villager.py      # 村民
│   │   ├── werewolf.py      # 狼人
│   │   ├── seer.py          # 预言家
│   │   ├── witch.py         # 女巫
│   │   ├── guard.py         # 守卫
│   │   └── hunter.py        # 猎人
│   ├── memory/              # 记忆系统
│   ├── llm/                 # LLM 服务
│   │   ├── qwen_client.py   # Qwen API 客户端
│   │   └── prompts.py       # 提示词模板
│   ├── api/                 # API 层
│   │   ├── routes.py        # REST API 路由
│   │   └── ws_handler.py    # WebSocket
│   ├── models/              # 数据模型
│   └── tests/              # 测试用例 (42 个)
│
└── frontend/                # 前端
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── api/
        │   └── gameApi.js        # API 调用
        ├── hooks/
        │   └── useGameStore.js   # Zustand 状态管理
        ├── components/
        │   ├── PlayerCard.jsx    # 玩家卡片
        │   ├── GameHeader.jsx    # 游戏头部
        │   ├── ChatPanel.jsx      # 发言记录
        │   └── ActionPanel.jsx   # 行动面板
        └── pages/
            ├── GameList.jsx      # 游戏大厅
            └── GameRoom.jsx      # 游戏房间
```

## 快速开始

### 1. 安装后端依赖

```bash
cd d:/BaiduNetdiskDownload/llm/work/刘成/week16
pip install fastapi uvicorn pydantic anthropic pytest httpx
```

### 2. 安装前端依赖

```bash
cd d:/BaiduNetdiskDownload/llm/work/刘成/week16/frontend
npm install
```

### 3. 配置 API Key（可选，已配置默认Key）

API Key 在 `werewolf/config.py` 中配置。

### 4. 启动服务

```bash
# 终端1：启动后端 (端口 8000)
cd d:/BaiduNetdiskDownload/llm/work/刘成/week16
python -m werewolf.main

# 终端2：启动前端 (端口 3000)
cd d:/BaiduNetdiskDownload/llm/work/刘成/week16/frontend
npm run dev
```

访问：
- 前端：http://localhost:3000
- 后端 API 文档：http://localhost:8000/docs

## 前端功能

### 游戏大厅
- 创建游戏：自定义各角色人数
- 刷新游戏列表
- 进入已有游戏

### 游戏房间
- 玩家列表：显示所有玩家，角色颜色区分
- **AI自动对战**：一键启动全自动游戏对局
- 发言记录：实时显示历史发言
- 阶段指示：夜间/白天/投票阶段
- 自动刷新：每2秒更新游戏状态

### 角色颜色
| 角色 | 颜色 |
|------|------|
| 狼人 | 红色 |
| 预言家 | 蓝色 |
| 女巫 | 紫色 |
| 守卫 | 黄色 |
| 猎人 | 橙色 |
| 村民 | 绿色 |

## 测试用例说明

运行测试：
```bash
cd d:/BaiduNetdiskDownload/llm/work/刘成/week16
python -m pytest werewolf/tests/ -v
```

### GameRules（游戏规则测试）

| 测试用例 | 说明 |
|---------|------|
| `test_validate_player_count_valid` | 验证合法人数配置（至少6人，至少1狼人） |
| `test_validate_player_count_too_few` | 验证人数过少时被拒绝 |
| `test_validate_player_count_no_werewolf` | 验证没有狼人时被拒绝 |
| `test_check_win_condition_werewolf_wins` | 狼人胜利条件：狼人数≥好人数 |
| `test_check_win_condition_good_wins` | 游戏继续条件：狼人存活且好人数>狼人数 |
| `test_check_win_condition_all_werewolves_dead` | 好人的胜利条件：所有狼人出局 |
| `test_distribute_roles` | 角色分配：根据配置正确分配角色 |
| `test_get_default_config` | 默认配置：经典模式10人局 |

### GameEngine（游戏引擎测试）

| 测试用例 | 说明 |
|---------|------|
| `test_create_game` | 创建游戏：生成唯一 game_id |
| `test_setup_players` | 设置玩家：根据 ai_count 分配 AI 玩家 |
| `test_start_game` | 开始游戏：状态变为 running，phase 变为 night |
| `test_next_phase` | 阶段转换：night → day → vote → dead_speech |
| `test_eliminate_player` | 淘汰玩家：玩家 is_alive=false，加入 dead_players |
| `test_get_visible_state` | 信息隔离：狼人可见队友真实身份 |
| `test_check_win_condition` | 胜负判定：满足条件时返回 winner |
| `test_add_speech_and_vote` | 记录发言和投票 |
| `test_process_night_action` | 夜间行动：狼人击杀、预言家查验 |

### API 端点测试

| 测试用例 | 说明 |
|---------|------|
| `test_root_endpoint` | 根路径返回服务信息 |
| `test_health_endpoint` | 健康检查返回 status: healthy |
| `test_create_game` | POST /api/games 创建游戏，返回 game_id |
| `test_list_games` | GET /api/games 列出所有游戏 |
| `test_get_game` | GET /api/games/{game_id} 获取游戏详情 |
| `test_get_game_not_found` | 获取不存在的游戏返回 404 |
| `test_delete_game` | DELETE /api/games/{game_id} 删除游戏 |
| `test_start_game` | POST /api/games/{game_id}/start 开始游戏 |
| `test_submit_action_speak` | POST /api/games/{game_id}/action 提交发言 |
| `test_submit_action_vote` | POST /api/games/{game_id}/action 提交投票 |
| `test_get_game_state` | GET /api/games/{game_id}/state 获取玩家可见状态 |
| `test_get_game_log` | GET /api/games/{game_id}/log 获取游戏日志 |
| `test_get_speeches` | GET /api/games/{game_id}/speeches 获取发言记录 |
| `test_advance_phase` | POST /api/games/{game_id}/next_phase 推进阶段 |

## API 接口

### 创建游戏

```bash
POST /api/games
{
    "name": "自定义局",
    "player_count": {
        "werewolf": 2,
        "seer": 1,
        "witch": 1,
        "guard": 1,
        "hunter": 1,
        "villager": 4
    },
    "ai_count": 10,
    "human_count": 0
}
```

### 获取游戏状态

```bash
GET /api/games/{game_id}/state?player_id=1
```

### 提交行动

```bash
POST /api/games/{game_id}/action
{
    "player_id": 1,
    "action_type": "speak",
    "content": "我认为2号是狼人"
}
```

## 测试结果

```
42 passed in 1.30s
```

所有测试用例全部通过。