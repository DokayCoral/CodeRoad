## Why

项目目前没有统一的日志系统，测试框架的运行结果无法持久化记录和追溯。随着打车功能的完善和后续更多模块的加入，需要一个模块化的日志系统来记录各模块的重要行为。现在首先对测试过程实现日志记录，为后续扩展到业务日志打下基础。

## What Changes

- 新增日志核心模块：定义日志接口（Logger interface），支持日志级别（DEBUG/INFO/WARN/ERROR），支持多种输出方式（控制台、文件）
- 新增测试日志记录器：实现 Logger 接口，专门记录测试方法名称和测试结果（PASS/FAIL），输出到文件
- 日志系统与测试框架集成：测试运行过程中自动记录每条测试的方法名和结果
- 模块化设计：通过接口抽象隔离日志核心与具体实现，后续可新增其他模块的日志记录器而不修改核心代码

## Capabilities

### New Capabilities

- `log-core`: 日志核心基础设施，定义统一的 Logger 接口、日志级别枚举、日志条目结构体、输出器抽象，支持控制台和文件输出
- `test-logger`: 基于 Logger 接口的测试日志记录器，记录测试方法名、测试结果（PASS/FAIL）、执行时间戳，输出到文件

### Modified Capabilities

<!-- No existing capabilities to modify -->

## Impact

- 新增代码模块：`src/pkg/log/`（日志核心接口与实现）
- 修改测试框架：`test/monitor/` 引入日志模块，集成测试日志记录
- 新增目录：`logs/`（日志文件输出目录）
- 依赖：仅使用 Go 标准库（`log`、`os`、`io`），不引入外部依赖
