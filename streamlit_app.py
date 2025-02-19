import os
import ast
from collections import Counter

import pandas
import streamlit
import plotly.express as px
from wordcloud import WordCloud
from sentence_transformers import SentenceTransformer, util

import helpers.password

if helpers.password.is_password_ok() is False:
    streamlit.stop()

streamlit.title("RecSys in Scopus")


def clean_application(text: str) -> str:
    patterns = [
        "recommendation systems",
        "recommendation system",
        "recommender systems",
        "recommendation",
        "recommendations",
        "recommender",
    ]
    for pattern in patterns:
        text = text.replace(pattern, "").strip()
    return text


def clean_algorithm(text: str) -> str:
    patterns = [
        "algorithm",
        "algorithms",
    ]
    for pattern in patterns:
        text = text.replace(pattern, "").strip()
    return text

@streamlit.cache_data()
def get_data() -> pandas.DataFrame:
    root_path = "data/predictions/"
    data = pandas.concat(
        objs=[
            pandas.read_csv(os.path.join(root_path, path))
            for path in os.listdir(root_path)
        ]
    )
    data["datasets"] = data["datasets"].apply(
        lambda x: ast.literal_eval(str(x).lower())
    )
    data["algorithms"] = data["algorithms"].apply(
        lambda x: ast.literal_eval(str(x).lower())
    )
    data["application"] = data["application"].apply(
        lambda x: clean_application(str(x).lower())
    )
    data = data.explode(column="algorithms")
    data.rename(columns={"algorithms": "algorithm"}, inplace=True)
    data = data[["DOI", "algorithm", "application"]].dropna()
    data = data[(~data["application"].isna()) & (~data["algorithm"].isna())]
    data["algorithm"] = data["algorithm"].apply(
        lambda x: clean_algorithm(str(x).lower())
    )
    return data


@streamlit.cache_data()
def get_applications_groups(data: pandas.DataFrame) -> pandas.DataFrame:
    data = data["application"].unique().tolist()
    model = SentenceTransformer(
        model_name_or_path="sentence-transformers/all-MiniLM-L6-v2"
    )
    embeddings = model.encode(
        sentences=data, convert_to_numpy=True, show_progress_bar=True
    )
    clusters = util.community_detection(
        embeddings, min_community_size=1, threshold=0.75
    )
    output = list()
    for i, cluster in enumerate(clusters):
        applications = [data[j] for j in cluster]
        try:
            name = Counter([y for x in applications for y in x.split()]).most_common(1)[0][0]
        except Exception as e:
            name = applications[0]
        output.append(
            {
                "size": len(cluster),
                "application_group_id": i,
                "application_group_name": name,
                "applications": applications,
            }
        )
    return pandas.DataFrame(data=output).sort_values(by="size", ascending=False)


@streamlit.cache_data()
def get_algorithms_groups(data: pandas.DataFrame) -> pandas.DataFrame:
    data = data["algorithm"].unique().tolist()
    model = SentenceTransformer(
        model_name_or_path="sentence-transformers/all-MiniLM-L6-v2"
    )
    embeddings = model.encode(
        sentences=data, convert_to_numpy=True, show_progress_bar=True
    )
    clusters = util.community_detection(
        embeddings, min_community_size=1, threshold=0.75
    )
    output = list()
    for i, cluster in enumerate(clusters):
        output.append(
            {
                "size": len(cluster),
                "algorithm_group_id": i,
                "algorithm_group_name": data[cluster[0]],
                "algorithms": [data[j] for j in cluster],
            }
        )
    return pandas.DataFrame(data=output).sort_values(by="size", ascending=False)


@streamlit.cache_data()
def get_groups(data: pandas.DataFrame) -> tuple[pandas.DataFrame, pandas.DataFrame]:
    return (
        get_applications_groups(data=data),
        get_algorithms_groups(data=data),
    )


@streamlit.cache_data()
def set_application_groups(
    data: pandas.DataFrame, app_groups: pandas.DataFrame, alg_groups: pandas.DataFrame
) -> pandas.DataFrame:
    output = data.copy()

    app_groups = app_groups.explode("applications").rename(
        columns={"applications": "application"}
    )
    output = pandas.merge(
        how="left",
        left=output,
        on="application",
        right=app_groups[
            ["application_group_id", "application_group_name", "application"]
        ],
    )

    alg_groups = alg_groups.explode("algorithms").rename(
        columns={"algorithms": "algorithm"}
    )
    output = pandas.merge(
        how="left",
        left=output,
        on="algorithm",
        right=alg_groups[["algorithm_group_id", "algorithm_group_name", "algorithm"]],
    )
    return output


### HEATMAP


# @streamlit.cache_data()
def get_algorithm_field_relationships(
    data: pandas.DataFrame, app_groups: pandas.DataFrame, alg_groups: pandas.DataFrame
) -> pandas.DataFrame:
    df = data.copy()
    df = (
        df.groupby(["algorithm_group_name", "application_group_name"])
        .size()
        .reset_index(name="count")
    )
    df = df.sort_values("count", ascending=False)
    return df


def set_algorithm_field_heatmap(data: pandas.DataFrame, top_n: int) -> None:
    pivot = data.pivot(
        index="algorithm_group_name", columns="application_group_name", values="count"
    ).fillna(0)

    fig = px.imshow(
        pivot,
        text_auto=True,
        aspect="auto",
        labels={"color": "Count"},
        color_continuous_scale="Viridis",
        title=f"Algorithm vs Field Heatmap (Top {top_n} Occurrences)",
    )
    streamlit.plotly_chart(fig)


def set_heatmap_and_metrics(data: pandas.DataFrame):
    top_n = streamlit.selectbox(
        "Select number of top occurrences to display",
        options=data["count"].unique(),
        index=len(data["count"].unique()) // 2,
    )

    data = data[data["count"] >= top_n]

    columns = streamlit.columns(2)
    columns[0].metric(
        "Number of Algorithms", len(data["algorithm_group_name"].unique())
    )
    columns[1].metric(
        "Number of Applications", len(data["application_group_name"].unique())
    )
    set_algorithm_field_heatmap(data=data, top_n=top_n)


### Fields groupers

data = get_data()
app_groups, alg_groups = get_groups(data=data)

data = set_application_groups(data=data, app_groups=app_groups, alg_groups=alg_groups)

relations = get_algorithm_field_relationships(
    data=data, app_groups=app_groups, alg_groups=alg_groups
)
set_heatmap_and_metrics(data=relations)


application_group_name = streamlit.selectbox(
    label="choose an application",
    options=app_groups["application_group_name"].unique().tolist()
)

application_group_data = data[data["application_group_name"] == application_group_name]


streamlit.markdown(f"## {application_group_name}")
frequencies = {x: 1 for x in application_group_data["application"].value_counts().to_dict()}
wordcloud = WordCloud(width=800, height=400, background_color="#0D1118", colormap="magma").generate_from_frequencies(
    frequencies
)
streamlit.image(wordcloud.to_image(), width=1000)

streamlit.markdown("## Algorithms")
frequencies = application_group_data["algorithm"].value_counts().to_dict()
wordcloud = WordCloud(width=800, height=400, background_color="#0D1118", colormap="magma").generate_from_frequencies(
    frequencies
)
streamlit.image(wordcloud.to_image(), width=1000)
