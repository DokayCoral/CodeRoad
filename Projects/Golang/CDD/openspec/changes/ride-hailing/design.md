## Context

从零构建网约车平台，当前仓库为空，无已有代码。项目分为 `src/`（业务运行代码）和 `test/`（框架测试代码）两部分。技术栈：Go、Gin（HTTP路由）、GORM（ORM）、MySQL（持久化）、Redis（缓存/位置）、RPC（服务间调用）。

## Goals / Non-Goals

**Goals:**
- 实现乘客叫车的完整端到端流程：请求 → 匹配 → 接单 → 行程中 → 完成/取消
- 建立清晰的分层架构，业务代码在 `src/`，测试代码在 `test/`
- 提供 RESTful API 供乘客端和司机端调用
- 基于地理位置的司机匹配算法
- 基于里程和时长的阶梯计费模型

**Non-Goals:**
- 不涉及用户注册/登录（后续实现）
- 不涉及支付系统（后续实现）
- 不涉及实时位置追踪（后续通过 GPS 上报实现）
- 不涉及拼车、预约等扩展场景

## Decisions

### 1. 项目分层架构

采用简洁的分层结构，避免过度设计：

```
src/
├── cmd/          # 服务入口
├── internal/
│   ├── handler/  # HTTP 处理器（Gin handler）
│   ├── service/  # 业务逻辑层
│   ├── repo/     # 数据访问层（GORM）
│   ├── model/    # 数据模型/表结构
│   └── config/   # 配置管理
└── pkg/          # 可复用的公共库

test/
├── mock/         # 模拟乘客/司机行为
└── monitor/      # 监控和指标收集
```

**Rationale**: 标准 Go 项目布局，清晰分层，便于测试。不做过早的微服务拆分，先单体后拆分。

### 2. 行程状态机

行程状态流转如下：

```
Pending  →  Matched  →  Accepted  →  Arrived  →  Started  →  Completed
    ↘                                                      ↗
      Cancelled (乘客/司机/系统取消均可)
```

- **Pending**: 乘客发起叫车，等待匹配
- **Matched**: 系统已分配司机，等待司机接单
- **Accepted**: 司机已接单，前往接乘客
- **Arrived**: 司机已到达上车点
- **Started**: 行程开始（乘客已上车）
- **Completed**: 行程结束，费用已结算
- **Cancelled**: 行程取消（可从 Pending/Matched 状态进入）

**Rationale**: 参考滴滴状态机设计，覆盖核心流程，状态不可逆（除取消外）。

### 3. 司机匹配策略

采用"就近匹配"策略：
1. 获取乘客上车点坐标
2. 从 Redis 中查询半径 3km 内状态为 `Online` 的司机（使用 Redis GEO）
3. 按距离排序，选择最近的可用司机
4. 通过 RPC 通知司机（预留接口，当前使用轮询查询代替）

**Rationale**: Redis GEO 适合地理位置查询，比 MySQL 空间查询更高效。半径可配置，后续可引入更复杂的匹配算法（评分、服务时长等）。

### 4. 计费模型

阶梯计价（参考滴滴快车定价）：
- 起步价：10元（含3公里、10分钟）
- 里程费：超出3公里后 2元/公里
- 时长费：超出10分钟后 0.3元/分钟
- 最低消费：10元

**Rationale**: 简单清晰的阶梯模型，易于实现和测试。价格参数化，后续可通过配置调整。

### 5. API 设计

使用 RESTful 风格，Gin 框架处理路由：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/rides` | 乘客发起叫车 |
| GET | `/api/v1/rides/:id` | 查询行程状态 |
| POST | `/api/v1/rides/:id/accept` | 司机接单 |
| POST | `/api/v1/rides/:id/arrive` | 司机到达上车点 |
| POST | `/api/v1/rides/:id/start` | 开始行程 |
| POST | `/api/v1/rides/:id/complete` | 完成行程 |
| POST | `/api/v1/rides/:id/cancel` | 取消行程 |
| GET | `/api/v1/drivers/nearby` | 查询附近可用司机 |

**Rationale**: 资源导向的 RESTful 设计，`rides` 为核心资源，状态变更通过 action 端点实现。

### 6. 数据库设计

核心表：

**rides** (行程表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 行程ID |
| passenger_id | VARCHAR(64) | 乘客标识 |
| driver_id | VARCHAR(64) | 司机标识（匹配后填充） |
| origin_lng/lat | DECIMAL(10,7) | 起点经纬度 |
| dest_lng/lat | DECIMAL(10,7) | 终点经纬度 |
| status | TINYINT | 行程状态 |
| distance | INT | 预估距离（米） |
| duration | INT | 预估时长（秒） |
| price | INT | 预估价格（分） |
| created_at/updated_at | DATETIME | 时间戳 |

**drivers** (司机表，基础信息)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(64) PK | 司机ID |
| name | VARCHAR(32) | 司机名称 |
| status | TINYINT | Online/Offline/Busy |
| lng/lat | DECIMAL(10,7) | 当前位置 |

**Rationale**: 最小化初始表结构。金额用整数（分）避免浮点精度问题。位置用 DECIMAL 保证精确度。

## Risks / Trade-offs

- **司机匹配依赖 Redis**：Redis 宕机时匹配不可用 → 后续可加 MySQL 降级方案
- **RPC 通知未实现**：当前司机通过轮询获取新订单 → 后续引入 WebSocket 或 gRPC 推送
- **真实距离计算依赖第三方**：当前使用直线距离 → 后续接入地图 API（高德/百度）获取路网距离
- **并发匹配**：多个请求同时匹配同一司机 → 使用 Redis 分布式锁或司机状态原子更新

### 7. 消息队列选型：RabbitMQ

引入 RabbitMQ 处理异步匹配和状态变更通知：
- 乘客叫车请求发布到 `ride.request` 队列，匹配服务异步消费
- 状态变更事件发布到 `ride.event` 队列，通知相关方
- 利用消息 ACK + 重试机制保证匹配可靠性

**Rationale**: RabbitMQ 在 Go 生态成熟（`amqp091-go`），支持可靠投递、死信队列、消息持久化，比 Redis Pub/Sub 更适合关键业务流程。比 Kafka 轻量，当前规模无需 Kafka 的高吞吐能力。

### 8. 坐标系统：GCJ-02

统一使用 GCJ-02 坐标系（国测局坐标系，中国地图法定标准），与高德/腾讯地图兼容。

## Open Questions

<!-- All questions resolved -->
