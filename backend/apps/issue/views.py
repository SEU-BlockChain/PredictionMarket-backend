from uuid import uuid4

from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

from django.core.files.base import File
from backend.libs import *
from backend.utils import COS


class ImageView(ViewSet):
    @action(["POST"], False)
    def image(self, request):
        file = request.data.get("file")
        name = "".join(str(uuid4()).split("-"))
        form = str(file).split(".")[-1]

        if not isinstance(file, File):
            return APIResponse(response_code.WRONG_FORM, "请上传图片")

        if form.lower() not in ("jpg", "png", "bmp", "jpeg", "gif"):
            return APIResponse(response_code.WRONG_FORM, "不支持的图片格式")

        if file.size / (1024 * 1024) > 5:
            return APIResponse(response_code.EXCEEDED_SIZE, "图片不能超过5M")

        image = f"issue/{name}.{form}"
        COS.put_obj(file, image)

        return APIResponse(response_code.SUCCESS_POST_ARTICLE_IMAGE, "成功", {"data": image})


__all__ = [
    "ImageView"
]
