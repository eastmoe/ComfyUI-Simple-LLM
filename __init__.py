import base64
import io
import json
import mimetypes
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image
from openai import OpenAI


class SimpleOpenAIAPINode:
    """
    Simple OpenAI-compatible Chat API node for ComfyUI.

    Features:
    - Uses openai Python SDK
    - Uses /v1/chat/completions
    - Supports base_url, api_key, model
    - Supports system prompt and user prompt
    - Supports temperature, top_p, top_k, min_p, presence_penalty, repetition_penalty
    - Supports reasoning_effort: high / max
    - Supports max_tokens
    - Optional image/audio/video inputs
    - Output mode: plain text or JSON
    - Filters reasoning/thinking content from reasoning models

    Notes:
    - temperature, top_p, presence_penalty, frequency_penalty, max_tokens are common Chat Completions params.
    - reasoning_effort / thinking / top_k / min_p / repetition_penalty are backend-dependent.
    - top_k, min_p, repetition_penalty, thinking are sent through extra_body for OpenAI-compatible backends.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_url": (
                    "STRING",
                    {
                        "default": "https://api.openai.com/v1",
                        "multiline": False,
                    },
                ),
                "apikey": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                    },
                ),
                "model": (
                    "STRING",
                    {
                        "default": "gpt-4o-mini",
                        "multiline": False,
                    },
                ),
                "systemprompt": (
                    "STRING",
                    {
                        "default": "You are a helpful assistant.",
                        "multiline": True,
                    },
                ),
                "userprompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                    },
                ),
                "reasoning_effort": (
                    ["high", "max"],
                    {
                        "default": "high",
                    },
                ),
                "max_tokens": (
                    "INT",
                    {
                        "default": 4096,
                        "min": 1,
                        "max": 262144,
                        "step": 1,
                    },
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.01,
                    },
                ),
                "topp": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                    },
                ),
                "topk": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 1000,
                        "step": 1,
                    },
                ),
                "minp": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                    },
                ),
                "presence_penalty": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": -2.0,
                        "max": 2.0,
                        "step": 0.01,
                    },
                ),
                "repetition_penalty": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.1,
                        "max": 3.0,
                        "step": 0.01,
                    },
                ),
                "output_format": (
                    ["text", "json"],
                    {
                        "default": "text",
                    },
                ),
            },
            "optional": {
                "image": ("IMAGE",),
                "audio": ("AUDIO",),
                "video": ("VIDEO",),
                "media_path": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("text", "json")
    FUNCTION = "run"
    CATEGORY = "api/OpenAI"

    def run(
        self,
        base_url: str,
        apikey: str,
        model: str,
        systemprompt: str,
        userprompt: str,
        reasoning_effort: str,
        max_tokens: int,
        temperature: float,
        topp: float,
        topk: int,
        minp: float,
        presence_penalty: float,
        repetition_penalty: float,
        output_format: str,
        image=None,
        audio=None,
        video=None,
        media_path: str = "",
    ) -> Tuple[str, str]:
        if not apikey:
            raise ValueError("apikey is required.")

        if not model:
            raise ValueError("model is required.")

        client = OpenAI(
            api_key=apikey,
            base_url=base_url.strip() or None,
        )

        user_content: List[Dict[str, Any]] = []

        if userprompt:
            user_content.append(
                {
                    "type": "text",
                    "text": userprompt,
                }
            )

        if image is not None:
            image_data_url = self._comfy_image_to_data_url(image)
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url,
                    },
                }
            )

        if audio is not None:
            audio_part = self._comfy_audio_to_content_part(audio)
            if audio_part is not None:
                user_content.append(audio_part)

        if video is not None:
            video_part = self._comfy_video_to_content_part(video)
            if video_part is not None:
                user_content.append(video_part)

        if media_path and media_path.strip():
            file_part = self._file_path_to_content_part(media_path.strip())
            user_content.append(file_part)

        if not user_content:
            user_content.append(
                {
                    "type": "text",
                    "text": "",
                }
            )

        messages = [
            {
                "role": "system",
                "content": systemprompt or "",
            },
            {
                "role": "user",
                "content": user_content,
            },
        ]

        extra_body: Dict[str, Any] = {}

        # DeepSeek / other reasoning-model compatible options.
        # Your reference format:
        # "thinking": {"type": "enabled"}
        # "reasoning_effort": "high"
        extra_body["thinking"] = {"type": "enabled"}

        # Some OpenAI-compatible backends accept reasoning_effort directly.
        # For maximum compatibility, it is also placed in create_kwargs below.
        selected_reasoning_effort = reasoning_effort if reasoning_effort in {"high", "max"} else "high"

        # Non-standard OpenAI-compatible sampling params.
        if topk and topk > 0:
            extra_body["top_k"] = int(topk)

        if minp and minp > 0:
            extra_body["min_p"] = float(minp)

        if repetition_penalty and abs(float(repetition_penalty) - 1.0) > 1e-6:
            extra_body["repetition_penalty"] = float(repetition_penalty)

        create_kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": float(temperature),
            "top_p": float(topp),
            "presence_penalty": float(presence_penalty),
            "max_tokens": int(max_tokens),
            "reasoning_effort": selected_reasoning_effort,
            "extra_body": extra_body,
        }

        if output_format == "json":
            create_kwargs["response_format"] = {"type": "json_object"}
        else:
            create_kwargs["response_format"] = {"type": "text"}

        response = client.chat.completions.create(**create_kwargs)

        text = self._extract_final_answer(response)
        text = self._strip_reasoning_text(text)

        if output_format == "json":
            json_text = self._normalize_json_text(text)
            return text, json_text

        return text, ""

    def _extract_final_answer(self, response) -> str:
        """
        Extracts assistant final content while avoiding reasoning fields.

        Different OpenAI-compatible reasoning backends may return fields like:
        - message.content
        - message.reasoning_content
        - message.reasoning
        - message.thinking
        - message.additional_kwargs["reasoning_content"]

        This function intentionally returns only message.content.
        """
        try:
            message = response.choices[0].message
        except Exception:
            return ""

        content = getattr(message, "content", "")

        # Some SDK/backends return content as a list of parts instead of a string.
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict):
                    part_type = part.get("type", "")
                    if part_type in {"reasoning", "thinking", "analysis"}:
                        continue
                    if part_type == "text":
                        parts.append(part.get("text", ""))
                    elif "text" in part:
                        parts.append(part.get("text", ""))
                else:
                    parts.append(str(part))
            return "".join(parts)

        if content is None:
            return ""

        return str(content)

    def _strip_reasoning_text(self, text: str) -> str:
        """
        Removes visible chain-of-thought / reasoning blocks from final output.

        Handles common reasoning wrappers:
        - <think>...</think>
        - <thinking>...</thinking>
        - <reasoning>...</reasoning>
        - <analysis>...</analysis>
        - ```thinking ... ```
        - ```reasoning ... ```
        - markdown sections like "Reasoning:" / "思考过程："
        """
        if not text:
            return ""

        cleaned = text

        # XML-like reasoning tags.
        tag_patterns = [
            r"<think\b[^>]*>.*?</think>",
            r"<thinking\b[^>]*>.*?</thinking>",
            r"<reasoning\b[^>]*>.*?</reasoning>",
            r"<analysis\b[^>]*>.*?</analysis>",
            r"<chain_of_thought\b[^>]*>.*?</chain_of_thought>",
        ]

        for pattern in tag_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

        # Fenced reasoning blocks.
        fence_patterns = [
            r"```(?:thinking|think|reasoning|analysis)\s*.*?```",
            r"~~~(?:thinking|think|reasoning|analysis)\s*.*?~~~",
        ]

        for pattern in fence_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

        # If a model outputs explicit reasoning section followed by final answer,
        # keep the final answer part when possible.
        final_markers = [
            "Final Answer:",
            "Final:",
            "Answer:",
            "最终答案：",
            "最终回答：",
            "答案：",
        ]

        for marker in final_markers:
            idx = cleaned.rfind(marker)
            if idx != -1:
                cleaned = cleaned[idx + len(marker):]
                break

        # Remove leading reasoning headings if they remain at the top.
        cleaned = re.sub(
            r"^\s*(Reasoning|Thinking|Analysis|思考过程|推理过程|分析)\s*[:：]\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        return cleaned.strip()

    def _comfy_image_to_data_url(self, image) -> str:
        """
        Converts ComfyUI IMAGE tensor to PNG data URL.

        ComfyUI IMAGE is usually torch tensor shaped:
        - [B, H, W, C]
        - value range 0..1
        """
        img = image

        try:
            import torch

            if isinstance(img, torch.Tensor):
                img = img.detach().cpu().numpy()
        except Exception:
            pass

        img = np.asarray(img)

        if img.ndim == 4:
            img = img[0]

        if img.ndim != 3:
            raise ValueError(f"Unsupported IMAGE shape: {img.shape}")

        img = np.clip(img, 0.0, 1.0)
        img = (img * 255).astype(np.uint8)

        if img.shape[-1] == 4:
            pil_img = Image.fromarray(img, mode="RGBA")
        else:
            pil_img = Image.fromarray(img[..., :3], mode="RGB")

        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return f"data:image/png;base64,{encoded}"

    def _comfy_audio_to_content_part(self, audio) -> Optional[Dict[str, Any]]:
        """
        Best-effort AUDIO handling.

        ComfyUI AUDIO commonly appears as a dict containing waveform and sample_rate.
        This emits a common 'input_audio' content part.
        """
        if audio is None:
            return None

        if isinstance(audio, str) and os.path.exists(audio):
            return self._file_path_to_content_part(audio)

        if isinstance(audio, dict):
            waveform = audio.get("waveform", None)
            sample_rate = audio.get("sample_rate", 44100)

            if waveform is None:
                return {
                    "type": "text",
                    "text": "[Audio input was provided, but waveform data was not found.]",
                }

            wav_bytes = self._waveform_to_wav_bytes(waveform, sample_rate)
            encoded = base64.b64encode(wav_bytes).decode("utf-8")

            return {
                "type": "input_audio",
                "input_audio": {
                    "data": encoded,
                    "format": "wav",
                },
            }

        return {
            "type": "text",
            "text": "[Audio input was provided, but this AUDIO object type is not supported by this node.]",
        }

    def _comfy_video_to_content_part(self, video) -> Optional[Dict[str, Any]]:
        """
        Best-effort VIDEO handling.

        Direct VIDEO support depends on the OpenAI-compatible backend.
        Prefer media_path for video files if your backend supports video_url data URLs.
        """
        if video is None:
            return None

        if isinstance(video, str) and os.path.exists(video):
            return self._file_path_to_content_part(video)

        return {
            "type": "text",
            "text": "[Video input was provided, but direct VIDEO tensor/object upload is backend-dependent. Use media_path for video files if your backend supports video data URLs.]",
        }

    def _file_path_to_content_part(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"media_path does not exist: {path}")

        mime_type, _ = mimetypes.guess_type(path)
        mime_type = mime_type or "application/octet-stream"

        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

        data_url = f"data:{mime_type};base64,{encoded}"

        if mime_type.startswith("image/"):
            return {
                "type": "image_url",
                "image_url": {
                    "url": data_url,
                },
            }

        if mime_type.startswith("audio/"):
            fmt = self._audio_format_from_mime(mime_type, path)
            return {
                "type": "input_audio",
                "input_audio": {
                    "data": encoded,
                    "format": fmt,
                },
            }

        if mime_type.startswith("video/"):
            return {
                "type": "video_url",
                "video_url": {
                    "url": data_url,
                },
            }

        return {
            "type": "text",
            "text": f"[Unsupported media file attached: {os.path.basename(path)}, mime={mime_type}]",
        }

    def _waveform_to_wav_bytes(self, waveform, sample_rate: int) -> bytes:
        """
        Converts waveform tensor/array to WAV bytes.
        """
        try:
            import torch

            if isinstance(waveform, torch.Tensor):
                waveform = waveform.detach().cpu().numpy()
        except Exception:
            pass

        arr = np.asarray(waveform)

        # Common shapes:
        # [B, C, N], [C, N], [N]
        if arr.ndim == 3:
            arr = arr[0]

        if arr.ndim == 2:
            # Convert [C, N] to [N, C] if needed.
            if arr.shape[0] <= 8:
                arr = arr.T

        if arr.ndim == 1:
            arr = arr[:, None]

        arr = np.clip(arr, -1.0, 1.0)
        pcm = (arr * 32767.0).astype(np.int16)

        import wave

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(pcm.shape[1])
            wf.setsampwidth(2)
            wf.setframerate(int(sample_rate))
            wf.writeframes(pcm.tobytes())

        return buffer.getvalue()

    def _audio_format_from_mime(self, mime_type: str, path: str) -> str:
        ext = os.path.splitext(path)[1].lower().replace(".", "")

        if ext in {"wav", "mp3", "m4a", "ogg", "flac", "webm"}:
            return ext

        if "mpeg" in mime_type:
            return "mp3"

        if "wav" in mime_type:
            return "wav"

        return ext or "wav"

    def _normalize_json_text(self, text: str) -> str:
        """
        Returns pretty JSON if model output is valid JSON.
        If invalid, returns a JSON object wrapping the raw text.
        """
        stripped = text.strip()

        # Remove common markdown fences if a backend ignores response_format.
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?", "", stripped, flags=re.IGNORECASE).strip()
            stripped = re.sub(r"```$", "", stripped).strip()

        try:
            parsed = json.loads(stripped)
            return json.dumps(parsed, ensure_ascii=False, indent=2)
        except Exception:
            return json.dumps(
                {
                    "raw": text,
                    "error": "Model output was not valid JSON.",
                },
                ensure_ascii=False,
                indent=2,
            )


NODE_CLASS_MAPPINGS = {
    "SimpleOpenAIAPINode": SimpleOpenAIAPINode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SimpleOpenAIAPINode": "Simple OpenAI API",
}