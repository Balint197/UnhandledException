import chainlit as cl
from chainlit.prompt import Prompt, PromptMessage
from chainlit.playground.providers.openai import ChatOpenAI
import re, json, requests

from openai import AsyncOpenAI
import re, json, os


api_key = os.environ.get("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)


# monthly loan amount, vacation budget, salary.

systemPromptBeforeBudget = """You are a helpful and very kind financial budget planning
 assistant. Your goal is to ask the user for their financial health, 
 and find out the following information about them with successive questions: 
 monthly loan amount, vacation budget.
 If the user gives this information in partial amounts, make sure to add them up, 
 and only return the total cost for these. As soon as you find out this 
 information, don't write anything else, just return it formatted in 
 the following way, using brackets, etc. Don't use any special symbols 
 for currency, only return the numbers. If the values are unknown, or zero, write 0. 
 Don't attempt to respond with the output before you have asked every question you need
 to find out the desired information. 
 Desired output format: JSON where the keys are: vacation, salary, loan. The values
 should be their respective numerical values. 
"""

systemPromptAfterBudget = """
You are a personal finance advisor, providing guidance on budgeting, saving, 
investing, and managing debt. Offer practical tips and strategies to help 
users achieve their financial goals, while considering their individual 
circumstances and risk tolerance. Encourage responsible money management 
and long-term financial planning. The user has given the following information 
about their monetary budget situation: vacation: {{budget_json.vacation}}, 
salary: {{budget_json.salary}}, loan: {{budget_json.loan}}.
"""


gotBudgetStatus: bool = False
# budgetRegex: re.Pattern = re.compile("\{(?:vacation|salary|loan): \d+(?:, (?:vacation|salary|loan): \d+)*\}")
session_names = ["before_setup", "after_setup"]
budget_json = None





# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(location, unit):
    """Get the current weather in a given location"""
    unit = unit or "Farenheit"
    weather_info = {
        "location": location,
        "temperature": "72",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }

    return json.dumps(weather_info)

def get_conversion_rate_of_currencies(currency_1, currency_2):
    """Get the current conversion rate between two currencies"""
    
    api_key = "API KEY"  #your https://currencyapi.com/docs/convert API key
    url = "https://api.currencyapi.com/v3/latest"
    headers = {
        'apikey': api_key,
        'value' : '1',
        'base_currency' : currency_1,
        'currencies' : currency_2
    }
    try:
        response = requests.request("GET", url, headers=headers)
        val = response.json()['data'][currency_2]['value']
        weather_info = {
            "Currency 1": currency_1,
            "Currency 2": currency_2,
            "Conversion rate": str(val),
        }
    except Exception as e:
        print(e)
        weather_info = {
            "Currency 1": currency_1,
            "Currency 2": currency_2,
            "Conversion rate": "Unknown",
        }

    return json.dumps(weather_info)


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_conversion_rate_of_currencies",
            "description": "Get the current conversion rate between two currencies",
            "parameters": {
                "type": "object",
                "properties": {
                    "currency_1": {
                        "type": "string",
                        "description": "The code of the first currency",
                    },
                    "currency_2": {
                        "type": "string",
                        "description": "The code of the second currency",
                    },
                },
                "required": ["currency_1", "currency_2"],
            },
        },
    }
]

settings = {
    "model": "gpt-4",
    #"model": "gpt-4-1106-preview",
    #"model": "gpt-3.5-turbo",
    "temperature": 0.2,
    "max_tokens": 256,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": ["```"],
    "tools": tools,
    "tool_choice": "auto",
}


@cl.action_callback("confirm_action")
async def on_action(action: cl.Action):
    if action.value == "ok":
        content = "Confirmed!"
    elif action.value == "not_ok":
        content = "Rejected!"
    else:
        await cl.ErrorMessage(content="Invalid action").send()
        return

    prev_msg = cl.user_session.get("msg")  # type: cl.Message
    if prev_msg:
        await prev_msg.remove_actions()
        cl.user_session.set("msg", None)

    await cl.Message(content=content).send()



@cl.on_chat_start
async def start_chat():

    # approve_action = cl.Action(name="confirm_action", value="ok", label="Confirm")
    # reject_action = cl.Action(name="confirm_action", value="not_ok", label="Reject")
    # actions = [approve_action, reject_action]

    msg = cl.Message(
        content="Hi, I will help you plan your finances. First, please let me know your monthly loan payment amount!",
        #actions=actions,
    )

    cl.user_session.set("msg", "Hi, I will help you plan your finances. First, please let me know your monthly loan payment amount!")

    await msg.send()





    # cl.user_session.set(
    #     session_names[0],
    #     [
    #         {"role": "system", "content": systemPromptBeforeBudget}
    #     ],
    # )


@cl.on_message
async def main(message: cl.Message):
    global gotBudgetStatus
    if gotBudgetStatus == False:
        message_history = cl.user_session.get(session_names[0])
        message_history.append({"role": "assistant", "content": "Hi, I will help you plan your finances. First, please let me know your monthly loan payment amount!"})
        message_history.append({"role": "user", "content": message.content})

        approve_action = cl.Action(name="confirm_action", value="ok", label="Confirm")
        reject_action = cl.Action(name="confirm_action", value="not_ok", label="Reject")
        actions = [approve_action, reject_action]

        msg = cl.Message(
            content="", 
            actions=actions)
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
            print(systemPromptAfterBudget)
            print(systemPromptAfterBudget.format(budget_json=budget_json))
            message_history.append({"role": "system", "content": systemPromptAfterBudget})


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
