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
            {"role": "system",
             "content": "You are playing a game where the humans try to write responses that sound similar to Answers by large language models. Then they will be shown the answers everybody wrote and one answer by a large language model is added, this is your answer. The players vote on which answer was written by you the large language model. Make the answer such that it is possible to guess but not easy. Limit responses to 1 sentence."},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content


if __name__ == '__main__':
    test()
