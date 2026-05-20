## 1. 项目初始化与基础设施

- [x] 1.1 创建项目目录结构（`src/cmd`, `src/internal/handler`, `src/internal/service`, `src/internal/repo`, `src/internal/model`, `src/internal/config`, `src/pkg`, `test/mock`, `test/monitor`）
- [x] 1.2 初始化 Go module 并安装核心依赖（Gin, GORM, MySQL driver, Redis client, RabbitMQ client）
- [x] 1.3 创建配置模块 `src/internal/config`，支持从文件/环境变量读取数据库、Redis、RabbitMQ 连接参数及计费参数
- [x] 1.4 创建 main 入口 `src/cmd/main.go`，初始化 Gin 路由、数据库连接、Redis 连接、RabbitMQ 连接

## 2. 数据模型与数据库

- [x] 2.1 定义数据模型 `src/internal/model`：`Ride`（行程）、`Driver`（司机），使用 GORM tag
- [x] 2.2 编写数据库迁移（AutoMigrate）创建 `rides` 和 `drivers` 表
- [x] 2.3 定义行程状态常量（Pending/Matched/Accepted/Arrived/Started/Completed/Cancelled）和司机状态常量（Online/Offline/Busy）

## 3. 数据访问层

- [x] 3.1 实现 `src/internal/repo/ride_repo.go`：CreateRide、GetRideByID、UpdateRideStatus、GetActiveRideByPassenger
- [x] 3.2 实现 `src/internal/repo/driver_repo.go`：UpdateDriverStatus、UpdateDriverLocation、GetDriverByID
- [x] 3.3 实现 `src/internal/repo/driver_location.go`（Redis GEO）：AddDriverLocation、RemoveDriverLocation、SearchNearbyDrivers

## 4. 核心业务服务

- [x] 4.1 实现行程请求服务 `src/internal/service/ride_service.go`：HandleRideRequest（校验乘客无进行中行程 → 计算预估费用 → 创建 Pending 行程 → 发布匹配消息到 RabbitMQ）
- [x] 4.2 实现司机匹配服务 `src/internal/service/matching_service.go`：消费 `ride.request` 队列 → 查询 Redis GEO 附近司机 → 选择最近司机 → 更新行程为 Matched → 发布 `ride.event`
- [x] 4.3 实现行程生命周期服务 `src/internal/service/lifecycle_service.go`：Accept/Arrive/Start/Complete/Cancel 各操作，含状态机校验和事件发布
- [x] 4.4 实现计费服务 `src/internal/service/pricing_service.go`：EstimatePrice（预估）和 CalculatePrice（结算），实现阶梯计价公式，参数从 config 读取

## 5. HTTP API 层

- [x] 5.1 实现乘客端 handler `src/internal/handler/passenger_handler.go`：POST `/api/v1/rides`、GET `/api/v1/rides/:id`、POST `/api/v1/rides/:id/cancel`
- [x] 5.2 实现司机端 handler `src/internal/handler/driver_handler.go`：POST `/api/v1/rides/:id/accept`、`/arrive`、`/start`、`/complete`，GET `/api/v1/drivers/nearby`
- [x] 5.3 注册路由 `src/internal/handler/router.go` 并挂载到 Gin engine

## 6. 消息队列集成

- [x] 6.1 实现 RabbitMQ 生产者/消费者封装 `src/pkg/mq`：声明队列、发布消息、消费消息
- [x] 6.2 实现 `ride.request` 队列消费逻辑（匹配服务异步处理）
- [x] 6.3 实现 `ride.event` 队列发布逻辑（状态变更时发布事件）

## 7. 并发安全与容错

- [x] 7.1 司机匹配使用 Redis SETNX 分布式锁防止重复分配
- [x] 7.2 状态变更使用数据库事务 + 乐观锁（version 字段）保证一致性

## 8. 测试框架搭建

- [x] 8.1 创建测试目录结构 `test/`，初始化 Go module
- [x] 8.2 实现 `test/mock/passenger.go`：模拟乘客行为（发起叫车、查看订单、取消订单）
- [x] 8.3 实现 `test/mock/driver.go`：模拟司机行为（上线、接单、到达、开始行程、完成行程）
- [x] 8.4 实现 `test/monitor/metrics.go`：收集系统运行指标（匹配耗时、订单量、完成率）
- [x] 8.5 编写集成测试脚本：模拟多乘客多司机并发场景，验证端到端流程
