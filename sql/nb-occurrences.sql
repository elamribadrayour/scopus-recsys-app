SELECT DISTINCT CAST(score AS INT64) AS nb_occurrences
FROM algorithm_application_link
ORDER BY nb_occurrences DESC
