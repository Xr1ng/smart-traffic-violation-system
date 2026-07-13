# API 设计

来源：[docs/系统设计方案.md](../系统设计方案.md)

AI 读取范围：登录鉴权、图片接入、案件审核、正式违章、统计分析和内部 AI 接口。

---

## 7. API 设计

统一前缀：`/api/v1`

### 7.1 登录与权限

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/auth/login` | 用户登录 |
| `GET` | `/auth/me` | 当前用户信息 |
| `GET` | `/permissions/menus` | 当前用户菜单权限 |

登录请求：

```json
{
  "username": "admin",
  "password": "123456"
}
```

登录响应：

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "reviewer"
  }
}
```

### 7.2 图片接入

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/intakes/citizen-reports` | 市民随手拍上传 |
| `POST` | `/intakes/camera-captures` | 摄像头抓拍上传 |
| `POST` | `/intakes/admin-uploads` | 工作人员后台上传 |

市民上传字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `image` | file | 违章图片 |
| `location_text` | string | 地点描述 |
| `captured_at` | datetime | 拍摄时间 |
| `description` | string | 举报描述 |

摄像头上传字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `image` | file | 抓拍图片 |
| `camera_id` | string | 摄像头编号 |
| `captured_at` | datetime | 抓拍时间 |
| `location_text` | string | 点位名称 |
| `speed` | number | 车速，可选 |
| `signature` | string | 请求签名 |

接入响应：

```json
{
  "case_id": 10001,
  "case_no": "CASE202607070001",
  "status": "uploaded",
  "message": "图片已接收，正在进行 AI 识别"
}
```

### 7.3 案件审核

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/cases` | 案件列表 |
| `GET` | `/cases/{case_id}` | 案件详情 |
| `POST` | `/cases/{case_id}/approve` | 人工审核通过 |
| `POST` | `/cases/{case_id}/reject` | 人工审核驳回 |
| `POST` | `/cases/{case_id}/request-recheck` | 重新触发 AI 初审 |

案件详情响应核心结构：

```json
{
  "id": 10001,
  "case_no": "CASE202607070001",
  "status": "pending_human_review",
  "source_type": "camera",
  "location_text": "人民路与建设路交叉口",
  "captured_at": "2026-07-07T10:30:00+08:00",
  "plate_no": "粤A12345",
  "media": {
    "original_url": "/media/original/10001.jpg",
    "annotated_url": "/media/annotated/10001.jpg"
  },
  "detection_result": {
    "model_version": "yolov8-traffic-v1",
    "objects": [
      {
        "label": "vehicle",
        "confidence": 0.94,
        "bbox": [100, 120, 420, 360]
      },
      {
        "label": "stop_line",
        "confidence": 0.89,
        "bbox": [80, 365, 520, 382]
      },
      {
        "label": "red_light",
        "confidence": 0.92,
        "bbox": [500, 40, 535, 85]
      }
    ]
  },
  "rule_result": {
    "candidate_violation_type": "闯红灯",
    "rule_matched": true,
    "evidence_level": "complete",
    "reason": "车辆位置、停止线和红灯状态等证据满足闯红灯规则。"
  },
  "ai_review": {
    "review_mode": "text_llm",
    "conclusion": "suggest_approve",
    "ai_confidence": 0.88,
    "reason": "规则判定显示车辆在红灯状态下越过停止线，证据链较完整，建议人工重点确认后通过。",
    "risk_points": [],
    "missing_evidence": []
  }
}
```

审核通过请求：

```json
{
  "plate_no": "粤A12345",
  "violation_type": "闯红灯",
  "fine_amount": 200,
  "points": 6,
  "review_opinion": "证据清晰，确认违法。"
}
```

审核驳回请求：

```json
{
  "reject_reason": "图片模糊，无法确认车辆是否越线。"
}
```

