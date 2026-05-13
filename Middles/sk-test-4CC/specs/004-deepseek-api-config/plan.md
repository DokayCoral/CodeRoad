# Implementation Plan: DeepSeek API 配置与交互式首次设置

**Branch**: `004-deepseek-api-config` | **Date**: 2026-05-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/004-deepseek-api-config/spec.md`

## Summary

两处核心改动：(1) 用交互式配置引导替换 API 密钥缺失时的崩溃；(2) 接入 DeepSeek Anthropic 兼容代理，支持 `DEEPSEEK_API_KEY`/`DEEPSEEK_BASE_URL` 环境变量和自定义 base URL。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: anthropic SDK (支持 `base_url` 参数)、pyyaml (已有)
**Storage**: `~/.claude-code-clone/config.yml` (已有，扩展字段)
**Testing**: pytest (已有) — 新增环境变量优先级测试
**Target Platform**: Cross-platform terminal
**Project Type**: CLI application (已有)
**Performance Goals**: 配置引导页 TTUI <30s
**Constraints**: 向后兼容已有的 `ANTHROPIC_API_KEY` 用户；DeepSeek 代理完全兼容 Anthropic Messages API

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simplicity First | ✅ PASS | 修改 3 个文件，无新抽象层 |
| II. Clear Contracts | ✅ N/A | 无新接口 |
| III. Test-Driven Development | ✅ PASS | 环境变量优先级链测试 |
| IV. Documentation as Code | ✅ PASS | quickstart.md 将更新为 DeepSeek 配置说明 |
| V. Continuous Validation | ✅ PASS | 独立功能，可单独验证 |

**Gate Result**: ALL PASS

## Project Structure

### Documentation

```text
specs/004-deepseek-api-config/
├── plan.md              # This file
└── spec.md              # Feature specification
```

### Source Code Changes

```text
src/config.py                     # 主要改动: env var 优先级链 + 交互式配置向导
src/services/ai_service.py        # AnthropicProvider 支持 base_url 参数
src/cli/app.py                    # main() 中调用配置检测，缺失时启动向导
```

## Implementation Steps

### Step 1: config.py — 环境变量优先级链

- 读取顺序: `DEEPSEEK_API_KEY` → `ANTHROPIC_API_KEY` → 配置文件 `api.key` → 交互式输入
- Base URL 读取: `DEEPSEEK_BASE_URL` → `ANTHROPIC_BASE_URL` → 配置文件 `api.base_url` → 默认 `https://api.deepseek.com/anthropic`
- 新增 `is_configured()` 检测函数
- 新增交互式设置函数 `interactive_setup()` 引导用户输入

### Step 2: ai_service.py — 自定义 base_url

- `AnthropicProvider.__init__` 增加 `base_url` 参数
- `create_ai_provider()` 从 config 读取 `base_url` 并传递给 Anthropic client
- 移除 OpenAI provider（用户只用 DeepSeek）或保留为备选

### Step 3: cli/app.py — 集成配置检测

- `main()` 启动时调用 `is_configured()`，未配置时调用 `interactive_setup()`
- 配置完成后再进入交替屏幕和会话选择

## Configuration Data Flow

```
环境变量             配置文件                    默认值
DEEPSEEK_API_KEY ──┐
                   ├──→ api.key ──→ ~/.claude-code-clone/config.yml
ANTHROPIC_API_KEY ─┘
                   
DEEPSEEK_BASE_URL ──┐
                    ├──→ api.base_url ──→ https://api.deepseek.com/anthropic
ANTHROPIC_BASE_URL ─┘
```

## Complexity Tracking

No violations.
