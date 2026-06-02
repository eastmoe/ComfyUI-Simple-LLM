const { app } = window.comfyAPI.app;

const NODE_CLASS = "SimpleOpenAIAPINode";
const NODE_TITLE = "简易 OpenAI API";

const INPUT_LABELS = {
  image: "图片",
  audio: "音频",
  video: "视频",
  base_url: "接口地址",
  apikey: "API 密钥",
  model: "模型",
  systemprompt: "系统提示词",
  userprompt: "用户提示词",
  reasoning_effort: "推理强度",
  max_tokens: "最大输出 Tokens",
  temperature: "温度",
  topp: "Top P",
  topk: "Top K",
  minp: "Min P",
  presence_penalty: "存在惩罚",
  repetition_penalty: "重复惩罚",
  output_format: "输出格式",
  media_path: "媒体路径",
};

const OUTPUT_LABELS = {
  text: "文本",
  json: "JSON",
  "文本": "文本",
  "JSON": "JSON",
};

function chainCallback(target, name, callback) {
  const original = target[name];
  target[name] = function (...args) {
    const result = original?.apply(this, args);
    callback.apply(this, args);
    return result;
  };
}

function applyLabels(node) {
  if (node.constructor?.comfyClass !== NODE_CLASS && node.type !== NODE_CLASS) {
    return;
  }

  node.title = NODE_TITLE;

  for (const input of node.inputs ?? []) {
    const label = INPUT_LABELS[input.name] ?? INPUT_LABELS[input.label];
    if (!label) continue;
    input.label = label;
    input.localized_name = label;
  }

  for (const output of node.outputs ?? []) {
    const label = OUTPUT_LABELS[output.name] ?? OUTPUT_LABELS[output.label];
    if (!label) continue;
    output.label = label;
    output.localized_name = label;
  }

  for (const widget of node.widgets ?? []) {
    const label = INPUT_LABELS[widget.name] ?? INPUT_LABELS[widget.label];
    if (!label) continue;
    widget.label = label;
    widget.localized_name = label;
  }

  app.graph?.setDirtyCanvas(true, true);
}

app.registerExtension({
  name: "eastmoe.ComfySimpleLLM.i18n",

  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData?.name !== NODE_CLASS) return;

    nodeData.display_name = NODE_TITLE;
    nodeData.output_name = ["文本", "JSON"];

    for (const section of ["required", "optional"]) {
      const inputs = nodeData.input?.[section];
      if (!inputs) continue;

      for (const [name, spec] of Object.entries(inputs)) {
        const label = INPUT_LABELS[name];
        if (!label || !Array.isArray(spec)) continue;
        const options = spec[1] ?? {};
        options.display_name = label;
        options.label = label;
        spec[1] = options;
      }
    }

    chainCallback(nodeType.prototype, "onNodeCreated", function () {
      applyLabels(this);
    });

    chainCallback(nodeType.prototype, "onConfigure", function () {
      applyLabels(this);
    });
  },

  nodeCreated(node) {
    applyLabels(node);
  },
});
