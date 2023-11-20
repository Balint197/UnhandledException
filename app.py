import chainlit as cl
from chainlit.prompt import Prompt, PromptMessage
from chainlit.playground.providers.openai import ChatOpenAI
import re, json, requests
from datetime import datetime, timedelta

from openai import AsyncOpenAI
import re, json, os

from tools import get_conversion_rate_of_currencies, get_balance_of_latest_month


client = AsyncOpenAI(api_key="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")


systemPromptBeforeBudget = """Te egy segítőkész és nagyon kedves pénzügyi költségvetési tervező asszisztens vagy. 
A célod az, hogy megkérdezd a felhasználót a pénzügyi helyzetükről, és kérdésekkel derítsd ki róluk a 
következő információkat: havi hitelösszeg, nyaralási költség, havi fizetés. Ha a felhasználó részletekben adja meg ezen 
információkat, győződj meg róla, hogy összeadod azokat, és csak a teljes költséget add vissza eredményként. 
Amint kiderülnek ezek az információk, add formázd a megadott módon. Ne használj különleges szimbólumokat a 
pénznemre, csak a számokat add vissza. Ha az értékek nismeretlenek vagy nulla, írj 0-t. Ne próbálj válaszolni 
a kimenettel, mielőtt minden olyan kérdést feltennél, amire szükséged van a kívánt információk megszerzéséhez.
Kívánt kimeneti formátum: JSON, ahol a kulcsok a következők: vakáció, nyaralás, hitel. 
Az értékek legyenek a megfelelő számszerű értékek. 
Miután visszaadtad a kimenetet, a felhasználó kérdéseire egy pénzügyi költségvetési tervező asszisztens szerepében válaszolj.
Amennyiben szükséges, használd a rendelkezésedre álló eszközöket. 
"""


gotBudgetStatus: bool = False
# budgetRegex: re.Pattern = re.compile("\{(?:vacation|salary|loan): \d+(?:, (?:vacation|salary|loan): \d+)*\}")
budget_json = None




tools = [
    {
        "type": "function",
        "function": {
            "name": "get_conversion_rate_of_currencies",
            "description": "Megadja az átváltási arányt két pénznem között",
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
                },
                "required": ["currency_1", "currency_2"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_balance_of_latest_month",
            "description": "A legutóbbi hónapban keletkezett bevételek és kiadások egyenlegét adja meg",
            "parameters": {},
        },
    },
]


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
    global gotBudgetStatus
    message_history = cl.user_session.get("message_history")
    message_history.append(
        {
            "role": "user",
            "content": message.content,
        }
    )

    msg = cl.Message(content="")
    await msg.send()

    stream = await client.chat.completions.create(
        messages=message_history, stream=True, **settings
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()

    if extract_json_from_string(msg.content) != None:
        budget_json = extract_json_from_string(msg.content)
        gotBudgetStatus = True


def extract_json_from_string(input_string):
    # Find the start and end indices of the JSON object
    start_index = input_string.find("{")
    end_index = input_string.rfind("}")

    # Check if both start and end indices are found
    if start_index != -1 and end_index != -1:
        # Extract the JSON object substring
        json_str = input_string[start_index : end_index + 1]

        try:
            # Parse the JSON object
            json_data = json.loads(json_str)
            return json_data
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
