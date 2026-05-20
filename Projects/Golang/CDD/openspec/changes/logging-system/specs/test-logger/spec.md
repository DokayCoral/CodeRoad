## ADDED Requirements

### Requirement: 测试开始日志记录

系统 SHALL 提供 TestLogger，在测试开始时记录测试方法名称，日志级别为 INFO。

#### Scenario: 单个测试开始时记录日志

- **WHEN** 测试方法 `TestPricing_ShortTrip` 开始执行
- **THEN** TestLogger SHALL 记录一条 INFO 级别日志，Module 为 "test"，消息 SHALL 包含方法名和 "started" 标识

### Requirement: 测试结果日志记录

系统 SHALL 提供 TestLogger，在测试结束时记录测试方法名称、测试结果（PASS 或 FAIL）和执行耗时。

#### Scenario: 测试通过时记录 PASS

- **WHEN** 测试方法 `TestPricing_ShortTrip` 执行通过，耗时 150ms
- **THEN** TestLogger SHALL 记录一条 INFO 级别日志，Fields SHALL 包含 {"method": "TestPricing_ShortTrip", "result": "PASS", "duration_ms": 150}

#### Scenario: 测试失败时记录 FAIL

- **WHEN** 测试方法 `TestCanTransition_InvalidPaths` 执行失败，耗时 50ms
- **THEN** TestLogger SHALL 记录一条 ERROR 级别日志，Fields SHALL 包含 {"method": "TestCanTransition_InvalidPaths", "result": "FAIL", "duration_ms": 50}

### Requirement: 测试日志文件输出

系统 SHALL 将测试日志写入 `logs/` 目录下的日期分割文件，文件名格式为 `test_YYYYMMDD.log`。

#### Scenario: 测试日志写入日期文件

- **WHEN** TestLogger 在 2026-05-21 记录测试日志
- **THEN** 日志内容 SHALL 写入 `logs/test_20260521.log` 文件，每行一条 JSON 格式的日志条目

#### Scenario: 同一天内的日志追加写入

- **WHEN** 同一天内多次运行测试
- **THEN** 后续测试日志 SHALL 追加写入同一个日期文件，不清空已有内容

### Requirement: TestLogger 与核心日志接口集成

TestLogger SHALL 基于核心 Logger 接口实现，不直接依赖具体输出器或实现。

#### Scenario: TestLogger 接受任意 Logger 接口实现

- **WHEN** 创建一个 TestLogger 实例
- **THEN** 构造函数 SHALL 接受一个 Logger 接口作为参数，TestLogger 不感知底层实现
