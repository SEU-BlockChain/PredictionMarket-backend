import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.dev")

if __name__ == '__main__':
    import django

    django.setup()

    from vote.models import *
    from message.models import System
    from user.models import User

    all_user = User.objects.all()

    a = []
    for i in all_user:
        a.append(System(receiver=i, content="<p>已有新版本！请在 我的->设置 中更新app</p>"))
    System.objects.bulk_create(a)
