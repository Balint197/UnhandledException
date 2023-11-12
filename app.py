import chainlit as cl
from chainlit.prompt import Prompt, PromptMessage
from chainlit.playground.providers.openai import ChatOpenAI
from decouple import config
import re, json

from openai import AsyncOpenAI
import os


client = AsyncOpenAI(api_key="")

setupTemplate = """You are a helpful and very kind financial budget planning
 assistant. Your goal is to ask the user for their financial health, 
 and find out the following information about them with successive 
 questions: monthly loan amount, vacation budget, salary. If the user 
 gives this information in partial amounts, make sure to add them up, 
 and only return the total cost for these. As soon as you find out this 
 information, don't write anything else, just return it formatted in 
 the following way, using brackets, etc. Don't use any special symbols 
 for currency, only return the numbers. If the values are unknown, or zero, write 0. 
 Don't attempt to respond with the output before you have asked every question you need
 to find out the desired information. 
 Desired output format: JSON where the keys are: vacation, salary, loan. The values
 should be their respective numerical values. 
"""
#
# You are a personal finance advisor, providing guidance on budgeting, saving, investing, and managing debt. Offer practical tips and strategies to help users achieve their financial goals, while considering their individual circumstances and risk tolerance. Encourage responsible money management and long-term financial planning.

template = """{input}"""


settings = {
    "model": "gpt-4-1106-preview",
    # "model": "gpt-3.5-turbo",
    "temperature": 0.2,
    "max_tokens": 256,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": ["```"],
}

gotBudgetStatus: bool = False
# budgetRegex: re.Pattern = re.compile("\{(?:vacation|salary|loan): \d+(?:, (?:vacation|salary|loan): \d+)*\}")

sysPrompt = Prompt(
    provider=ChatOpenAI.id,
    completion="The openai completion",
    messages=[
        PromptMessage(role="system", template=setupTemplate, formatted=setupTemplate),
    ],
    settings=settings,
    #inputs={"input": message.content},
)


@cl.on_chat_start
async def start():
    await cl.Message(
        content="Welcome! I will be your financial advisor. To start, please give me your monthly loan amount. ",
        prompt=sysPrompt,
    ).send()


@cl.on_message
async def main(message: cl.Message):
    # Create the prompt object for the Prompt Playground

    prompt = Prompt(
        provider=ChatOpenAI.id,
        #completion="The openai completion",
        messages=[
            #            PromptMessage(role="system", template=setupTemplate, formatted=setupTemplate),
            PromptMessage(
                role="user",
                template=template,
                formatted=template.format(input=message.content),
            ),
        ],
        settings=settings,
        inputs={"input": message.content},
    )

    # Prepare the message for streaming
    msg = cl.Message(
        content="",
        language="python",
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

    try:
        budgetInfo = json.loads(prompt.completion)
        gotBudgetStatus = True
        print(budgetInfo)
    except:
        pass

    #    if (budgetRegex.search(prompt.completion)):
    #       print(budgetInfo)

    # Send and close the message stream
    await msg.send()
