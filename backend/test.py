import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.dev")

if __name__ == '__main__':
    import django

    django.setup()

    from user import models

    a: models.User = models.User.objects.get(id__gte=1)
    print(a.my_follow.all())
