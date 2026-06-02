# ComfyUI-Simple-LLM

一个面向 ComfyUI 的简易 LLM 请求节点，基于 `openai` Python SDK 调用 OpenAI 兼容的 `/v1/chat/completions` 接口。

节点会出现在右键菜单：

```text
eastmoe -> Comfy-Simple-LLM -> 简易 OpenAI API
```

## 功能

- 支持自定义 `base_url`、`apikey` 和 `model`，可连接 OpenAI 或其他 OpenAI 兼容后端。
- 支持 system prompt 与 user prompt。
- 支持 `temperature`、`top_p`、`top_k`、`min_p`、`presence_penalty`、`repetition_penalty`、`max_tokens` 等参数。
- 支持 `reasoning_effort`，可选 `low`、`medium`、`high`、`xhigh`、`max`，并会尽量过滤推理模型输出中的思考片段。
- 支持可选图片、音频、视频输入，也可以通过 `media_path` 传入本地媒体文件。
- 支持文本输出和 JSON 输出。
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
| `reasoning_effort` | 推理强度，可选 `low`、`medium`、`high`、`xhigh` 或 `max`，具体支持情况取决于后端。 |
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

## 使用提示

- 如果使用非 OpenAI 官方服务，请确认该服务支持 `/v1/chat/completions` 和你启用的参数。
- `top_k`、`min_p`、`repetition_penalty`、`thinking` 等字段属于后端相关参数，不同服务可能会忽略或报错。
- 如果要传入视频文件，优先使用 `media_path`，并确认后端支持 `video_url` data URL。
- JSON 模式会请求后端返回 JSON；如果模型仍返回非法 JSON，节点会把原始内容包装到一个 JSON 对象中。

## 依赖

- ComfyUI
- `openai`
- `numpy`
- `Pillow`

其中 `numpy` 和 `Pillow` 通常已由 ComfyUI 提供，仓库的 `requirements.txt` 只额外声明了 `openai`。
