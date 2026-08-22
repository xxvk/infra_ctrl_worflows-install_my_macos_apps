# Vision models comparison: deepseek-v4-flash-vision-exp vs qwen3-vl-flash

Comparison of the two cloud vision backends used by the `dsh-vision-router`
chain (see `deepseek-harness-operations.md` → VL capability). Both models are
new; public benchmark tables are sparse. Every figure below is labelled with
its provenance: **official** (vendor docs/announcement), **vendor claim**
(no public replication), or **third-party** (independent source).

## TL;DR

| | deepseek-v4-flash-vision-exp | qwen3-vl-flash |
|---|---|---|
| 一句话定位 | 完整 DeepSeek 模型 + 视觉（Agent 型） | 轻量视觉专家（细节/视频/便宜） |
| 上线时间 | 2026-08-21（实验性质 exp） | 2026-01-22（当前版） |
| 上下文 | 1M tokens | ~260K tokens |
| 单图 token 上限 | ≤384 tokens | ≤16,384 tokens |
| 视频输入 | ❌ | ✅（时间戳定位） |
| 文档/表格/公式/多语种 OCR | 基础 | 强项 |
| 通用推理/Agent 能力 | 强（与 v4-flash 持平） | 弱（OSWorld 41.6） |
| 价格（每百万 token） | $0.22 in / $0.66 out（非高峰） | ¥0.15 in / ¥1.5 out（0–32K 档） |

## 硬规格对比

| 规格 | deepseek-v4-flash-vision-exp | qwen3-vl-flash |
|---|---|---|
| 上下文长度 | **1M**（与 v4-flash 相同，官方） | ~**260,096**（非思考）/ ~258,048（思考），官方 |
| 最大输出 | 384K（官方） | 未公开（按 128K–256K 档计费） |
| 思考模式 | ✅ 非思考/思考（默认思考） | ✅ 非思考/思考（`enable_thinking`） |
| 图片格式 | JPEG / PNG / GIF / WebP（按文件内容识别，非扩展名） | 图像 + 视频 |
| 单图 token 上限 | **≤384 tokens/图**（按尺寸换算） | **≤16,384 tokens/图** |
| API 形态 | Chat Completions / Responses / Anthropic Messages 三种（官方） | OpenAI 兼容 + 百炼专用 |
| 附加能力 | JSON 输出、工具调用、前缀补全（Beta）；不支持 FIM | Batch 半价、上下文缓存折扣 |
| 并发上限 | 2500（官方） | 未公开 |

来源：DeepSeek [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing) 与
[Vision 指南](https://api-docs.deepseek.com/guides/vision/)（官方）；qwen3-vl-flash
见阿里云 [模型调用计费](https://help.aliyun.com/zh/model-studio/model-pricing) 与
[能力介绍](https://toolnavs.com/article/479-shi-jue-yu-yan-yi-ti-hua-sheng-ji-qwen-3-vl-flash-ti-gong-dai-li-kong-zhi-zhang)（官方/厂商）。

## 能力差异

### deepseek-v4-flash-vision-exp — "Agent 型多模态"
- 纯文本能力（Agent、推理、世界知识）**与 V4-Flash 正式版持平**（官方）——看图之外仍是顶级通用推理模型，这是它最大的优势
- 多模态 Agent 基准官方称**接近 Opus-4.8**（vendor claim；BenchLM 综合分 Opus-4.8 = 85.2 为第三方参照，[BenchLM](https://benchlm.ai/best/computer-use)）
- 擅长：描述图片、识别截图文字、分析图表（官方用途列表）
- 局限：**仅图片、无视频**；单图 384 token 上限 → 大图/密集小字/复杂版面会被压缩，细节保留有限
- 实验性质（exp），API 行为可能调整

### qwen3-vl-flash — "视觉专家型"
- 图像 + **视频时序理解**（事件定位、时间戳提取，官方）
- **文档解析**（表格/公式）、**多语种 OCR**（官方列出的典型场景）
- 2D/3D 目标检测、空间关系、遮挡判断（官方）
- 单图最多 16,384 tokens → 细节/小字/复杂版面保留更好
- 轻量设计：响应快、成本低；但通用推理/Agent 弱于 DS vision（OSWorld 41.6，第三方 [airank.dev](https://airank.dev/models/qwen3-vl-flash)）
- "优于开源 Qwen3-VL-30B-A3B / Qwen2.5-72B" 为**厂商口径**，无公开复测

## 价格对比（每百万 token）

| 项目 | deepseek-v4-flash-vision-exp（USD，与 v4-flash 同价） | qwen3-vl-flash（CNY） |
|---|---|---|
| 输入（缓存未命中） | $0.22 非高峰 / $0.44 高峰（≈¥1.6 / ¥3.2） | ¥0.15（0–32K）/ ¥0.3 / ¥0.6 |
| 输入（缓存命中） | **$0.007**（≈¥0.05） | 上下文缓存折扣 |
| 输出 | $0.66 非高峰 / $1.32 高峰（≈¥4.8 / ¥9.5） | ¥1.5 / ¥3 / ¥6 |

- qwen 单价便宜：输入约 10 倍、输出约 3 倍价差（CNY 折算）
- 但 DS 单图仅 ≤384 token、qwen 可达 16K：摊到每次看图，DS 的 token 开销更小，**量大时 qwen 更省、量小时差距缩小**
- DS 缓存命中价极低（$0.007/M）：长会话/重复图片场景很便宜

来源：DeepSeek [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing)（官方）；
阿里云 [模型调用计费](https://help.aliyun.com/zh/model-studio/model-pricing)（官方）。

## 与 vision-router 链的关系（2026-08-21 定稿）

当前链顺序：`deepseek-vision/deepseek-v4-flash-vision-exp`（主力）→
`aliyun/qwen3-vl-flash`（次主力）→ `local-ocr/deepseek-ocr-2`（本地）→ OVH（兜底）。

分工逻辑：
- **DS vision**：截图理解 + Agent 操作、需要推理、与文字模型同源（同一把 key、同价位）
- **qwen3-vl-flash**：密集文档/表格/公式、多语种 OCR、视频、需要细节 —— 恰好补 DS 单图 384 token 上限的短板
- 若大图在 DS 端看不清会自动落到 qwen（16K 单图上限），链条设计互相覆盖短板

## 待补充

- deepseek-v4-flash-vision-exp 具体 MMMU/OCRBench/DocVQA 数值：官方尚未公布（上线当日即录入）
- qwen3-vl-flash 的 MMMU/DocVQA 官方分数：未见公开表
- 两模型发布后若有正式 benchmark 或价格调整，更新本文件
