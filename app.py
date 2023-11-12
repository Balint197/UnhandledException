import chainlit as cl
from chainlit.prompt import Prompt, PromptMessage
from chainlit.playground.providers.openai import ChatOpenAI
from decouple import config


from openai import AsyncOpenAI
import os


client = AsyncOpenAI(api_key="")


template = """SQL tables (and columns):
* Customers(customer_id, signup_date)
* Streaming(customer_id, video_id, watch_date, watch_minutes)

A well-written SQL query that {input}:
```"""


settings = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.8,
    "max_tokens": 500,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": ["```"],
}



@cl.on_message
async def main(message: cl.Message):
    # Create the prompt object for the Prompt Playground
    prompt = Prompt(
        provider=ChatOpenAI.id,
        messages=[
            PromptMessage(
                role="user",
                template=template,
                formatted=template.format(input=message.content)
            )
        ],
        settings=settings,
        inputs={"input": message.content},
    )

    # Prepare the message for streaming
    msg = cl.Message(
        content="",
        language="sql",
    )

    # Call OpenAI

    stream = await client.chat.completions.create(
        messages=[m.to_openai() for m in prompt.messages], stream=True, **settings
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    # Update the prompt object with the completion
    prompt.completion = msg.content
    msg.prompt = prompt

    # Send and close the message stream
    await msg.send()