### 7.4 正式违章

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/violations` | 违章列表查询 |
| `GET` | `/violations/{violation_id}` | 违章详情 |
| `POST` | `/violations/{violation_id}/notify` | 手动重新发送短信 |
| `GET` | `/owners/{owner_id}/violations` | 车主本人违章查询 |

查询参数：

- `plate_no`
- `violation_type`
- `location_text`
- `start_time`
- `end_time`
- `status`

### 7.5 统计与 LLM 分析

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/statistics/overview` | 总览指标 |
| `GET` | `/statistics/by-location` | 地点统计 |
| `GET` | `/statistics/by-time` | 时间趋势 |
| `GET` | `/statistics/by-type` | 类型占比 |
| `POST` | `/analysis/reports` | 生成 LLM 分析报告 |

生成分析报告请求：

```json
{
  "start_time": "2026-07-01T00:00:00+08:00",
  "end_time": "2026-07-07T23:59:59+08:00"
}
```

两个时间均必填，时间跨度不得超过 366 天。

响应：

```json
{
  "title": "交通违章综合分析报告",
  "start_time": "2026-06-30T16:00:00Z",
  "end_time": "2026-07-07T15:59:59Z",
  "summary": "本期违章总体情况摘要。",
  "trend_analysis": "按日趋势分析。",
  "hotspot_analysis": "高发类型、地点及时段分析。",
  "risk_alerts": ["风险提示"],
  "recommendations": ["治理建议"],
  "statistics_snapshot": {
    "overview": {},
    "trend": [],
    "violation_types": [],
    "locations": [],
    "road_time_hotspots": []
  },
  "author": "AI 分析助手",
  "generated_at": "2026-07-13T06:00:00Z"
}
```

报告同步生成且不持久化。非法日期范围返回 `422`；LLM 不可用或响应无法校验时返回 `503`。

### 7.6 内部 AI 接口

内部接口不直接暴露给前端：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/internal/ai/yolo/detect` | YOLOv8 检测 |
| `POST` | `/internal/ai/ocr/plate` | 车牌 OCR |
| `POST` | `/internal/ai/rules/evaluate` | 违章规则判定 |
| `POST` | `/internal/ai/review/text` | 文本 LLM 初审 |
| `POST` | `/internal/ai/review/vision` | 多模态模型复核 |

YOLOv8 输出：

```json
{
  "case_id": 10001,
  "vehicle_bbox": [100, 120, 420, 360],
  "plate_bbox": [210, 310, 310, 345],
  "detections": [
    {
      "label": "vehicle",
      "confidence": 0.94,
      "bbox": [100, 120, 420, 360]
    },
    {
      "label": "stop_line",
      "confidence": 0.89,
      "bbox": [80, 365, 520, 382]
    },
    {
      "label": "red_light",
      "confidence": 0.92,
      "bbox": [500, 40, 535, 85]
    }
  ],
  "annotated_image_url": "/media/annotated/10001.jpg",
  "model_version": "yolov8-traffic-v1"
}
```

违章规则判定输出：

```json
{
  "case_id": 10001,
  "candidate_violation_type": "闯红灯",
  "rule_code": "RL-001",
  "rule_matched": true,
  "evidence_level": "complete",
  "evidence_items": [
    "检测到车辆",
    "检测到停止线",
    "检测到红灯状态",
    "车辆位置越过停止线"
  ],
  "missing_evidence": [],
  "reason": "根据车辆框、停止线位置和红灯状态，规则判定为疑似闯红灯。"
}
```

LLM 初审输出：

```json
{
  "case_id": 10001,
  "review_mode": "text_llm",
  "conclusion": "suggest_approve",
  "ai_confidence": 0.88,
  "suggested_violation_type": "闯红灯",
  "reason": "规则判定显示车辆在红灯状态下越过停止线，证据链较完整，建议人工终审确认。",
  "risk_points": [],
  "missing_evidence": [],
  "prompt_version": "traffic-review-v1"
}
```

