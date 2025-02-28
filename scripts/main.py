import os

import numpy
import pandas
from tqdm import tqdm
from uuid import uuid4
from typer import Typer
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel


class Output(BaseModel):
    datasets: list[str]
    algorithms: list[str]
    application: str  # Primary application field (e.g., cancer, medical, ecommerce)


def get_prediction(text: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""
    Analyze the following abstract and extract the following details ONLY if the abstract is related to recommendation systems:

    1. datasets: List any datasets referenced or used.
    2. algorithms: List any algorithms or methods mentioned (e.g., collaborative filtering, matrix decomposition, etc.).
    3. application: Extract the primary practical application context in which the recommendation system is applied. This should reflect the real-world domain (for example, "medical", "cancer diagnosis", "ecommerce", "entertainment", "social media", or "financial services"). If multiple application domains are present, select the one that is most prominently featured or central to the study.

    If the abstract is not related to recommendation systems, please return an empty JSON object (i.e {{}}).

    Please provide the output in JSON format with the keys: datasets, algorithms, application.

    Abstract:
    {text}
    """

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format=Output,
    )
    return response.choices[0].message.parsed


def get_processed_dois() -> list[str]:
    paths = [
        os.path.join("data/predictions", path)
        for path in os.listdir("data/predictions")
        if path.endswith(".csv") and path.startswith("predictions")
    ]
    dois = list()
    for path in paths:
        df = pandas.read_csv(path)
        dois.extend(df["DOI"].tolist())
    return dois


load_dotenv()
app = Typer()


@app.command(name="predict")
def predict():
    data = pandas.read_csv("data/RS_Scopus - RS_Scopus.csv")
    # Clean DOI column: strip whitespace and replace literal double quotes with an empty string
    data["DOI"] = data["DOI"].str.strip().replace('""', "")
    # Remove cases where DOI is empty
    data = data[data["DOI"] != ""]
    dois = get_processed_dois()
    data = data[~data["DOI"].isin(dois)]

    print(f"to process {len(data)} -- already processed: {len(dois)}")

    batch_size = 10
    batches = numpy.array_split(data, len(data) // batch_size)
    for batch in tqdm(batches, total=len(batches)):
        batch["prediction"] = batch["Abstract"].apply(get_prediction)
        batch["datasets"] = batch["prediction"].apply(lambda x: x.datasets)
        batch["algorithms"] = batch["prediction"].apply(lambda x: x.algorithms)
        batch["application"] = batch["prediction"].apply(lambda x: x.application)
        batch[["DOI", "datasets", "algorithms", "application"]].to_csv(
            f"data/predictions/predictions_{uuid4()}.csv", index=False
        )


@app.command(name="create")
def create():
    data = pandas.read_csv("data/RS_Scopus - RS_Scopus.csv")
    # Clean DOI column: strip whitespace and replace literal double quotes with an empty string
    data = data[(data["DOI"] != "") & (data["DOI"].notna())]
    processed = pandas.concat(
        [
            pandas.read_csv(os.path.join("data/predictions", path))
            for path in os.listdir("data/predictions")
            if path.endswith(".csv") and path.startswith("predictions")
        ]
    )
    # Clean DOI column in processed dataframe similarly
    processed = processed[(processed["DOI"] != "") & (processed["DOI"].notna())]
    data = pandas.merge(left=data, right=processed, on="DOI", how="inner")
    data.to_csv("data/RS_Scopus - RS_Scopus_processed.csv", index=False)


if __name__ == "__main__":
    app()
