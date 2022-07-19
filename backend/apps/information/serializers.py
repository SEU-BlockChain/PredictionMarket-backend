from .models import *
from backend.libs.wraps.serializers import APIModelSerializer


class NewsSerializer(APIModelSerializer):
    class Meta:
        model = News
        fields = [
            "id",
            "title",
            "author",
            "description",
            "content",
            "raw_content",
            "create_time",
            "update_time",
            "is_draft",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        action = self.context["view"].action
        self.context["action"] = action
        remove = []
        if action == "list":
            remove = [
                "author",
                "content",
                "raw_content",
                "update_time",
            ]
            if not self.context["request"].query_params.get("self"):
                remove.append("is_draft")
        if action == "retrieve":
            remove = [
                "author",
                "is_draft",
            ]
            if not self.context["request"].query_params.get("raw"):
                remove += ["description", "raw_content"]
        if action == "create":
            remove = [
                "author",
                "create_time",
                "update_time",
            ]
        if action == "update":
            remove = [
                "author",
                "create_time",
                "update_time",
            ]
        for i in remove:
            self.fields.pop(i)

    def create(self, validated_data):
        validated_data["author_id"] = self.context["request"].user.id
        return super().create(validated_data)
