## ADDED Requirements

### Requirement: 行程状态流转

系统 SHALL 严格按状态机定义管理行程状态流转，禁止非法状态变更。

有效状态流转：
- `Pending` → `Matched`（系统匹配成功）
- `Matched` → `Accepted`（司机接单）
- `Accepted` → `Arrived`（司机到达上车点）
- `Arrived` → `Started`（乘客上车，行程开始）
- `Started` → `Completed`（到达目的地，行程结束）
- `Pending` → `Cancelled`（乘客/系统取消）
- `Matched` → `Cancelled`（司机/乘客/系统取消）

#### Scenario: 司机接单

- **WHEN** 司机对状态为 `Matched` 的行程发起接单操作
- **THEN** 行程状态变更为 `Accepted`，记录司机 ID 和接单时间

#### Scenario: 司机到达上车点

- **WHEN** 司机对状态为 `Accepted` 的行程发起到达操作
- **THEN** 行程状态变更为 `Arrived`，记录到达时间

#### Scenario: 行程开始

- **WHEN** 司机对状态为 `Arrived` 的行程发起开始行程操作
- **THEN** 行程状态变更为 `Started`，记录行程开始时间

#### Scenario: 行程完成

- **WHEN** 司机对状态为 `Started` 的行程发起完成操作，并提供实际行驶距离和时长
- **THEN** 行程状态变更为 `Completed`，计算实际费用并记录完成时间

#### Scenario: 乘客在等待阶段取消

- **WHEN** 乘客对状态为 `Pending` 或 `Matched` 的行程发起取消操作
- **THEN** 行程状态变更为 `Cancelled`，记录取消方和取消原因

#### Scenario: 非法状态变更被拒绝

- **WHEN** 对行程发起不符合状态机的操作（如对 `Pending` 行程发起"开始行程"）
- **THEN** 系统返回 409 错误，提示当前状态不允许该操作

### Requirement: 行程事件通知

系统 SHALL 在行程状态变更时，通过 RabbitMQ 发布事件消息，供其他服务消费。

#### Scenario: 状态变更发布事件

- **WHEN** 行程状态发生变更
- **THEN** 系统向 `ride.event` 队列发布一条包含行程 ID、新状态、时间戳的事件消息
