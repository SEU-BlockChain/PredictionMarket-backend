from backend.libs.wraps.models import APIModel, models


class Banner(APIModel):
    img = models.CharField(max_length=256)
    url = models.CharField(max_length=256)
    category = models.IntegerField()


class Top(APIModel):
    text = models.CharField(max_length=256)
    url = models.CharField(max_length=256)
    category = models.IntegerField()
