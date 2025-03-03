SELECT
    algorithm_name,
    application_name,
    CAST(score AS INT64) AS score
FROM algorithm_application_link
WHERE score >= ?
ORDER BY score DESC
