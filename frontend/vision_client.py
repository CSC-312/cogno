import base64
import os
from typing import Any, Dict, List

from openai import AsyncOpenAI


class VisionClient:
    """Send images to an OpenAI-compatible vision model (Gemini 2.5 Flash Lite)."""

    def __init__(self) -> None:
        base_url = os.getenv("GEMINI_BASE_URL")
        api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_VISION_MODEL")
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    async def summarize_images_async(
        self, images: List[bytes], prompt: str = "Summarize the images succinctly."
    ) -> str:
        if not images:
            return ""

        contents: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        for img in images:
            b64 = base64.b64encode(img).decode("utf-8")
            contents.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                }
            )

        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": contents}],
        )
        return resp.choices[0].message.content.strip()
