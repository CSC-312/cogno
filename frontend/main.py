import chainlit as cl
from typing import Dict, Optional
from ollama import AsyncClient

ollama = AsyncClient(host="http://localhost:11434")


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    return default_user


# Declare Chat Profile
@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="UWC_Chat",
            markdown_description="Chatbot with **UWC** brand colors",
        )
    ]


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Help",
            message="Where can i make an affidavit?",
            icon="public/faq.svg",
        ),
        cl.Starter(
            label="Give",
            message="Where can I donate food to other students?",
            icon="public/honest.svg",
        ),
        cl.Starter(
            label="Know", message="Who is the vice chancellor?", icon="public/staff.svg"
        ),
        cl.Starter(
            label="Contact",
            message="How do i get hold of residencially services?",
            icon="public/contact.svg",
        ),
    ]


@cl.on_message
async def on_message(msg: cl.Message):
    stream = await ollama.chat(
        model="qwen3:0.6b",
        messages=[
            {"role": "system", "content": "You are an helpful assistant"},
            *cl.chat_context.to_openai(),
        ],
        stream=True,
        think=False,
    )
    final_answer = cl.Message(content="")

    async for chunk in stream:
        content = chunk["message"]["content"]

        await final_answer.stream_token(content)

    await final_answer.send()
