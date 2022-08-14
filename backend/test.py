import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.dev")

if __name__ == '__main__':
    import django

    django.setup()

    from bbs.models import Article
    from user.models import User, Follow
    from special.models import Column
    from information.models import News

    a = Article.objects.all().values_list(
        "update_time"
    ).union(Column.objects.all().values_list(
        "update_time"
    )).union(News.objects.all().values_list(
        "update_time"
    ))
    print(a)
