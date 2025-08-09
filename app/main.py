import chainlit as cl
from ollama import AsyncClient

# Initialize Ollama client
ollama = AsyncClient(host="http://localhost:11434")


# Declare Chat Profile
@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="UWC_Chat",
            markdown_description="Chatbot with **UWC** brand colors",
        )
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
