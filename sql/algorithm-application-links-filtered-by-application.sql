SELECT
    algorithm_name,
    application_name,
    CAST(score AS INT64) AS score
FROM algorithm_application_link
WHERE application_name = ?
ORDER BY score DESC