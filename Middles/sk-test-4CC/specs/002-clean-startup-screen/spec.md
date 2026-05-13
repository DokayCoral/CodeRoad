# Feature Specification: 终端交替屏幕隔离体验

**Feature Branch**: `002-clean-startup-screen`  
**Created**: 2026-05-12  
**Status**: Draft  
**Input**: User description: "首页不干净，我们启动时最好清空控制台的所有消息，只保留系统的信息。"
**Clarified**: 不使用 screen clearing，改用终端交替屏幕缓冲区（alternate screen buffer），达到"新窗口"的隔离体验。

## Clarifications

### Session 2026-05-12

- Q: 新窗口应该以什么方式实现？ → A: 终端交替缓冲区（alternate screen buffer），类似 vim/less/htop 的效果

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 进入独立的全屏编程界面 (Priority: P1)

作为一名开发者，当我启动 Code Clone 时，我希望平台占据整个终端形成一个"虚拟新窗口"（类似 vim 或 htop 的效果），隐藏原终端的所有历史命令和输出。当我退出系统后，终端完全恢复到启动前的样子，就像什么都没发生过。

**Why this priority**: 这是平台的第一印象和核心体验。用户希望 Code Clone 像一个独立的应用程序，启动后沉浸其中，退出后不留痕迹。alternate screen buffer 提供了这种原生终端应用的隔离感。

**Independent Test**: 在终端中执行几条命令让屏幕充满历史内容，启动 Code Clone，验证屏幕切换到一个干净的全屏界面。在系统中进行会话操作后退出，验证原终端内容完全恢复。

**Acceptance Scenarios**:

1. **Given** 终端中有历史命令和输出残留, **When** 用户启动 Code Clone 平台，**Then** 终端切换到交替屏幕缓冲区，呈现干净的全屏系统界面（欢迎信息、会话选择菜单），原终端内容被完整保留在后台
2. **Given** 平台运行在交替屏幕缓冲区中, **When** 用户进行编程会话，**Then** 所有 AI 对话和工具输出在交替屏幕中正常渲染，不混入原终端内容
3. **Given** 用户正在 Code Clone 中, **When** 用户退出系统，**Then** 交替屏幕缓冲区被释放，终端完全恢复到启动前的状态（历史命令、输出、滚动位置均不变）

---

### Edge Cases

- 平台异常崩溃时，交替屏幕缓冲区可能未被正确释放，导致终端显示异常——系统应在启动时检测并修复残留的交替屏幕状态
- 在某些不支持交替屏幕缓冲区的终端模拟器中（极少见），系统应降级为普通的清屏行为（console.clear()）并给出提示
- 用户在交替屏幕中调整终端窗口大小时，界面布局应正确响应
- 交替屏幕缓冲区不支持滚动回看历史（这是正常行为），用户应在会话内使用 `/history` 或类似命令查看对话历史

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统在启动时必须进入终端的交替屏幕缓冲区（alternate screen buffer），为用户提供干净的全屏界面
- **FR-002**: 系统在退出时必须退出交替屏幕缓冲区，完整恢复原终端内容和滚动位置
- **FR-003**: 交替屏幕缓冲区的进入和退出必须通过标准的 ANSI 转义序列实现（`\033[?1049h` 进入，`\033[?1049l` 退出）
- **FR-004**: 系统必须注册退出处理器（atexit / signal handler），确保即使在异常退出路径下也能恢复原终端屏幕
- **FR-005**: 系统在启动时应检测终端是否支持交替屏幕缓冲区，若不支持则降级使用普通清屏并警告用户

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% 的正常启动流程中，用户进入交替屏幕后看到的第一屏内容完全是系统界面
- **SC-002**: 100% 的正常退出流程中，原终端内容完整恢复（包括历史命令、输出和滚动位置）
- **SC-003**: 交替屏幕切换在 50ms 内完成，用户感知为瞬间切换
- **SC-004**: 在 Windows Terminal、Windows CMD、macOS Terminal、Linux GNOME Terminal 四款主流终端上行为一致
- **SC-005**: 异常退出（Ctrl+C、进程被杀）后，终端屏幕恢复率 ≥ 99% （通过 atexit + signal handler 保障）

## Assumptions

- 目标终端模拟器支持 ANSI 转义序列（所有现代终端都支持，包括 Windows Terminal、CMD Windows 10+）
- 平台运行在交互式终端环境中，非管道或重定向模式
- 交替屏幕缓冲区切换不影响用户的实际命令历史（bash/zsh history），仅影响屏幕显示
- rich 库的 `console.clear()` 可作为不支持 alternate screen 的降级方案
