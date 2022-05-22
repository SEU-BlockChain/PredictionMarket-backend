import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.dev")

if __name__ == '__main__':
    import django

    django.setup()

    from bbs.models import Article
    from user.models import User, Follow
    from message.models import Dynamic, MessageSetting
    from django.db.models import F, Q
    from django.db.models.query import QuerySet

    u = User.objects.get(id=2)
    print(u.dynamic_me.all().filter(is_active=False).update(is_active=True))
