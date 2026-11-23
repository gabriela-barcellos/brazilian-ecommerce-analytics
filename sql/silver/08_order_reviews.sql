-- Bronze -> Silver | order_reviews
-- Comentários vazios viram NULL; o texto em si não é alterado.
INSERT INTO silver.order_reviews
    (review_id, order_id, review_score, review_comment_title,
     review_comment_message, review_creation_date, review_answer_timestamp,
     _run_id)
SELECT
    btrim(review_id),
    btrim(order_id),
    btrim(review_score)::SMALLINT,
    NULLIF(btrim(review_comment_title), ''),
    NULLIF(btrim(review_comment_message), ''),
    btrim(review_creation_date)::TIMESTAMP,
    btrim(review_answer_timestamp)::TIMESTAMP,
    %(run_id)s
FROM bronze.order_reviews;
