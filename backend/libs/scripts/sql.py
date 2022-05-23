like_sql = """
            select 
                *,count(*) num,min(is_viewed) viewed
            from 
                message_like 
            where 
                receiver_id=1 
            group by 
                bbs_article_id,bbs_comment_id
            order by 
                is_viewed,
                time desc 
            """
