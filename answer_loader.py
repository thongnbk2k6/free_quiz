import pandas as pd


def load_answers(path):
    df = pd.read_csv(path, encoding='utf-8-sig')

    answers = {}

    for _, row in df.iterrows():
        question = str(row["question"]).strip()
        answer = str(row["answer"]).strip()

        answers[question] = answer

    return answers
