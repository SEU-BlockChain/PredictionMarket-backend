from backend.libs.wraps.models import APIModel, models


class RecommendAbstract(models.Model):
    recommend_id = models.IntegerField(verbose_name="id")
    recommend_type = models.IntegerField(verbose_name="类型")
    update_time = models.DateTimeField(verbose_name="时间")

    class Meta:
        abstract = True


class HomeBanner(APIModel):
    image = models.CharField(max_length=128)
    url = models.CharField(max_length=128)


class SpecialBanner(APIModel):
    image = models.CharField(max_length=128)
    url = models.CharField(max_length=128)


class BBSTop(APIModel):
    title = models.CharField(max_length=128)
    url = models.CharField(max_length=128)
