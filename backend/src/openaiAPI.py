from dotenv import load_dotenv
from openai import OpenAI
import os
from pathlib import Path
import random

load_dotenv()
api_key = os.getenv("MY_VERY_SECRET_KEY")

client = OpenAI(
    api_key=api_key
)


def test():
    print(answer_prompt(get_random_prompt()))


# lines = Path("file.txt").read_text().strip().splitlines()
# randomPrompt = random.choice(lines)

def get_random_prompt() -> str:
    lines = Path("PROMPTS_LIST.txt").read_text().strip().splitlines()
    return random.choice(lines)


def answer_prompt(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user",
             "content": "You are participating in a game where the humans try to come up with responses while trying to imitate a Large Language Model. Then they get to vote which answer was written by you, the Large Language Model. Limit your brief response to 3 SHORT sentences. Make your response short!"},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content


if __name__ == '__main__':
    test()
