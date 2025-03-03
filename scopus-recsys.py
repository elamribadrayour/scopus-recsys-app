"""Streamlit app."""

import pandas
import duckdb
import streamlit
import plotly.express as px
from wordcloud import WordCloud

import helpers.password


def get_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect("./data/db.duckdb")


@streamlit.cache_data(ttl=3600)
def get_result_from_db(
    query: str,
    parameters: tuple | None = None,
) -> pandas.DataFrame:
    connection = get_connection()
    return connection.execute(query=query, parameters=parameters).fetch_df()


def get_query(file_name: str) -> str:
    return open(f"./sql/{file_name}.sql").read()


def get_result(
    file_name: str,
    parameters: tuple | None = None,
) -> pandas.DataFrame:
    query = get_query(file_name=file_name)
    return get_result_from_db(query=query, parameters=parameters)


def get_result_as_df(
    file_name: str,
    parameters: tuple | None = None,
) -> pandas.DataFrame:
    return get_result(file_name=file_name, parameters=parameters)


def get_result_as_list(
    file_name: str,
    parameters: tuple | None = None,
) -> list:
    return get_result(file_name=file_name, parameters=parameters).to_dict(
        orient="records"
    )


def set_occurences_stats() -> None:
    nb_algorithms = get_result_as_list(file_name="nb-algorithms")[0]
    nb_applications = get_result_as_list(file_name="nb-applications")[0]

    columns = streamlit.columns(2)
    columns[0].metric(
        label="Number of Algorithms", value=nb_algorithms["nb_algorithms"]
    )
    columns[1].metric(
        label="Number of Applications", value=nb_applications["nb_applications"]
    )


def set_heatmap_and_metrics():
    data = get_result_as_df(file_name="nb-occurrences")["nb_occurrences"].tolist()

    top_n = streamlit.selectbox(
        "Select number of top occurrences to display",
        options=data,
        index=len(data) // 2,
    )

    data = get_result_as_df(
        file_name="algorithm-application-links-filtered-by-score",
        parameters=(top_n,),
    )
    data = data.pivot(
        index="algorithm_name", columns="application_name", values="score"
    )
    fig = px.imshow(
        img=data,
        aspect="auto",
        text_auto=True,
        labels={"color": "Count"},
        color_continuous_scale="Magma",  # Custom color scale
        title=f"Algorithm vs Application Heatmap (< {top_n} occurrences)",
    )
    streamlit.plotly_chart(fig)


@streamlit.cache_data(ttl=3600)
def get_wordcloud(data: pandas.DataFrame, column: str) -> WordCloud:
    frequencies = dict(zip(data[column], data["score"]))
    return WordCloud(
        width=800, height=400, background_color="#0D1118", colormap="magma"
    ).generate_from_frequencies(frequencies=frequencies)


def set_algorithm_specific_applications():
    streamlit.subheader("Algorithm specific applications")

    algorithms = get_result_as_df(file_name="algorithm-names")[
        "algorithm_name"
    ].unique()
    algorithm_name = streamlit.selectbox(
        options=algorithms,
        label="Select algorithm",
    )

    data = get_result_as_df(
        file_name="algorithm-application-links-filtered-by-algorithm",
        parameters=(algorithm_name,),
    )
    wordcloud = get_wordcloud(data=data, column="application_name")
    streamlit.image(wordcloud.to_image(), width=1000)


def set_application_specific_algorithms():
    streamlit.subheader("Application specific algorithms")

    applications = get_result_as_df(file_name="application-names")[
        "application_name"
    ].unique()
    application_name = streamlit.selectbox(
        options=applications,
        label="Select application",
    )

    data = get_result_as_df(
        file_name="algorithm-application-links-filtered-by-application",
        parameters=(application_name,),
    )
    wordcloud = get_wordcloud(data=data, column="algorithm_name")
    streamlit.image(wordcloud.to_image(), width=1000)


def run():
    if helpers.password.is_password_ok() is False:
        streamlit.stop()

    streamlit.title("RecSys in Scopus")

    set_occurences_stats()
    set_heatmap_and_metrics()
    set_algorithm_specific_applications()
    set_application_specific_algorithms()


if __name__ == "__main__":
    run()
