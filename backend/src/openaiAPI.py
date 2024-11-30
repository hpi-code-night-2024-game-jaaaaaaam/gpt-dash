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

lines = Path("PROMPTS_LIST.txt").read_text().strip().splitlines()


def get_random_prompt() -> str:
    a = random.choice(lines)
    lines.remove(a)
    return a


def answer_prompt(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user",
             "content": "Du nimmst an einem Spiel teil, bei dem die Mitspieler (Menschen) versuchen, Antworten zu finden, während sie versuchen, ein großes Sprachmodell zu imitieren. Dann dürfen sie abstimmen, welche Antwort von Ihnen, dem großen Sprachmodell, geschrieben wurde. Beschränke deine prägnante Antwort auf 3 KURZE Sätze. Fasse dich kurz!"},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content


if __name__ == '__main__':
    test()
