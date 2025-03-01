import pandas
import duckdb
import streamlit
import plotly.express as px
from wordcloud import WordCloud
import helpers.password


def get_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect("data/db.duckdb")


def get_result(connection: duckdb.DuckDBPyConnection, query: str, parameters: tuple = None) -> pandas.DataFrame:
    return connection.execute(query=query, parameters=parameters).fetch_df()


def get_algorithms_applications_links() -> pandas.DataFrame:
    connection = get_connection()
    query = """
    SELECT *
    FROM algorithm_application_link
    """
    return get_result(connection=connection, query=query)


def single_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return "#B3E9C7"


def set_occurences_stats() -> None:

    query = """
    SELECT
        COUNT(DISTINCT group_id) AS nb_algorithms
    FROM algorithm_similarity
    """
    data = get_result(connection=connection, query=query).to_dict(orient="records")[0]
    columns = streamlit.columns(2)
    columns[0].metric(
        label="Number of Algorithms", 
        value=data["nb_algorithms"]
    )

    query = """
    SELECT
        COUNT(DISTINCT group_id) AS nb_applications
    FROM application_similarity
    """
    data = get_result(connection=connection, query=query).to_dict(orient="records")[0]
    columns[1].metric(
        label="Number of Applications", 
        value=data["nb_applications"]
    )


def set_heatmap_and_metrics():
    connection = get_connection()

    query = """
    SELECT DISTINCT CAST(score AS INT64) AS nb_occurrences
    FROM algorithm_application_link
    ORDER BY nb_occurrences DESC
    """
    data = get_result(connection=connection, query=query)["nb_occurrences"].tolist()

    top_n = streamlit.selectbox(
        "Select number of top occurrences to display",
        options=data,
        index=len(data) // 2,
    )

    query = """
    SELECT
        algorithm_name,
        application_name,
        CAST(score AS INT64) AS score
    FROM algorithm_application_link
    WHERE score >= ?
    ORDER BY score DESC
    """
    data = get_result(connection=connection, query=query, parameters=(top_n,))
    data = data.pivot(index='algorithm_name', columns='application_name', values='score')
    fig = px.imshow(
        img=data,
        aspect="auto",
        text_auto=True,
        labels={"color": "Count"},
        color_continuous_scale="Magma",  # Custom color scale
        title=f"Algorithm vs Application Heatmap (< {top_n} occurrences)",
    )
    streamlit.plotly_chart(fig)



def set_algorithm_specific_applications():
    streamlit.subheader("Algorithm specific applications")
    connection = get_connection()

    query = """
    SELECT DISTINCT algorithm_name
    FROM algorithm_application_link
    ORDER BY score DESC
    """
    algorithms = get_result(connection=connection, query=query)["algorithm_name"].unique()
    algorithm_name = streamlit.selectbox(
        options=algorithms,
        label="Select algorithm",
    )

    query = """
    SELECT
        algorithm_name,
        application_name,
        CAST(score AS INT64) AS score
    FROM algorithm_application_link
    WHERE algorithm_name = ?
    ORDER BY score DESC
    """
    data = get_result(connection=connection, query=query, parameters=(algorithm_name,))
    frequencies = dict(zip(data["application_name"], data["score"]))
    wordcloud = WordCloud(
        width=800, height=400, background_color="#0D1118", colormap="magma"
    ).generate_from_frequencies(frequencies=frequencies)
    streamlit.image(wordcloud.to_image(), width=1000)


def set_application_specific_algorithms():
    streamlit.subheader("Application specific algorithms")
    connection = get_connection()

    query = """
    SELECT DISTINCT application_name
    FROM algorithm_application_link
    ORDER BY score DESC
    """
    applications = get_result(connection=connection, query=query)["application_name"].unique()
    application_name = streamlit.selectbox(
        options=applications,
        label="Select application",
    )

    query = """
    SELECT
        algorithm_name,
        application_name,
        CAST(score AS INT64) AS score
    FROM algorithm_application_link
    WHERE application_name = ?
    ORDER BY score DESC
    """
    data = get_result(connection=connection, query=query, parameters=(application_name,))
    frequencies = dict(zip(data["algorithm_name"], data["score"]))
    wordcloud = WordCloud(
        width=800, height=400, background_color="#0D1118", colormap="magma"
    ).generate_from_frequencies(frequencies=frequencies)
    streamlit.image(wordcloud.to_image(), width=1000)


# if helpers.password.is_password_ok() is False:
#     streamlit.stop()

streamlit.title("RecSys in Scopus")
connection = get_connection()

set_occurences_stats()
set_heatmap_and_metrics()
set_algorithm_specific_applications()
set_application_specific_algorithms()
