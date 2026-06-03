# 后端接口 Spec：模型 API 配置

## 1. 适用范围

本文档定义模型 API 配置中心涉及的后端接口合同和服务规则。

覆盖能力：

- 文本模型配置 CRUD。
- 图片模型配置 CRUD。
- 配置软删除。
- 配置启用切换。
- 文本模型连通性测试。
- 图片模型连通性测试。
- 测试日志记录。
- 生成任务前置校验。

不覆盖能力：

- 多用户、团队级密钥管理。
- 用量统计和费用分析。
- 定时健康检查。
- 多模型自动路由。

## 2. 核心后端规则

### 2.1 配置类型

`config_type` 只支持：

- `text`：文本生成模型。
- `image`：图片生成模型。

文本生成任务只读取当前启用且最近测试成功的文本配置；图片生成任务只读取当前启用且最近测试成功的图片配置。

### 2.2 API Key 安全

- API Key 必须由后端保存。
- 列表和详情接口不得返回完整 API Key。
- 测试日志不得保存完整 API Key。
- 错误信息不得包含 API Key、内部异常堆栈或数据库错误原文。
- Markdown 导出不得包含 API Key。

### 2.3 测试状态

`last_test_status` 支持：

- `untested`：已保存但未测试。
- `success`：最近一次测试成功。
- `failed`：最近一次测试失败。

创建配置后状态为 `untested`。

编辑配置后必须重置为：

- `last_test_status = "untested"`
- `last_tested_at = null`
- `last_test_error = null`

避免用户修改 API Key、模型名称或接口地址后继续沿用旧的成功状态。

### 2.4 启用规则

- 同一 `config_type` 下最多只有一条未删除配置 `enabled=true`。
- 启用某条配置时，后端必须自动将同类型其他未删除配置设为 `enabled=false`。
- 不要求被启用配置最近测试成功；但生成任务只能使用最近测试成功的启用配置。

### 2.5 软删除规则

删除配置必须使用软删除：

- 设置 `deleted_at = now`。
- 设置 `enabled = false`。
- 更新 `updated_at`。

软删除原因：

- `model_api_test_logs` 会引用配置 ID。
- 保留测试日志有利于排查失败原因。
- 硬删除容易触发外键约束或丢失审计信息。

已删除配置：

- 不在列表接口返回。
- 详情、编辑、测试、启用接口均返回“模型配置不存在”。
- 不参与生成任务前置校验。

允许删除当前启用的唯一配置。删除后该类型没有可用配置，生成任务应提示用户重新配置。

## 3. 数据对象

### 3.1 ModelApiConfig

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 配置 ID |
| config_type | text / image | 配置类型 |
| provider_mode | preset / custom | 供应商配置方式 |
| provider_preset | string | 供应商预设标识 |
| provider_name | string | 供应商名称 |
| api_base_url | string | API Base URL |
| api_key_secret | string | 后端保存的 API Key |
| model_name | string | 模型名称 |
| image_size | string | 图片尺寸，仅图片模型使用 |
| endpoint_path | string | 图片接口路径，仅图片模型使用 |
| supports_reference_image | boolean | 是否支持参考图输入 |
| remark | string | 备注 |
| enabled | boolean | 是否启用 |
| last_test_status | untested / success / failed | 最近测试状态 |
| last_tested_at | datetime | 最近测试时间 |
| last_test_error | string | 最近测试失败原因 |
| deleted_at | datetime | 软删除时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 3.2 ModelApiConfigResponse

响应对象不得包含完整 API Key。

建议返回：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 配置 ID |
| config_type | text / image | 配置类型 |
| provider_mode | preset / custom | 供应商配置方式 |
| provider_preset | string | 供应商预设标识 |
| provider_name | string | 供应商名称 |
| api_base_url | string | API Base URL |
| model_name | string | 模型名称 |
| image_size | string | 图片尺寸 |
| endpoint_path | string | 图片接口路径 |
| supports_reference_image | boolean | 是否支持参考图输入 |
| remark | string | 备注 |
| enabled | boolean | 是否启用 |
| last_test_status | string | 最近测试状态 |
| last_tested_at | datetime | 最近测试时间 |
| last_test_error | string | 最近失败原因 |
| has_api_key | boolean | 是否已保存 API Key |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 3.3 ModelApiTestLog

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 测试日志 ID |
| config_id | string | 关联配置 ID |
| config_type | text / image | 配置类型 |
| request_summary | string | 脱敏请求摘要 |
| success | boolean | 是否成功 |
| response_summary | string | 脱敏响应摘要 |
| error_message | string | 失败原因 |
| latency_ms | integer | 请求耗时 |
| tested_at | datetime | 测试时间 |

