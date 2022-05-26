like_sql = """
SELECT
    id,
    origin,
    bbs_article_id,
    bbs_comment_id,
    receiver_id,
    sender_id,
    max( time ) last_time,
    count(*) total,
    min( is_viewed ) viewed,
    count(*) - sum( is_viewed ) new 
FROM
    message_like 
WHERE
    is_active=true and receiver_id = %d 
GROUP BY
    bbs_article_id,
    bbs_comment_id 
ORDER BY
    viewed,
    last_time DESC
"""

private_sql = """
SELECT
    id,
    content,
    sender_id,
    MAX(time) last_time,
    MIN( is_viewed ) viewed,
    COUNT(*)- SUM( is_viewed ) new 
FROM
    message_private 
WHERE
    is_active=1 
    AND receiver_id = %d 
GROUP BY
    sender_id
ORDER BY
    viewed,
    last_time DESC;
"""
