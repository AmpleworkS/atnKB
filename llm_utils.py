from openai import OpenAI

client = OpenAI()

class LLM:
    def invoke(self, messages, tools=None):
        response = client.chat.completions.create(
            model="gpt-4o",   # or gpt-4.1 / gpt-3.5
            messages=messages,
            tools=tools if tools else None
        )
        return response.choices[0].message

llm = LLM()
