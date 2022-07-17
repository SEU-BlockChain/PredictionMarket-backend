import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.dev")

if __name__ == '__main__':
    import django

    django.setup()

    from bbs.models import Article
    from user.models import User, Follow

    print(User.objects.get(id=1).daily)
