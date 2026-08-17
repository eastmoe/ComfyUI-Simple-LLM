# ComfyUI-Simple-LLM

一个面向 ComfyUI 的简易 LLM 请求节点，基于 `openai` Python SDK 调用 OpenAI 兼容的 `/v1/chat/completions` 接口。

节点会出现在右键菜单：

```text
eastmoe -> Comfy-Simple-LLM -> 简易 OpenAI API
eastmoe -> Comfy-Simple-LLM -> 思维链过滤
```

## 功能

- 支持自定义 `base_url`、`apikey` 和 `model`，可连接 OpenAI 或其他 OpenAI 兼容后端。
- 支持 system prompt 与 user prompt。
- 支持 `temperature`、`top_p`、`top_k`、`min_p`、`presence_penalty`、`repetition_penalty`、`max_tokens` 等参数。
- 支持 `reasoning_effort`，可选 `off`、`low`、`medium`、`high`、`xhigh`、`max`，并会尽量过滤推理模型输出中的思考片段。
- 支持可选图片、音频、视频输入，也可以通过 `media_path` 传入本地媒体文件。
- 支持文本输出和 JSON 输出。
- 提供独立的“思维链过滤”节点，可连接任意文本输出，并按 `<think>`、`<thinking>`、`<reasoning>`、`<analysis>`、Markdown 推理块或 Harmony `analysis/final` 通道过滤思维链。
- 提供中文本地化文件 `locales/zh-CN/nodeDefs.json`、`locales/zh/nodeDefs.json` 和 `locales/zh-cn/nodeDefs.json`，用于覆盖节点、参数和接口名称；同时保留 `locales/zh-CN/nodes.json` 作为兼容说明文件。
- 内置前端扩展 `web/simple_llm_i18n.js`，即使 ComfyUI 全局界面语言不是中文，也会把本节点标题、插槽和参数标签显示为中文。

## 安装

进入 ComfyUI 的 `custom_nodes` 目录后克隆本仓库：

```bash
cd ComfyUI/custom_nodes
git clone <this-repo-url> ComfyUI-Simple-LLM
```

安装依赖：

```bash
cd ComfyUI-Simple-LLM
pip install -r requirements.txt
```

重启 ComfyUI 后，在右键菜单 `eastmoe -> Comfy-Simple-LLM` 下添加节点。

## 节点说明

### 简易 OpenAI API

节点类名：`SimpleOpenAIAPINode`

输入参数：

| 参数 | 说明 |
| --- | --- |
| `base_url` | OpenAI 兼容接口地址，例如 `https://api.openai.com/v1`。 |
| `apikey` | API 密钥。 |
| `model` | 模型名称。 |
| `systemprompt` | system 角色提示词。 |
| `userprompt` | user 角色提示词。 |
| `reasoning_effort` | 推理强度，可选 `off`、`low`、`medium`、`high`、`xhigh` 或 `max`，具体支持情况取决于后端。`off` 不发送 reasoning/thinking 参数。 |
| `max_tokens` | 最大输出 token 数。 |
| `temperature` | 输出随机性。 |
| `topp` | 对应 Chat Completions 的 `top_p`。 |
| `topk` | 非标准采样参数，非 0 时通过 `extra_body` 发送。 |
| `minp` | 非标准采样参数，非 0 时通过 `extra_body` 发送。 |
| `presence_penalty` | 存在惩罚。 |
| `repetition_penalty` | 非标准重复惩罚参数，非默认值时通过 `extra_body` 发送。 |
| `output_format` | 输出格式，可选 `text` 或 `json`。 |
| `image` | 可选图片输入，会转换为 PNG data URL。 |
| `audio` | 可选音频输入，会尽量转换为 `input_audio`。 |
| `video` | 可选视频输入，直接支持情况取决于接口后端。 |
| `media_path` | 可选本地媒体文件路径，按 MIME 类型转换后发送。 |

输出：

| 输出 | 说明 |
| --- | --- |
| `text` | 模型最终文本响应。 |
| `json` | 当 `output_format=json` 时输出格式化 JSON；否则为空字符串。 |

### 思维链过滤

节点类名：`ChainOfThoughtFilterNode`

将其它节点的文本输出连接到 `text` 输入，节点会删除指定格式的思维链，并从 `文本` 输出最终内容。默认模式为最常见且较保守的 `<think>...</think>`。

过滤模式：

| 模式 | 行为 |
| --- | --- |
| `<think>...</think>` | 仅过滤 `think` 标签，包括缺少起始或结束标签的截断输出。 |
| `自动（常见格式）` | 过滤所有受支持的标签、Markdown 推理块及 Harmony analysis 通道。 |
| `<thinking>...</thinking>` | 仅过滤 `thinking` 标签。 |
| `<reasoning>...</reasoning>` | 仅过滤 `reasoning` 标签。 |
| `<analysis>...</analysis>` | 仅过滤 `analysis` 标签。 |
| `Markdown 推理块` | 过滤标记为 think/thinking/reasoning/analysis 的代码围栏，或“Reasoning → Final Answer”章节。 |
| `Harmony analysis/final` | 从原始 Harmony 文本中丢弃 analysis 通道并提取 final 通道。 |

自动模式还识别 `<chain_of_thought>...</chain_of_thought>`。当最终回答整体包在 `<answer>`、`<output>` 或 `<final>` 中时，节点会去掉最外层标签。

## 使用提示

- 如果使用非 OpenAI 官方服务，请确认该服务支持 `/v1/chat/completions` 和你启用的参数。
- `top_k`、`min_p`、`repetition_penalty`、`thinking` 等字段属于后端相关参数，不同服务可能会忽略或报错。
- DeepSeek 思考模式下，`message.reasoning_content` 和 `message.content` 是分开的；`max_tokens` 可能会先被推理内容消耗完，导致最终 `content` 为空。节点会在 `max` 推理耗尽预算时自动用 `high` 重试一次；如果仍无最终内容，会在文本输出中显示诊断信息。
- 如果要传入视频文件，优先使用 `media_path`，并确认后端支持 `video_url` data URL。
- JSON 模式会请求后端返回 JSON；如果模型仍返回非法 JSON，节点会把原始内容包装到一个 JSON 对象中。
- 思维链过滤节点默认只处理 `<think>`，适合大多数 DeepSeek-R1/Qwen3 类输出；只有在来源格式不确定时才建议使用自动模式。

## 依赖

- ComfyUI
- `openai`
- `numpy`
- `Pillow`

其中 `numpy` 和 `Pillow` 通常已由 ComfyUI 提供，仓库的 `requirements.txt` 只额外声明了 `openai`。
