import os
import io
import wave
from datetime import datetime
from typing import Any, Dict, Optional

import numpy as np
import chainlit as cl
from ollama import AsyncClient
from openai import AsyncOpenAI

ollama = AsyncClient(
    host=os.getenv("OLLAMA_BASE_URL"),
    headers={"Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"},
)

whisper = AsyncOpenAI(
    base_url=os.getenv("GROQ_BASE_URL"), api_key=os.getenv("GROQ_API_KEY")
)


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    return default_user


@cl.on_shared_thread_view
async def on_shared_thread_view(thread: Dict[str, Any], current_user: cl.User) -> bool:
    return True


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Apply",
            message="How do I apply to the University of the Western Cape?",
            icon="public/square-academic-cap-svgrepo-com.svg",
            command="search",
        ),
        cl.Starter(
            label="Eat",
            message="How where can I find places to eat on campus?",
            icon="public/donut-bitten-svgrepo-com.svg",
            command="search",
        ),
        cl.Starter(
            label="Find",
            message="Where is the Life Sciences Building on campus?",
            icon="public/map-point-school-svgrepo-com.svg",
            command="search",
        ),
        cl.Starter(
            label="Call",
            message="What is the phone number of residential services?",
            icon="public/call-chat-svgrepo-com.svg",
            command="search",
        ),
        cl.Starter(
            label="Sports",
            message="What sports are offered at the University of the Western Cape?",
            icon="public/basketball-svgrepo-com.svg",
            command="search",
        ),
    ]


@cl.step(type="tool", show_input=False)
async def audio(audio_file):
    response = await whisper.audio.transcriptions.create(
        model=os.getenv("GROQ_MODEL"), file=audio_file
    )

    return response.text


async def process_audio():
    if audio_chunks := cl.user_session.get("audio_chunks"):
        concatenated = np.concatenate(list(audio_chunks))
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
            wav_file.setframerate(24000)  # sample rate (24kHz PCM)
            wav_file.writeframes(concatenated.tobytes())

        wav_buffer.seek(0)

        cl.user_session.set("audio_chunks", [])

    frames = wav_file.getnframes()
    rate = wav_file.getframerate()

    duration = frames / float(rate)
    if duration <= 1.71:
        print("The audio is too short, please try again.")
        return

    audio_buffer = wav_buffer.getvalue()


    whisper_input = ("audio.wav", audio_buffer, "audio/wav")
    transcription = await audio(whisper_input)

    user_message = cl.Message(
        content=transcription,
        author="User",
        type="user_message",
    )
    await user_message.send()

    await on_message(user_message)


@cl.on_audio_start
async def on_audio_start():
    cl.user_session.set("audio_chunks", [])
    return True


@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    audio_chunks = cl.user_session.get("audio_chunks")

    if audio_chunks is not None:
        audio_chunk = np.frombuffer(chunk.data, dtype=np.int16)
        audio_chunks.append(audio_chunk)


@cl.on_audio_end
async def on_audio_end():
    await process_audio()
    return True


@cl.on_chat_start
async def start():
    await cl.context.emitter.set_commands(
        [
            {
                "id": "search",
                "name": "Search",
                "description": "Search for information about the University of the Western Cape",
                "icon": "folder-search",
                "button": True,
                "persistent": True,
            }
        ]
    )


@cl.on_message
async def on_message(msg: cl.Message):
    if msg.command != "search":
        msg.content = f"/bypass {msg.content}"
    stream = await ollama.chat(
        model=os.getenv("OLLAMA_MODEL"),
        messages=[
            {
                "role": "system",
                "content": f"""You are Cogno, a helpful assistant for the University of the Western Cape, a South African University.
                               Today is {datetime.now()}. Ignore use of /bypass, it is just internal configuration to talk to you without using the UWC Knowledge Base as context, don't mention it to the user.
                               Do not include citations or references in your responses under any circumstances, as it is too verbose. Your answers must be structured neatly. Do not make reference to this instruction or knowledge base.
                               Your aim to to help with University of the Western Cape related queries.

                            """,
            },
            *cl.chat_context.to_openai(),
        ],
        stream=True,
    )
    final_answer = cl.Message(content="")

    async for chunk in stream:
        content = chunk["message"]["content"]

        await final_answer.stream_token(content)
    await final_answer.send()
