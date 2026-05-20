## ADDED Requirements

### Requirement: Logger 接口定义

系统 SHALL 定义一个统一的 Logger 接口，包含 Debug、Info、Warn、Error 四个日志级别方法，所有模块通过此接口记录日志。

#### Scenario: 各模块通过 Logger 接口记录不同级别日志

- **WHEN** 调用方持有 Logger 接口实例
- **THEN** 调用方 SHALL 可调用 Debug/Info/Warn/Error 任一方法，传入格式化字符串和参数记录日志

### Requirement: Writer 接口定义

系统 SHALL 定义一个 Writer 接口，抽象日志的输出目标。Writer 接收 Entry 并写入目标，支持 Close 方法释放资源。

#### Scenario: 不同输出目标实现相同 Writer 接口

- **WHEN** 控制台输出或文件输出都需要写入日志
- **THEN** 两者 SHALL 实现相同的 Writer 接口，Logger 不感知具体输出目标

### Requirement: 日志条目结构

系统 SHALL 使用结构化的 Entry 作为日志记录的最小单元，包含日志级别、时间戳、来源模块、消息内容和可选的结构化字段。

#### Scenario: 创建一条结构化日志条目

- **WHEN** 记录一条 INFO 级别日志，来源为 "test"，消息为 "test completed"，附带字段 {"result": "PASS", "duration_ms": 150}
- **THEN** 生成的 Entry 对象 SHALL 包含所有上述信息，时间戳为当前时间

### Requirement: 日志级别过滤

系统 SHALL 支持按日志级别过滤，低于配置级别的日志不输出。

#### Scenario: INFO 级别过滤掉 DEBUG 日志

- **WHEN** 日志系统配置最低输出级别为 INFO
- **THEN** 调用 Logger.Debug() 时，该条日志 SHALL 不写入任何输出目标

#### Scenario: ERROR 级别显示所有重要日志

- **WHEN** 日志系统配置最低输出级别为 ERROR
- **THEN** 调用 Logger.Info() 或 Logger.Warn() 时，这些日志 SHALL 不写入任何输出目标

### Requirement: 控制台输出器

系统 SHALL 提供一个控制台输出器（ConsoleWriter），将日志格式化后输出到标准输出。

#### Scenario: 控制台输出包含级别、模块和消息

- **WHEN** 使用 ConsoleWriter 输出一条 INFO 级别来自 "test" 模块的日志
- **THEN** 标准输出 SHALL 包含 "[INFO]"、"[test]" 和时间戳

### Requirement: 文件输出器

系统 SHALL 提供一个文件输出器（FileWriter），将日志写入指定文件，自动创建目录，支持并发安全写入。

#### Scenario: 文件输出器自动创建日志目录

- **WHEN** 指定日志文件路径为 `logs/test_20260521.log`，但 `logs/` 目录不存在
- **THEN** FileWriter SHALL 自动创建 `logs/` 目录并写入日志

#### Scenario: 并发写入文件安全

- **WHEN** 多个 goroutine 同时通过同一个 FileWriter 写入日志
- **THEN** 所有日志条目 SHALL 完整写入文件，不出现交错或丢失
