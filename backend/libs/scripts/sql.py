like_sql = """
SELECT id,
       origin,
       bbs_article_id,
       bbs_comment_id,
       receiver_id,
       sender_id,
       max(time)                 last_time,
       count(*)                  total,
       min(is_viewed)            viewed,
       count(*) - sum(is_viewed) new
FROM message_like
WHERE is_active = true
  AND receiver_id = %d
GROUP BY bbs_article_id,
         bbs_comment_id,
         special_column_id,
         special_comment_id
ORDER BY viewed,
         last_time DESC;
"""

private_sql = """
SELECT id,
       content,
       sender_id,
       MAX(time)                 last_time,
       MIN(is_viewed)            viewed,
       COUNT(*) - SUM(is_viewed) new
FROM message_private
WHERE is_active = 1
  AND receiver_id = %d
GROUP BY sender_id
ORDER BY viewed,
         last_time DESC;
"""

recommend_sql = """SELECT *
FROM (
         SELECT id, update_time, 1 AS recommend_type
         FROM bbs_article
         WHERE is_active = true
         UNION
         SELECT id, update_time, 2 AS recommend_type
         FROM special_column
         WHERE is_active = true
           AND is_audit = true
           AND is_draft = false
         UNION
         SELECT id, update_time, 3 AS recommend_type
         FROM information_news
         WHERE is_draft = false
           AND is_active = true
     ) AS C
ORDER BY update_time DESC
LIMIT 10 OFFSET %d;
"""

post_sql = """SELECT *
FROM (
         SELECT id, update_time, create_time, up_num, comment_num, 1 AS post_type
         FROM bbs_article
         WHERE is_active = true
           AND author_id = "{user_id}"
         UNION
         SELECT id, update_time, create_time, up_num, comment_num, 2 AS post_type
         FROM special_column
         WHERE is_active = true
           AND is_audit = true
           AND is_draft = false
           AND author_id = "{user_id}"
     ) AS T
ORDER BY {order} {desc}
LIMIT 10 OFFSET {offset};
"""

comment_sql = """
SELECT *
FROM (
         SELECT id, comment_time, up_num, comment_num, comment_type
         FROM (
                  SELECT id, comment_time, up_num, comment_num, article_id, 1 AS comment_type
                  FROM bbs_comment
                  WHERE is_active = true
                    AND author_id = "{user_id}"
              ) AS A
                  JOIN (
             SELECT id as uid, is_active
             FROM bbs_article
             where is_active = true
         ) AS B ON A.article_id = B.uid
         UNION
         SELECT id, comment_time, up_num, comment_num, comment_type
         FROM (
                  SELECT id, comment_time, up_num, comment_num, column_id, 2 AS comment_type
                  FROM special_comment
                  WHERE is_active = true
                    AND author_id = "{user_id}"
              ) AS A
                  JOIN (
             SELECT id as uid, is_active
             FROM special_column
             where is_active = true
               AND is_draft = false
               AND is_audit = true
         ) AS B ON A.column_id = B.uid
         UNION
         SELECT id, comment_time, up_num, comment_num, 3 AS comment_type
         FROM issue_issuecomment
         WHERE is_active = true
           AND author_id = "{user_id}"
     ) AS T
ORDER BY {order} {desc}
LIMIT 10 OFFSET {offset};
"""