## 4. 接口定义

### 4.1 查询配置列表

```text
GET /api/model-configs?config_type=text|image
```

响应：

- `200`：`ModelApiConfigResponse[]`。
- 默认过滤 `deleted_at is null`。
- 如果传入 `config_type`，只返回对应类型。

### 4.2 创建配置

```text
POST /api/model-configs
```

请求体：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| config_type | text / image | 是 | 配置类型 |
| provider_mode | preset / custom | 是 | 配置方式 |
| provider_preset | string | 否 | 供应商预设 |
| provider_name | string | 是 | 供应商名称 |
| api_base_url | string | 是 | API Base URL |
| api_key | string | 是 | API Key |
| model_name | string | 是 | 模型名称 |
| image_size | string | image 必填 | 图片尺寸 |
| endpoint_path | string | 否 | 图片接口路径 |
| supports_reference_image | boolean | 否 | 是否支持参考图 |
| remark | string | 否 | 备注 |
| enabled | boolean | 否 | 是否启用 |

响应：

- `200`：`ModelApiConfigResponse`。
- `400`：字段非法。

业务要求：

- `api_base_url` 必须以 `http://` 或 `https://` 开头。
- 创建后 `last_test_status = "untested"`。
- 如果创建时 `enabled=true`，同类型其他配置必须自动停用。

### 4.3 更新配置

```text
PUT /api/model-configs/{config_id}
```

响应：

- `200`：更新后的 `ModelApiConfigResponse`。
- `400`：字段非法。
- `404`：配置不存在或已删除。

业务要求：

- 如果请求中的 API Key 为空或为占位值，后端应保留原 API Key。
- 如果用户提供新的 API Key，后端覆盖旧值。
- 保存成功后重置测试状态为 `untested`。
- 已删除配置不得更新。

### 4.4 删除配置

```text
DELETE /api/model-configs/{config_id}
```

响应：

- `200`：`{ "ok": true }`。
- `404`：配置不存在或已删除。

业务要求：

- 使用软删除，不删除测试日志。
- 允许删除当前启用的唯一配置。
- 删除后该配置不再出现在列表中。

### 4.5 启用配置

```text
POST /api/model-configs/{config_id}/enable
```

响应：

- `200`：启用后的 `ModelApiConfigResponse`。
- `404`：配置不存在或已删除。

业务要求：

- 将目标配置 `enabled=true`。
- 将同类型其他未删除配置 `enabled=false`。

### 4.6 测试配置

```text
POST /api/model-configs/{config_id}/test
```

响应：

- `200`：测试结果对象。
- `404`：配置不存在或已删除。

测试结果对象：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| success | boolean | 是否成功 |
| message | string | 中文结果说明 |
| latency_ms | integer | 请求耗时 |
| response_summary | string | 脱敏响应摘要 |

业务要求：

- 文本配置发送轻量文本测试请求。
- 图片配置发送轻量文生图测试请求。
- 每次测试必须写入 `ModelApiTestLog`。
- 每次测试必须更新配置的 `last_test_status`、`last_tested_at` 和 `last_test_error`。
- 测试失败信息必须是可理解的中文错误，不暴露内部堆栈。

## 5. 生成任务前置校验

文本生成任务执行前：

- 必须存在 `config_type = text`、`enabled=true`、`deleted_at is null` 的配置。
- 该配置 `last_test_status` 必须为 `success`。

图片生成任务执行前：

- 必须存在 `config_type = image`、`enabled=true`、`deleted_at is null` 的配置。
- 该配置 `last_test_status` 必须为 `success`。

参考图参与图片生成时：

- 当前图片配置必须 `supports_reference_image = true`。
- 当前角色必须存在可读取的参考图。

## 6. 前端 Service 对齐

| 前端方法 | 后端接口 |
| --- | --- |
| `listModelConfigs` | `GET /api/model-configs` |
| `createModelConfig` | `POST /api/model-configs` |
| `updateModelConfig` | `PUT /api/model-configs/{config_id}` |
| `deleteModelConfig` | `DELETE /api/model-configs/{config_id}` |
| `enableModelConfig` | `POST /api/model-configs/{config_id}/enable` |
| `testModelConfig` | `POST /api/model-configs/{config_id}/test` |

## 7. 验收标准

- 列表接口不返回软删除配置。
- 响应中不包含完整 API Key。
- 编辑配置后测试状态重置为 `untested`。
- 测试失败配置可以删除，且不会因测试日志外键失败。
- 删除当前启用的唯一配置后，该类型没有启用配置。
- 已删除配置不能编辑、测试或启用。
- 同一配置类型最多只有一条启用配置。
- 文本和图片生成任务只使用启用且测试成功的配置。
