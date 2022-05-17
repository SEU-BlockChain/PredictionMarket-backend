import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.dev")

if __name__ == '__main__':
    import django

    django.setup()

    from user import models

    a = models.User.objects.get(id=1).my_black.values_list('blacked').first()
    print(a)
