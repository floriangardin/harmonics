from .prompts import SPCECIAL_PROMPT_EXAMPLE, SYSTEM_PROMPT, SYSTEM_PROMPT_CORRECT
import openai


def get_between_start_and_end(text: str, start: str, end: str) -> str:
    return text.split(start)[1].split(end)[0]


def compose_rntxt(
    prompt: str = SPCECIAL_PROMPT_EXAMPLE,
    model: str = "gpt-4o",
    client: openai.OpenAI = None,
) -> str:

    if client is None:
        client = openai.OpenAI()
    print(SYSTEM_PROMPT)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": SYSTEM_PROMPT + "\n\n" + prompt},
        ],
        response_format={"type": "text"},
    )
    return response.choices[0].message.content


def correct_rntxt(
    rntxt: str, model: str = "gpt-4o", client: openai.OpenAI = None
) -> str:
    if client is None:
        client = openai.OpenAI()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": SYSTEM_PROMPT_CORRECT + "\nRNTXT TO CORRECT : \n" + rntxt,
            },
        ],
        response_format={"type": "text"},
    )
    return response.choices[0].message.content
