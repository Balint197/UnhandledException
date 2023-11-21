import chainlit as cl
from chainlit.prompt import Prompt, PromptMessage
from chainlit.playground.providers.openai import ChatOpenAI
import re, json, requests
from datetime import datetime, timedelta
import ast
from openai import AsyncOpenAI
import re, json, os

from tools import (
    get_conversion_rate_of_currencies,
    get_balance_of_latest_month,
    store_budget,
    calculate_budget,
)


client = AsyncOpenAI(api_key="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")

MAX_ITER = 5  # how many times does it try to use tools in case of failure
budget_json = None

systemPromptBeforeBudget = """Te egy segítőkész és nagyon kedves pénzügyi költségvetési tervező asszisztens vagy. 
A célod az, hogy megkérdezd a felhasználót a pénzügyi helyzetükről, és kérdésekkel derítsd ki róluk a 
következő információkat: havi hitelösszeg, nyaralási költség, havi fizetés. Ha a felhasználó részletekben adja meg ezen 
információkat, győződj meg róla, hogy összeadod azokat, és csak a teljes költséget add vissza eredményként. 
Amint kiderülnek ezek az információk, tárold el azokat. 
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_conversion_rate_of_currencies",
            "description": "Megadja az átváltási arányt két pénznem között, az adott mennyiségben",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency_1": {
                        "type": "string",
                        "description": "Az első pénznem jele",
                    },
                    "currency_2": {
                        "type": "string",
                        "description": "A második pénznem jele",
                    },
                    "amount": {
                        "type": "number",
                        "description": "A váltott pénz mennyisége",
                    },
                },
                "required": ["currency_1", "currency_2", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "store_budget",
            "description": "Eltárolja a költségvetési adatokat",
            "parameters": {
                "type": "object",
                "properties": {
                    "vakacio": {
                        "type": "number",
                        "description": "A vakáció költsége",
                    },
                    "fizetes": {
                        "type": "number",
                        "description": "A havi fizetés",
                    },
                    "torleszto": {
                        "type": "number",
                        "description": "A havi törlesztőrészlet",
                    },
                },
                "required": ["vakacio", "fizetes", "torleszto"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_budget",
            "description": "Kiszámolja a felhasználó költségvetését, és visszaadja a havi fennmaradt költségvetést",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_balance_of_latest_month",
            "description": "A legutóbbi hónapban keletkezett bevételek és kiadások egyenlegét adja meg",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


@cl.action_callback("function_action")
async def on_action(action: cl.Action):
    if action.value == "budget":
        content = "Határozd meg a költségvetési adataimat!"
    elif action.value == "investment":
        content = "Segíts a befektetéseimmel!"
    elif action.value == "exchange":
        content = "Hány forintot ér 500 amerikai dollár?"
    elif action.value == "esg":
        content = "Hogyan tudok úgy spórolni, hogy közben a környezetet is védem? Ha szükséges, kérdezz a személyes válaszadáshoz szükséges információkat tőlem!"
    else:
        await cl.ErrorMessage(content="Érvénytelen gomb").send()
        return

    prev_msg = cl.user_session.get("message_history")  # type: cl.Message
    if prev_msg:
        # await prev_msg.remove_actions()
        print("prev_msg: ")
        prev_msg.append({"role": "user", "content": content})

    msg = cl.Message(content=content)
    await msg.send()
    stream = await client.chat.completions.create(
        messages=prev_msg, stream=True, **settings
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    prev_msg.append({"role": "assistant", "content": msg.content})
    await msg.update()


@cl.on_chat_start
async def start_chat():
    cl.user_session.set(
        "message_history",
        [{"role": "system", "content": systemPromptBeforeBudget}],
    )

    msg = cl.Message(
        content="Szia, a pénzügyeid tervezésében szeretnék segíteni 😊 Először kérlek, mond meg nekem, mennyi a havi hiteltörlesztőd összege!",
    )

    await msg.send()


@cl.on_message
async def main(message: cl.Message):
    global settings, budget_json

    budget_action = cl.Action(
        name="function_action", value="budget", label="💰 Költségvetés számolása"
    )
    investment_action = cl.Action(
        name="function_action", value="investment", label="📈 Befektetési tanácsadás"
    )
    exchange_action = cl.Action(
        name="function_action", value="exchange", label="💱 Valutaváltás"
    )
    esg_action = cl.Action(
        name="function_action", value="esg", label="🌍 Környezettudatos spórolás"
    )
    # actions = []
    actions = [budget_action, investment_action, exchange_action, esg_action]
    # if budget_json != None:
    #    actions = [budget_action, investment_action, exchange_action]

    message_history = cl.user_session.get("message_history")
    message_history.append(
        {
            "role": "user",
            "content": message.content,
        }
    )

    cur_iter = 0

    while cur_iter < MAX_ITER:
        settings = {
            "model": "gpt-4-1106-preview",
            # "model": "gpt-3.5-turbo",
            "temperature": 0.2,
            "max_tokens": 256,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop": ["```"],
            "tools": tools,
            "tool_choice": "auto",
        }

        prompt = Prompt(
            provider="openai-chat",
            messages=[
                PromptMessage(
                    formatted=m["content"], name=m.get("name"), role=m["role"]
                )
                for m in message_history
            ],
            settings=settings,
        )

        response = await client.chat.completions.create(
            messages=message_history, **settings
        )

        message = response.choices[0].message

        prompt.completion = message.content or ""

        root_msg_id = await cl.Message(
            prompt=prompt,
            author=message.role,
            content=prompt.completion,
            actions=actions,
        ).send()

        if not message.tool_calls:
            break

        for tool_call in message.tool_calls:
            if tool_call.type == "function":
                function_name = tool_call.function.name
                arguments = ast.literal_eval(tool_call.function.arguments)
                await cl.Message(
                    author=function_name,
                    content=str(tool_call.function),
                    language="json",
                    parent_id=root_msg_id,
                    actions=[],
                ).send()

                if function_name == "get_conversion_rate_of_currencies":
                    function_response = get_conversion_rate_of_currencies(
                        arguments.get("currency_1"),
                        arguments.get("currency_2"),
                        arguments.get("amount"),
                    )
                if function_name == "store_budget":
                    function_response = store_budget(
                        arguments.get("vakacio"),
                        arguments.get("fizetes"),
                        arguments.get("torleszto"),
                    )
                    budget_json = function_response

                if function_name == "calculate_budget":
                    function_response = calculate_budget(budget_json)

                if function_name == "get_balance_of_latest_month":
                    function_response = get_balance_of_latest_month()

                message_history.append(
                    {
                        "role": "function",
                        "name": function_name,
                        "content": function_response,
                        "tool_call_id": tool_call.id,
                    }
                )

                await cl.Message(
                    author=function_name,
                    content=str(function_response),
                    language="json",
                    parent_id=root_msg_id,
                    actions=[],
                ).send()
        cur_iter += 1
