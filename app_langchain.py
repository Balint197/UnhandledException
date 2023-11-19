from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
import chainlit as cl

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
 should be their respective numerical values. Don't ask the user to input the information
 using this format. 
"""

@cl.on_chat_start
async def on_chat_start():
    model = ChatOpenAI(streaming=True)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                systemPromptBeforeBudget,
            ),
            ("human", "{question}"),
        ]
    )
    runnable = prompt | model | StrOutputParser()
    cl.user_session.set("runnable", runnable)


@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable

    msg = cl.Message(content="")

    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await msg.stream_token(chunk)

    await msg.send()
