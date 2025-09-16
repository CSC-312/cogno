import os
from datetime import datetime
from typing import Any, Dict, Optional

import chainlit as cl
from ollama import AsyncClient

ollama = AsyncClient(
    host=os.getenv("OLLAMA_BASE_URL"),
    headers={"Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"},
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
    # Deny if user not on same team
    owner_team = thread.get("metadata", {}).get("team")
    user_team = current_user.metadata.get("team")
    if owner_team != user_team:
        return False

    shared_at = thread.get("metadata", {}).get("shared_at")
    if shared_at:
        thread["steps"] = [
            s for s in thread.get("steps", []) if s.get("created_at") <= shared_at
        ]

    for step in thread.get("steps", []):
        if step.get("metadata", {}).get("sensitive"):
            step["output"] = "[REDACTED]"

    return True


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Help",
            message="How do I apply to UWC, using NSFAS",
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
            message="How do i get hold of residential services?",
            icon="public/contact.svg",
        ),
    ]


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
                               Do not include citations or references in your responses under any circumstances, as it is too verbose.
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
