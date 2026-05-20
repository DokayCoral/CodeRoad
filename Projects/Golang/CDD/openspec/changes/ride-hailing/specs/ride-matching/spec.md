## ADDED Requirements

### Requirement: 自动匹配最近司机

系统 SHALL 在收到叫车请求后，自动查找乘客附近（默认半径 3km）状态为 Online 的司机，并按距离排序选择最近司机进行匹配。

#### Scenario: 附近有可用司机

- **WHEN** 乘客发起叫车请求且附近 3km 内有 Online 状态的司机
- **THEN** 系统将行程分配给距离最近的司机，行程状态变更为 `Matched`

#### Scenario: 附近无可用司机

- **WHEN** 乘客发起叫车请求但附近 3km 内无 Online 状态的司机
- **THEN** 系统返回提示"附近暂无可用司机"，行程状态保持 `Pending`

#### Scenario: 多个请求并发匹配同一司机

- **WHEN** 两个叫车请求同时匹配到同一司机
- **THEN** 系统保证只有一个请求成功匹配到该司机，另一个请求重新匹配或保持 Pending

### Requirement: 司机状态管理

系统 SHALL 维护司机的在线状态和位置信息，作为匹配算法的数据基础。

#### Scenario: 司机上线

- **WHEN** 司机将状态设置为 Online 并上报当前位置（GCJ-02 坐标）
- **THEN** 系统记录司机状态为 Online，更新 Redis GEO 中的位置

#### Scenario: 司机位置更新

- **WHEN** 处于 Online 状态的司机上报新的位置坐标
- **THEN** 系统更新 Redis GEO 中该司机的位置信息

#### Scenario: 查询附近可用司机

- **WHEN** 请求查询指定坐标附近指定半径内的可用司机
- **THEN** 系统返回范围内所有 Online 状态的司机列表，按距离排序
