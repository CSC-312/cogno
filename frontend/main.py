import io
import logging
import os
import wave
from typing import Any, Dict, Optional

import chainlit as cl
import numpy as np
from ollama import AsyncClient
from openai import AsyncOpenAI
from prompts import GROK_PROMPT

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ollama = AsyncClient(
    host=os.getenv("OLLAMA_BASE_URL"),
    headers={"Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"},
)

whisper = AsyncOpenAI(
    base_url=os.getenv("GROQ_BASE_URL"), api_key=os.getenv("GROQ_API_KEY")
)

groq = AsyncOpenAI(
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
            message="Give me directions to UWC",
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
        model=os.getenv("GROQ_WHISPER_MODEL"), file=audio_file
    )

    return response.text


async def process_audio():
    audio_chunks = cl.user_session.get("audio_chunks")
    if not audio_chunks:
        return
    concatenated = np.concatenate(audio_chunks)
    sample_rate = 24000
    duration = concatenated.shape[0] / float(sample_rate)
    if duration <= 1.71:
        cl.user_session.set("audio_chunks", [])
        print("The audio is too short, please try again.")
        logger.warning("The audio is too short, please try again.")
        return

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)  # mono
        wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
        wav_file.setframerate(sample_rate)  # 24 kHz PCM
        wav_file.writeframes(concatenated.tobytes())

    wav_buffer.seek(0)
    cl.user_session.set("audio_chunks", [])

    audio_buffer = wav_buffer.getvalue()

    whisper_input = ("audio.wav", audio_buffer, "audio/wav")
    transcription = await audio(whisper_input)
    logger.info(f"Command: {cl.user_session.get('selected_command')}")

    selected_command = cl.user_session.get("selected_command")

    user_message = cl.Message(
        content=transcription,
        author="User",
        type="user_message",
        command=selected_command,
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
                "icon": "scan-search",
                "button": True,
                "persistent": True,
            }
        ]
    )


@cl.on_message
async def on_message(msg: cl.Message):
    if not cl.user_session.get("is_thread_renamed", False):
        thread_name_response = await groq.chat.completions.create(
            model=os.getenv("GROQ_MODEL"),
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize this query in MAX 8 words for a chat thread name: `{msg.content}`",
                }
            ],
            temperature=0.8,
            max_completion_tokens=50,
            top_p=1,
            reasoning_effort="low",
            stream=False,
            stop=None,
        )
        thread_name = thread_name_response.choices[0].message.content.strip()

        await cl.context.emitter.init_thread(thread_name)
        cl.user_session.set("is_thread_renamed", True)

    if msg.command == "search":
        msg.content = f"/hybrid {msg.content}"
    else:
        msg.content = f"/bypass {msg.content}"

    logger.debug(f"Command: {msg.command}, Content: {msg.content}")
    messages = cl.user_session.get("chat_history", [])
    messages.append({"role": "user", "content": msg.content})

    stream = await ollama.chat(
        model=os.getenv("OLLAMA_MODEL"),
        messages=messages,
        stream=True,
    )
    if msg.command == "search":
        full_response = ""
        async for chunk in stream:
            content = chunk.get("message", {}).get("content")
            if content:
                full_response += content

        cleaned_response_stream = await groq.chat.completions.create(
            model=os.getenv("GROQ_MODEL"),
            messages=[
                {"role": "system", "content": str(GROK_PROMPT)},
                {
                    "role": "user",
                    "content": full_response,
                },
            ],
            temperature=0,
            stream=True,
        )
        cleaned_response = ""
        async for chunk in cleaned_response_stream:
            content = chunk.choices[0].delta.content
            if content:
                cleaned_response += content

        await cl.Message(content=cleaned_response).send()
    else:
        final_answer_content = ""
        final_answer = cl.Message(content="")
        async for chunk in stream:
            content = chunk.get("message", {}).get("content")
            if content:
                final_answer_content += content
                await final_answer.stream_token(content)
        await final_answer.send()

    chat_history = cl.user_session.get("chat_history", [])
    chat_history.append({"role": "user", "content": msg.content})
    if msg.command == "search":
        chat_history.append({"role": "assistant", "content": cleaned_response})
    else:
        chat_history.append({"role": "assistant", "content": final_answer_content})
    cl.user_session.set("chat_history", chat_history)
