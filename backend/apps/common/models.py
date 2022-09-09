from backend.libs.wraps.models import APIModel, models


class Banner(APIModel):
    img = models.CharField(max_length=256)
    url = models.CharField(max_length=256)
    category = models.IntegerField()


class Top(APIModel):
    text = models.CharField(max_length=256)
    url = models.CharField(max_length=256)
    category = models.IntegerField()


class Sign(APIModel):
    address = models.CharField(max_length=128)


class ReceiveRecord(APIModel):
    address = models.ForeignKey(to="Sign", on_delete=models.DO_NOTHING)
    data = models.DateTimeField(auto_now_add=True, verbose_name="日期")
