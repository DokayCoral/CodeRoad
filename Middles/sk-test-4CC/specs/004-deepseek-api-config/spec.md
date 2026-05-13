# Feature Specification: DeepSeek API 配置与 config.txt 常量读取

**Feature Branch**: `004-deepseek-api-config`  
**Created**: 2026-05-12  
**Status**: Draft  
**Input**: User description: "第一次没有配置API_KEY就直接报错退出，用户体验不好。API_KEY还有一个问题，我们使用的是DeepSeek的代理，并没有使用Claude模型。所以我们应该按照DeepSeek的环境变量要求去设计。"
**Clarified**: 不使用环境变量优先级链和交互式配置向导，直接从项目中的 `src/config.txt` 读取所有 API 常量。修改配置就是修改 config.txt，方便调整，隔离性好。

## Clarifications

### Session 2026-05-12

- Q: API 配置应该从哪里读取？ → A: 直接读取 `src/config.txt` 文件中的 key=value 常量，不做环境变量优先级链和交互式配置向导

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 通过 config.txt 配置 API 连接 (Priority: P1)

作为一名开发者，我希望通过编辑项目中的 `src/config.txt` 文件来配置 API 连接参数（密钥、base URL、模型名称），平台启动时自动读取该文件，无需设置环境变量或通过交互式向导输入。

**Why this priority**: config.txt 方式是最简单、隔离性最好的配置方案——修改方便、一目了然、不依赖环境变量。这是用户明确要求的配置方式。

**Independent Test**: 编辑 config.txt 中的 API 常量（如修改 AUTH_TOKEN），重启平台，验证平台使用了新的配置值。

**Acceptance Scenarios**:

1. **Given** `src/config.txt` 中存在有效的 API 配置常量, **When** 平台启动，**Then** 平台自动读取并应用这些配置
2. **Given** 用户修改了 `src/config.txt` 中的模型名称, **When** 重启平台，**Then** 平台使用新的模型名称调用 API
3. **Given** config.txt 中的 TOKEN 为空或无效, **When** 平台启动，**Then** 显示清晰的提示"请在 src/config.txt 中配置有效的 AUTH_TOKEN"并退出

---

### Edge Cases

- config.txt 文件不存在时，平台应提示用户创建该文件并给出示例内容
- config.txt 编码不是 UTF-8 时，平台应给出明确错误提示
- config.txt 中某个键缺失时，使用合理的默认值并记录警告

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 平台必须从项目根目录下的 `src/config.txt` 文件中读取 API 配置常量
- **FR-002**: config.txt 格式为简单的 key=value（每行 `KEY="value"` 或 `KEY=value`）
- **FR-003**: 平台必须读取以下常量：`ANTHROPIC_BASE_URL`（API 端点地址）、`ANTHROPIC_AUTH_TOKEN`（API 密钥）、`ANTHROPIC_MODEL`（默认模型名称）
- **FR-004**: 当 config.txt 中的 `ANTHROPIC_AUTH_TOKEN` 为空或文件不存在时，平台应给出清晰提示并退出（而非抛出未捕获异常）
- **FR-005**: 平台创建 AI provider 客户端时必须使用 config.txt 中的 `ANTHROPIC_BASE_URL` 作为 base_url，`ANTHROPIC_AUTH_TOKEN` 作为 api_key
- **FR-006**: 移除之前实现的环境变量优先级链（`DEEPSEEK_API_KEY`/`ANTHROPIC_API_KEY`等）和交互式配置向导

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 修改 config.txt 后重启平台，100% 的情况下新配置立即生效
- **SC-002**: config.txt 不存在或 TOKEN 为空时，平台显示明确的配置提示并正常退出（零崩溃）

## Assumptions

- config.txt 使用 UTF-8 编码
- 格式为简单的 key=value，可能带引号
- 文件位于 `src/config.txt`，与项目代码一起管理
- 所有 DeepSeek 代理所需的常量已由用户填入 config.txt
