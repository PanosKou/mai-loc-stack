import logging
import os
import uuid
from pathlib import Path

import httpx
from fastmcp import FastMCP

from .base import AgentHubSkill


log = logging.getLogger("mcp-agent-hub.skills.tts")


class TtsSkill(AgentHubSkill):
    name = "tts"
    tool_names = ("tts_generate_audio",)

    def __init__(self) -> None:
        self.piper_tts_url = os.getenv("PIPER_TTS_URL", "http://127.0.0.1:8095").rstrip("/")
        self.tts_output_dir = Path(os.getenv("TTS_OUTPUT_DIR", "/tmp"))

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool
        async def tts_generate_audio(
            text: str,
            voice: str = "",
        ) -> str:
            """
            Generate local speech audio from text using Piper TTS.

            Args:
                text: Text to convert to speech.
                voice: Optional Piper voice name. Leave empty to use the default Piper voice.

            Returns:
                Local WAV file path.
            """

            safe_text = (text or "").strip()
            safe_voice = (voice or "").strip()

            if not safe_text:
                return "No text provided."

            if len(safe_text) > 2000:
                return "Text is too long. Maximum allowed length is 2000 characters."

            self.tts_output_dir.mkdir(parents=True, exist_ok=True)
            output_file = self.tts_output_dir / f"tts-{uuid.uuid4().hex}.wav"

            payload = {"text": safe_text}
            if safe_voice:
                payload["voice"] = safe_voice

            log.info("tts_generate_audio called chars=%s voice=%r", len(safe_text), safe_voice)

            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        self.piper_tts_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )

                response.raise_for_status()

                audio = response.content
                if not audio.startswith(b"RIFF"):
                    return (
                        "Piper returned a non-WAV response. "
                        f"HTTP status={response.status_code}, first_bytes={audio[:80]!r}"
                    )

                output_file.write_bytes(audio)
                return f"TTS audio generated: {output_file}"

            except Exception as exc:
                log.exception("tts_generate_audio failed")
                return f"tts_generate_audio failed: {type(exc).__name__}: {exc}"
