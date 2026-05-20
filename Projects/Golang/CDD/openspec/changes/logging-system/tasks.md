## 1. 日志核心基础设施

- [x] 1.1 创建 `src/pkg/log/` 目录，定义 Level（日志级别常量：DEBUG/INFO/WARN/ERROR）和 Level 的 String() 方法
- [x] 1.2 定义 Entry 结构体（Level, Time, Module, Message, Fields）
- [x] 1.3 定义 Writer 接口（Write(Entry) error, Close() error）
- [x] 1.4 定义 Logger 接口（Debug/Info/Warn/Error 四个方法）

## 2. 日志输出器实现

- [x] 2.1 实现 ConsoleWriter：将 Entry 格式化为 `[LEVEL] [Time] [Module] Message {Fields}` 输出到 os.Stdout
- [x] 2.2 实现 FileWriter：自动创建目录，支持追加写入，使用 sync.Mutex 保证并发安全，支持 Close()

## 3. 核心 Logger 实现

- [x] 3.1 实现 DefaultLogger（实现 Logger 接口）：聚合 Writer 和 Level，实现级别过滤后调用 Writer.Write()
- [x] 3.2 提供 New(level, writer) 构造函数，支持组合不同 Writer

## 4. 测试日志记录器

- [x] 4.1 在 `test/monitor/` 下实现 TestLogger：基于 Logger 接口，提供 LogTestStart(method) 和 LogTestResult(method, passed, duration)
- [x] 4.2 实现日志文件按日期分割命名（`logs/test_YYYYMMDD.log`）

## 5. 与现有测试框架集成

- [x] 5.1 修改 `test/monitor/metrics.go`：在 RecordRequest/RecordSuccess/RecordCancelled/RecordMatchTimeout 等方法中调用 TestLogger 记录日志
- [x] 5.2 修改 `test/cmd/integration_test.go`：在每个测试场景的开始和结束时通过 TestLogger 记录日志

## 6. 日志系统单元测试

- [x] 6.1 编写 Level 和 Entry 的单元测试
- [x] 6.2 编写 ConsoleWriter 格式化输出的单元测试（捕获 stdout 验证）
- [x] 6.3 编写 FileWriter 写入/追加/并发安全的单元测试
- [x] 6.4 编写 DefaultLogger 级别过滤的单元测试
- [x] 6.5 编写 TestLogger 的单元测试：验证 LogTestStart 和 LogTestResult 产生的日志内容和级别
- [x] 6.6 编写模块化验证测试：使用 mock Writer 证明 TestLogger 不依赖具体实现（接口契约测试）
