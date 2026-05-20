## ADDED Requirements

### Requirement: 乘客发起叫车请求

系统 SHALL 允许乘客通过 API 发起叫车请求，提供起点、终点位置信息，创建一个待匹配的行程订单。

#### Scenario: 乘客成功发起叫车

- **WHEN** 乘客提交有效的起点经纬度（GCJ-02）、终点经纬度和乘客标识
- **THEN** 系统创建一条状态为 `Pending` 的行程记录，返回行程 ID 和预估费用

#### Scenario: 起点或终点信息不完整

- **WHEN** 乘客提交的请求缺少起点或终点经纬度
- **THEN** 系统返回 422 错误，提示参数不完整

#### Scenario: 乘客已有进行中的行程

- **WHEN** 乘客当前已有一条状态为 Pending/Matched/Accepted/Arrived/Started 的行程
- **THEN** 系统拒绝新请求，返回 409 错误，提示已有进行中的行程

### Requirement: 行程信息查询

系统 SHALL 允许乘客和司机通过行程 ID 查询行程的完整信息，包括状态、位置、费用等。

#### Scenario: 查询存在的行程

- **WHEN** 请求携带有效的行程 ID
- **THEN** 系统返回行程详情，包含状态、起终点、司机信息（如已分配）、预估费用

#### Scenario: 查询不存在的行程

- **WHEN** 请求的行程 ID 不存在
- **THEN** 系统返回 404 错误
