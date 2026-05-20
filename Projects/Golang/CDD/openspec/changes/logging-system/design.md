## Context

项目已有基础的测试框架（`test/mock/` 模拟乘客/司机行为，`test/monitor/` 收集运行指标），但缺少统一的日志系统。目前测试结果仅输出到控制台，无法持久化。需要设计一个模块化的日志系统，首期用于记录测试过程，后续可扩展到业务日志。

## Goals / Non-Goals

**Goals:**
- 定义统一的 Logger 接口，作为所有日志记录器的契约
- 实现控制台和文件两种输出器，通过接口可互换
- 首期实现测试日志记录器（TestLogger），记录测试方法名和 PASS/FAIL 结果
- 日志文件输出到 `logs/` 目录，按日期滚动命名
- 模块化设计：接口在 `src/pkg/log/` 定义，各模块的具体 Logger 实现与核心解耦

**Non-Goals:**
- 不实现日志采集/聚合（如 ELK）
- 不实现网络输出（如发送到远程日志服务）
- 不实现日志加密或压缩
- 不改变现有测试框架的结构，仅在其基础上增加日志记录能力

## Decisions

### 1. 接口抽象：Logger + Writer 两层

```go
// Logger: 客户端使用的接口
type Logger interface {
    Debug(format string, args ...interface{})
    Info(format string, args ...interface{})
    Warn(format string, args ...interface{})
    Error(format string, args ...interface{})
}

// Writer: 输出目标抽象
type Writer interface {
    Write(entry Entry) error
    Close() error
}
```

- `Logger` 定义四个日志级别的记录方法
- `Writer` 抽象输出目标（控制台/文件），便于扩展（后续可加网络输出）
- 通过组合将 Logger 和 Writer 解耦

**Rationale**: 两层抽象比单一 Logger 更灵活——同一个 Logger 实现可以搭配不同的 Writer，无需修改 Logger 代码。

### 2. 日志级别

| 级别 | 枚举值 | 使用场景 |
|------|--------|---------|
| DEBUG | 0 | 调试细节 |
| INFO | 1 | 一般操作（测试方法名、执行信息） |
| WARN | 2 | 警告（测试超时、匹配失败等） |
| ERROR | 3 | 错误（测试 FAIL、异常退出） |

**Rationale**: 四级足够覆盖当前需求，不引入 TRACE 或 FATAL 避免过度设计。

### 3. 日志条目结构

```go
type Entry struct {
    Level   Level     // 日志级别
    Time    time.Time // 时间戳
    Module  string    // 来源模块（如 "test", "ride"）
    Message string    // 日志内容
    Fields  map[string]interface{} // 结构化字段
}
```

- `Module` 字段标识日志来源模块，是模块化设计的关键
- `Fields` 支持结构化数据（如测试结果：`{"method": "TestPricing", "result": "PASS"}`）

**Rationale**: 结构化日志比纯文本更容易解析和查询，`Module` 字段天然支持模块扩展。

### 4. TestLogger 设计

在 `test/monitor/` 包中实现，聚合核心 Logger：

```go
type TestLogger struct {
    logger log.Logger
}
```

- `LogTestStart(method string)`: 记录测试开始（INFO 级别）
- `LogTestResult(method string, passed bool, duration time.Duration)`: 记录测试结果（PASS/FAIL + 耗时）
- 内部使用 Logger 接口，Writer 使用文件输出到 `logs/test_YYYYMMDD.log`

**Rationale**: TestLogger 是核心 Logger 的消费者，验证了模块化设计的有效性——未来添加 RideLogger、MatchLogger 时无需改动核心代码。

### 5. 文件输出策略

- 日志目录：`logs/`
- 文件命名：`test_20260521.log`（按日期分割）
- 自动创建目录和文件
- 使用 Go 标准库 `os.File` + `sync.Mutex` 保证并发安全

**Rationale**: 不使用第三方日志库（如 zap/zerolog），保持零外部依赖，与项目"从零构建"的理念一致。日期分割避免单文件过大。

### 6. 与测试框架的集成点

在 `test/monitor/metrics.go` 中引入 TestLogger，在以下时机记录：
- 测试用例开始前：`LogTestStart(testName)`
- 测试用例结束后：`LogTestResult(testName, passed, duration)`
- 系统指标报告时：`LogMetricsReport(report string)`

**Rationale**: 最小化对现有代码的改动，TestLogger 作为 Metrics 的补充而非替代。

## Risks / Trade-offs

- **文件写入性能**：高频日志写入可能影响测试性能 → 使用 `bufio.Writer` 缓冲写入，减少 IO 次数
- **日志文件无限增长**：日期分割保证按天分文件，但旧文件不会自动清理 → 后续可加保留天数配置
- **并发写入安全**：多个 goroutine 同时写日志 → `sync.Mutex` 保护 Writer

## Open Questions

<!-- All questions resolved -->
