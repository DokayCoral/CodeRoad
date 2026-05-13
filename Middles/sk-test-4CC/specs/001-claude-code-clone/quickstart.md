# Quickstart: Claude Code 核心功能复刻平台

**Feature**: 001-claude-code-clone
**Target**: 新开发者从零搭建并运行平台

## Prerequisites

- Python 3.11+
- Claude API key (or OpenAI API key)
- Git (optional, for version control)

## Setup

```bash
# 1. Clone and enter project
cd sk-test-4CC

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
mkdir -p ~/.claude-code-clone
cat > ~/.claude-code-clone/config.yml << 'EOF'
api:
  provider: anthropic  # or openai
  key: sk-ant-xxxxx    # your API key
  model: claude-sonnet-4-6  # or gpt-4o
EOF
```

## Verify Setup

```bash
# Run tests to verify everything works
pytest tests/ -v

# Start the platform (interactive mode)
python -m src.cli.app
```

## First Session

```
$ python -m src.cli.app

Welcome to Code Clone v1.0.0

[1] New Session
[2] Continue: 001-claude-code-clone (2026-05-12 14:30)
> 1

New session started. Describe your coding task:

> 帮我读一下 src/main.py 文件的内容

AI: 正在读取 src/main.py...           # auto-execute (read tool)
[显示文件内容]

> 在文件末尾添加一个 main 函数入口

AI: 建议修改 src/main.py，在第 42 行之后添加:
    if __name__ == "__main__":
        main()
执行此编辑? [Y/n]                    # write tool requires approval
> Y

AI: 已修改 src/main.py (已自动备份为 src/main.py.bak)
```

## Key Workflows

### 1. Ask a coding question
```
> 如何用 Python 实现一个线程安全的单例模式？
```

### 2. Search the codebase
```
> 搜索所有包含 "TODO" 的 Python 文件
```

### 3. Execute a read-only shell command
```
> 查看 git 状态
```
(AI auto-executes `git status`)

### 4. Execute a write shell command
```
> 安装 pytest 依赖
```
(AI proposes `pip install pytest` → user approves → executes)

### 5. Manage tasks
```
> 帮我规划实现用户登录功能的任务
```
(AI creates task list, tracks progress)

### 6. Interrupt a long operation
Press `Ctrl+C` to interrupt AI response generation or a running command.

## Project Configuration

Create `CLAUDE.md` in your project root to customize AI behavior:

```markdown
# Project: MyProject
# Tech Stack: Python 3.11, FastAPI, PostgreSQL

## Code Style
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Prefer dataclasses over plain dicts
```

The AI loads this context automatically at session start.

## Directory Layout After Usage

```
~/.claude-code-clone/
├── config.yml              # Your API configuration
└── sessions/
    └── 2026-05-12/
        └── abc123-def456.json  # Session history
```
