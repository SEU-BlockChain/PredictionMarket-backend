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
            receiver_id = %d 
        GROUP BY
            bbs_article_id,
            bbs_comment_id 
        ORDER BY
            viewed,
            last_time DESC
            """
