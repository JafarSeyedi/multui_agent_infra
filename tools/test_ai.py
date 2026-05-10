# from openai import OpenAI

# client = OpenAI(base_url="https://api.gapgpt.app/v1", api_key="sk-z84HyyfxX0tTara06vfnC8JxLA4bgxLgVnwfJHPoRX5ESF9U")

# response = client.chat.completions.create(
#     model="gpt-chat-5.3-latest",
#     messages=[{"role": "user", "content": "سلام!"}]
# )
# print(response.choices[0].message.content)

from openai import OpenAI

# ایجاد یک نمونه از کلاینت با کلید API خود
client = OpenAI(base_url='https://api.gapgpt.app/v1', api_key='sk-z84HyyfxX0tTara06vfnC8JxLA4bgxLgVnwfJHPoRX5ESF9U')

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "سلام!"}
    ]
)

print(response.choices[0].message.content)
