import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.dev")

if __name__ == '__main__':
    import django

    django.setup()

    from bbs.models import Article
    from user.models import User, Follow
    from message.models import Dynamic, MessageSetting, Like
    from django.db.models import F, Q, Count, Sum
    from django.db.models.query import QuerySet

    a = User.objects.get(id=1)
    query = a.like_me.raw(
        """
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
    )

    for i in query:
        print(i.viewed, i.id)
