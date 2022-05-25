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

    username = "huhu"
    query = User.objects.raw(
        f"""
        SELECT * FROM 
            user_user 
        WHERE 
            username="{username}"
        """
    )

    for i in query:
        print(i.username)
