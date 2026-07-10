# 交通违章智能管理平台 · 内部 AI 接口文档

> **受众：唐高鹏（数据处理工程师）**  
> 版本：2026-07-10 · 分支 `frontend-backend-integration`  
> 后端基地址：`http://localhost:8000`

---

## 目录

1. [概述](#1-概述)
2. [你的四件交付物](#2-你的四件交付物)
3. [Adapter 接口契约（必须实现）](#3-adapter-接口契约必须实现)
4. [如何接入（只改一个文件）](#4-如何接入只改一个文件)
5. [HTTP API 参考（4 个接口）](#5-http-api-参考4-个接口)
6. [鉴权](#6-鉴权)
7. [环境变量](#7-环境变量)
8. [Stub 参考实现](#8-stub-参考实现)
9. [测试你的实现](#9-测试你的实现)

---

## 1. 概述

整个 AI 管线架构：

```
图片上传 → 案件创建
              ↓
    ┌───────── Celery 任务链 ─────────┐
    │  detect_objects_task (YOLO)      │ ← 你的唐高鹏-7
    │       ↓                          │
    │  ocr_plate_task (OCR)            │ ← 你的唐高鹏-8
    │       ↓                          │
    │  evaluate_rule_task (规则判定)     │ ← 你的唐高鹏-9
    │       ↓                          │
    │  ai_review_task (LLM 初审)       │ ← 你的唐高鹏-11
    └──────────────────────────────────┘
              ↓
    案件到达 pending_human_review
              ↓
         人工终审
```

每个 AI 任务内部调用 `/internal/ai/*` HTTP 接口。这些接口通过**可插拔 adapter** 调用你的实现。当前默认用 stub（返回固定假数据），你交付后切到 real。

**你的工作**：实现 4 个 Python 类（YOLO/OCR/规则/LLM），放到 `backend/app/ai/adapters/` 目录，然后在 `providers.py` 里注册。

---

## 2. 你的四件交付物

| 编号 | 名称 | 对应 ABC | 输入 | 输出 |
|------|------|------|------|------|
| 唐高鹏-7 | YOLOv8 检测器 | `YoloDetector` | 图片本地路径 | `DetectionResult` |
| 唐高鹏-8 | OCR 车牌识别 | `OcrEngine` | 车牌裁剪图路径 | 车牌号字符串（失败返 None） |
| 唐高鹏-9 | 规则判定引擎 | `RuleEvaluator` | 检测结果 + OCR + 接入事件 + 规则配置 | `RuleResult` |
| 唐高鹏-11 | LLM 文本初审 | `LLMProvider` | 证据 JSON | `AIReviewResultData` |

---

## 3. Adapter 接口契约（必须实现）

文件位置：`backend/app/ai/adapters/base.py`

### 3.1 YoloDetector

```python
class YoloDetector(ABC):
    @abstractmethod
    def detect(self, image_path: str) -> DetectionResult:
        """对图片进行目标检测。

        Args:
            image_path: 本地临时图片文件的绝对路径（jpg/png/webp，已校验过格式和大小）。

        Returns:
            DetectionResult（见下方 dataclass）
        """
        ...
```

#### DetectionResult

```python
@dataclass
class DetectionResult:
    objects: list[dict]              # 检测到的目标列表
    # 每个 dict 的字段：
    #   label: str       — 类别名（car / truck / bus / motorcycle / person）
    #   confidence: float — 目标检测置信度 (0.0–1.0)
    #   bbox: list[int]   — [x1, y1, x2, y2] 边界框

    vehicle_bbox: list[int] | None   # 主车辆边界框 [x1,y1,x2,y2]，无则 None
    plate_bbox: list[int] | None     # 车牌区域边界框 [x1,y1,x2,y2]，无则 None
    annotated_image_path: str | None # 标注图（画了框的图）的持久化 URL 或本地路径
                                     # stub 返回 None；real 实现应将标注图存到
                                     # settings.MEDIA_STORAGE_DIR 下，返回
                                     # 形如 /media/annotated/xxx.jpg 的路径
    model_version: str               # 模型版本标识（如 "yolov8n-v1"）
```

**YOLO 检测目标类别建议**（spec §2 第一阶段）：car / truck / bus / motorcycle / person。预制 COCO 模型可检出这些。车牌框需要独立预训练模型或使用 yolov8n-plate。

### 3.2 OcrEngine

```python
class OcrEngine(ABC):
    @abstractmethod
    def recognize_plate(self, plate_crop_path: str) -> str | None:
        """从车牌裁剪图中识别车牌号。

        Args:
            plate_crop_path: 车牌区域裁剪图的本地路径
                            （由 YOLO 检出 plate_bbox 后裁剪得到）

        Returns:
            车牌号字符串（如 "京A12345"），识别失败返回 None
        """
        ...
```

### 3.3 RuleEvaluator

```python
class RuleEvaluator(ABC):
    @abstractmethod
    def evaluate(
        self,
        detection: DetectionResult,  # YOLO 检测结果
        ocr_result: str | None,      # OCR 车牌号（可能为 None）
        intake_event: dict,          # 接入事件元数据
        rule: dict,                  # 规则配置
    ) -> RuleResult:
        """判定是否满足违章规则。

        Args:
            intake_event: { source_type, speed, location_text, captured_at, ... }
            rule: { rule_type, rule_code, speed_limit?, lane_roi?, ... }

        Returns:
            RuleResult（见下方）
        """
        ...
```

#### RuleResult

```python
@dataclass
class RuleResult:
    candidate_violation_type: str | None  # 违章类型（speed / special_lane），不匹配为 None
    rule_code: str | None                 # 规则代码（SPD-001 / LANE-001）
    rule_matched: bool                    # 是否满足规则
    evidence_level: str                   # complete / partial / insufficient
    evidence_items: list[str]             # 证据清单（如 "车速120，限速80"）
    missing_evidence: list[str]           # 缺失证据（如 "车速数据缺失"）
    reason: str                           # 判定理由
```

**第一阶段范围**：超速（`rule_type=speed`）和占用专用车道（`rule_type=special_lane`）。

**重要约束（spec §3）**：YOLO 输出的 `confidence` 是目标检测置信度，**不是违章置信度**。违章成立必须由规则判定形成证据链 + LLM 初审意见 + 人工终审共同支撑，不得用 YOLO 置信度直接判定违章。

### 3.4 LLMProvider

```python
class LLMProvider(ABC):
    @abstractmethod
    def review(self, evidence_payload: dict) -> AIReviewResultData:
        """基于证据 JSON 生成 AI 初审意见。

        Args:
            evidence_payload: 自由格式的 JSON dict，包含：
                - detection: YOLO 检测结果（objects/bboxes）
                - ocr_result: OCR 车牌号
                - rule_result: 规则判定结果（RuleResult 各字段）
                - intake_event: 接入事件（位置/时间/速度）
                - case_no: 案件编号

        Returns:
            AIReviewResultData（见下方）
        """
        ...
```

#### AIReviewResultData

```python
@dataclass
class AIReviewResultData:
    conclusion: str            # suggest_approve / need_review / suggest_reject
    ai_confidence: float | None  # AI 置信度 0.0–1.0
    reason: str                # 初审理由
    risk_points: list[str]     # 风险点（如 "车牌模糊，置信度低"）
    missing_evidence: list[str]  # 缺失证据
    prompt_version: str        # Prompt 版本标识（如 "glm-4-flash-v1"）
```

**三个结论的语义**：
- `suggest_approve`：证据链完整，建议通过
- `need_review`：证据存疑，建议人工仔细审核
- `suggest_reject`：证据不足，建议驳回

---

## 4. 如何接入（只改一个文件）

### 4.1 把你的实现放到指定位置

在 `backend/app/ai/adapters/` 下新建你的实现文件（一个或多个）：

```
backend/app/ai/adapters/
├── base.py              ← 接口定义（不动）
├── stub.py              ← stub 参考（不动）
├── yolo_ultralytics.py  ← 你的 YOLO 实现
├── ocr_paddle.py        ← 你的 OCR 实现
├── rule_evaluator.py    ← 你的规则引擎
└── llm_glm.py           ← 你的 LLM 实现
```

每个文件里 import 对应的 ABC 并实现：

```python
# 示例：backend/app/ai/adapters/yolo_ultralytics.py
from ultralytics import YOLO
from app.ai.adapters.base import YoloDetector, DetectionResult

class UltralyticsYoloDetector(YoloDetector):
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)

    def detect(self, image_path: str) -> DetectionResult:
        results = self.model(image_path)
        # ... 解析 results → DetectionResult
        return DetectionResult(...)
```

### 4.2 在 providers.py 注册（只改这一个文件）

文件：`backend/app/ai/providers.py`

在 4 个工厂函数里各加一个 `elif` 分支：

```python
# 在你的新文件头部导入你的实现
from app.ai.adapters.yolo_ultralytics import UltralyticsYoloDetector
from app.ai.adapters.ocr_paddle import PaddleOcrEngine
from app.ai.adapters.rule_evaluator import RoiRuleEvaluator
from app.ai.adapters.llm_glm import GlmLLMProvider

def get_yolo_detector() -> YoloDetector:
    if settings.AI_PROVIDER == "real":
        return UltralyticsYoloDetector()        # ← 加这行
    if settings.AI_PROVIDER == "stub":
        return StubYoloDetector()
    raise _provider_not_supported()

def get_ocr_engine() -> OcrEngine:
    if settings.AI_PROVIDER == "real":
        return PaddleOcrEngine()                # ← 加这行
    if settings.AI_PROVIDER == "stub":
        return StubOcrEngine()
    raise _provider_not_supported()

def get_rule_evaluator() -> RuleEvaluator:
    if settings.AI_PROVIDER == "real":
        return RoiRuleEvaluator()               # ← 加这行
    if settings.AI_PROVIDER == "stub":
        return StubRuleEvaluator()
    raise _provider_not_supported()

def get_llm_provider() -> LLMProvider:
    if settings.AI_PROVIDER == "real":
        return GlmLLMProvider()                 # ← 加这行
    if settings.AI_PROVIDER == "stub":
        return StubLLMProvider()
    raise _provider_not_supported()
```

### 4.3 切到 real 模式

在 `backend/.env` 中修改：

```env
AI_PROVIDER=real
```

不改这行，默认就是 stub（返回固定假数据，不影响前后端联调）。

### 4.4 不改的东西

- **不碰路由**（`routes.py`）——路由只依赖 ABC 接口，不管实现是 stub 还是 real
- **不碰 schemas**（`schemas/ai.py`）——HTTP 响应格式已固定
- **不碰测试**（`tests/ai/`）——测试用 dependency_overrides 注入自己的假 adapter

---

## 5. HTTP API 参考（4 个接口）

全部挂载在 `/internal/ai` 下（不在 `/api/v1` 下）。鉴权要求见 §6。

### 5.1 POST /internal/ai/yolo/detect

对图片进行 YOLO 目标检测。

**请求**

```
POST /internal/ai/yolo/detect
Content-Type: multipart/form-data

image: <图片文件>（必填，jpg/png/webp，≤10MB）
```

**响应** `200 OK`

```json
{
  "objects": [
    {
      "label": "car",
      "confidence": 0.92,
      "bbox": [100, 200, 300, 350]
    }
  ],
  "vehicle_bbox": [100, 200, 300, 350],
  "plate_bbox": [120, 230, 200, 270],
  "annotated_image_url": null,
  "model_version": "stub-yolov8n"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| objects | list[dict] | 检测到的所有目标 |
| objects[].label | str | 类别名 |
| objects[].confidence | float | 检测置信度 |
| objects[].bbox | [int,int,int,int] | 边界框坐标 |
| vehicle_bbox | [int,int,int,int] \| null | 主车辆边界框 |
| plate_bbox | [int,int,int,int] \| null | 车牌边界框 |
| annotated_image_url | str \| null | 标注图的持久化路径（stub 返回 null） |
| model_version | str | 模型版本 |

**错误**：`401`（未登录）、`403`（角色不足）、`422`（图片格式不正确）

### 5.2 POST /internal/ai/ocr/plate

对车牌裁剪图进行 OCR 识别。

**请求**

```
POST /internal/ai/ocr/plate
Content-Type: multipart/form-data

image: <车牌裁剪图片文件>
```

**响应** `200 OK`

```json
{
  "plate_no": "京A12345"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| plate_no | str \| null | 车牌号，识别失败时 null |

### 5.3 POST /internal/ai/rules/evaluate

基于检测结果 + OCR + 事件元数据 + 规则配置，判定违章。

**请求**

```
POST /internal/ai/rules/evaluate
Content-Type: application/json
```

```json
{
  "detection": {
    "objects": [{"label": "car", "confidence": 0.92, "bbox": [100,200,300,350]}],
    "vehicle_bbox": [100,200,300,350],
    "plate_bbox": [120,230,200,270],
    "annotated_image_url": null,
    "model_version": "stub-yolov8n"
  },
  "ocr_result": "京A12345",
  "intake_event": {
    "source_type": "camera",
    "speed": 120,
    "location_text": "中山大道",
    "captured_at": "2026-07-10T10:00:00"
  },
  "rule": {
    "rule_type": "speed",
    "rule_code": "SPD-001",
    "speed_limit": 80
  }
}
```

| 字段 | 说明 |
|------|------|
| detection | YOLO 检测结果（同 5.1 响应） |
| ocr_result | OCR 车牌号（string 或 null） |
| intake_event.speed | 摄像头抓拍上报的车速（超速判定用），**单位 km/h** |
| intake_event.location_text | 地点 |
| rule.rule_type | `"speed"` 或 `"special_lane"` |
| rule.speed_limit | 限速值（超速规则时必填） |
| rule.lane_roi | 专用车道 ROI（专用车道规则时） |

**响应** `200 OK`

```json
{
  "rule_matched": true,
  "evidence_level": "complete",
  "evidence_items": ["车速120，限速80"],
  "reason": "超速判定"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| rule_matched | bool | 是否满足规则 |
| evidence_level | str | complete / partial / insufficient |
| evidence_items | list[str] | 证据清单 |
| reason | str | 判定理由 |

### 5.4 POST /internal/ai/review/text

LLM 文本初审，基于结构化证据生成审核建议。

**请求**

```
POST /internal/ai/review/text
Content-Type: application/json

{
  "detection": {...},
  "ocr_result": "京A12345",
  "rule_result": {
    "rule_matched": true,
    "evidence_level": "complete",
    "evidence_items": ["车速120，限速80"],
    "reason": "超速判定"
  },
  "intake_event": {...},
  "case_no": "CASE20260710001"
}
```

证据体是自由格式 dict，服务端透传给 LLMProvider.review()。建议按上述字段组装。

**响应** `200 OK`

```json
{
  "conclusion": "suggest_approve",
  "ai_confidence": 0.88,
  "reason": "stub: 证据链完整，建议通过"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| conclusion | str | suggest_approve / need_review / suggest_reject |
| ai_confidence | float \| null | AI 置信度 0.0–1.0 |
| reason | str | 初审理由 |

---

## 6. 鉴权

所有 `/internal/ai/*` 接口需要 **admin 或 reviewer 角色**。

请求头携带 JWT：

```
Authorization: Bearer <token>
```

获取 token：

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin1234"}'
```

响应中 `access_token` 即 JWT。

本地测试默认账号：`admin / admin1234`（seed_data 已建）。

---

## 7. 环境变量

在 `backend/.env` 中配置（全部可选，有默认值）：

```env
# AI 模式：stub（假数据，默认）/ real（你的实现）
AI_PROVIDER=stub

# LLM — 智谱 GLM（OpenAI 兼容协议）
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_API_KEY=
LLM_MODEL=glm-4-flash

# 图片上传限制
MAX_IMAGE_SIZE=10485760     # 10MB
ALLOWED_IMAGE_TYPES=image/jpeg,image/png,image/webp

# 文件存储目录
MEDIA_STORAGE_DIR=./media
```

---

## 8. Stub 参考实现

`backend/app/ai/adapters/stub.py` 包含 4 个 stub 类，返回写实固定数据。你可以把它当参考：

| Stub 类 | 返回什么 |
|------|------|
| `StubYoloDetector` | 1 辆 car（0.92 置信度）+ vehicle_bbox + plate_bbox |
| `StubOcrEngine` | `"京A12345"` |
| `StubRuleEvaluator` | 超速：按 speed > speed_limit 判定；专用车道：默认匹配；未知类型：insufficient |
| `StubLLMProvider` | conclusion=suggest_approve, confidence=0.88 |

你的实现只需实现同样的 ABC 方法，返回同样格式的 dataclass。

---

## 9. 测试你的实现

后端全量测试：

```bash
cd backend
python -m pytest -q
# 预期：180 passed（全部通过）

# 只跑 AI 模块测试
python -m pytest tests/ai/ -v

# 用 curl 测试真实端点（确保服务在 8000 端口运行）
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin1234"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 测 YOLO
curl -X POST http://localhost:8000/internal/ai/yolo/detect \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@test_image.jpg"

# 测 OCR
curl -X POST http://localhost:8000/internal/ai/ocr/plate \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@plate_crop.jpg"

# 测规则
curl -X POST http://localhost:8000/internal/ai/rules/evaluate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @rule_test.json

# 测 LLM
curl -X POST http://localhost:8000/internal/ai/review/text \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @evidence.json
```

---

## 附：你的所有任务对应关系

| 你的任务 | ABC 接口 | HTTP 端点 | 你实现什么 |
|------|------|------|------|
| 唐高鹏-7 | `YoloDetector` | `POST /internal/ai/yolo/detect` | `UltralyticsYoloDetector.detect(image_path) -> DetectionResult` |
| 唐高鹏-8 | `OcrEngine` | `POST /internal/ai/ocr/plate` | `PaddleOcrEngine.recognize_plate(crop_path) -> str \| None` |
| 唐高鹏-9 | `RuleEvaluator` | `POST /internal/ai/rules/evaluate` | `RoiRuleEvaluator.evaluate(detection, ocr, event, rule) -> RuleResult` |
| 唐高鹏-11 | `LLMProvider` | `POST /internal/ai/review/text` | `GlmLLMProvider.review(evidence_payload) -> AIReviewResultData` |
| 唐高鹏-5 | — | — | YOLO 模型训练（数据集 + 训练输出 yolov8n-traffic-v1.pt） |
| 唐高鹏-10 | — | — | 违章规则库初始数据（violation_rules 表种子数据） |
| 唐高鹏-14 | — | — | 演示数据准备（50+ 条违章图片） |
