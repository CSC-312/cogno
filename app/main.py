import chainlit as cl
from ollama import AsyncClient
import time

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
    start = time.time()
    stream = await ollama.chat(
        model="qwen3:0.6b",
        messages=[
            {"role": "system", "content": "You are an helpful assistant"},
            *cl.chat_context.to_openai(),
        ],
        stream=True,
    )

    thinking = False

    # Streaming the thinking
    async with cl.Step(name="Thinking") as thinking_step:
        final_answer = cl.Message(content="")

        async for chunk in stream:
            content = chunk["message"]["content"]
            if content == "<think>":
                thinking = True
                continue

            if content == "</think>":
                thinking = False
                thought_for = round(time.time() - start)
                thinking_step.name = f"Thought for {thought_for}s"
                await thinking_step.update()
                continue

            if thinking:
                await thinking_step.stream_token(content)
            else:
                await final_answer.stream_token(content)

    await final_answer.send()
