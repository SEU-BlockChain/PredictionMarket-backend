import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings.dev")

if __name__ == '__main__':
    import django

    django.setup()

    from vote.models import *

    print(ChoiceToUser.objects.filter(choice__vote_id=8, user_id=1).values("choice_id"))
