import datetime

from .models import *
from backend.libs.wraps.serializers import APIModelSerializer, serializers, SimpleAuthorSerializer, OtherUserSerializer


class VoteChoiceSerializer(APIModelSerializer):
    num = serializers.SerializerMethodField()

    def get_num(self, instance: VoteChoice):
        if not self.context.get("show"):
            return None
        return instance.voter.all().count()

    class Meta:
        model = VoteChoice
        fields = [
            "id",
            "content",
            "num"
        ]


class VoteSerializer(APIModelSerializer):
    choice_list = serializers.ListField(write_only=True)
    choice = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()
    num = serializers.SerializerMethodField()
    voted = serializers.SerializerMethodField()
    opened = serializers.SerializerMethodField()
    show = serializers.SerializerMethodField()

    def get_show(self, instance: Vote):
        if not self.context.get("show"):
            self.context["show"] = \
                not instance.need_vote \
                or VoteToUser.objects.filter(vote=instance, user=self.context["request"].user).exists() \
                or instance.end_time < datetime.datetime.now()
        return self.context["show"]

    def get_opened(self, instance: Vote):
        return instance.start_time < datetime.datetime.now() < instance.end_time

    def get_voted(self, instance):
        record = ChoiceToUser.objects.filter(
            choice__vote=instance,
            user_id=self.context["request"].user
        ).values_list("choice_id")
        if not record:
            return False

        return list(map(lambda x: x[0], record))

    def get_creator(self, instance):
        if self.context["view"].action == "retrieve":
            return OtherUserSerializer(instance.creator, context=self.context).data
        return SimpleAuthorSerializer(instance.creator).data

    def get_num(self, instance: Vote):
        return ChoiceToUser.objects.filter(choice__vote=instance).all().count()

    def get_choice(self, instance: Vote):
        if not self.context.get("show"):
            self.context["show"] = \
                not instance.need_vote \
                or VoteToUser.objects.filter(vote=instance, user=self.context["request"].user).exists() \
                or instance.end_time < datetime.datetime.now()
        return VoteChoiceSerializer(instance=instance.votechoice_set.all(), many=True, context=self.context).data

    class Meta:
        model = Vote
        fields = [
            "id",
            "title",
            "creator",
            "start_time",
            "end_time",
            "min_num",
            "max_num",
            "anonymous",
            "need_vote",
            "choice",
            "choice_list",
            "num",
            "voted",
            "opened",
            "show",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        action = self.context["view"].action
        self.context["action"] = action
        remove = []

        if action == "retrieve":
            remove = ["choice_list"]
        if action == "list":
            remove = [
                "min_num",
                "max_num",
                "anonymous",
                "need_vote",
                "choice",
                "opened",
                "voted",
                "show",
                "num",
            ]
        for i in remove:
            self.fields.pop(i)

    def create(self, validated_data):
        choice_list = validated_data.pop("choice_list")
        validated_data["creator"] = self.context["request"].user
        instance = super().create(validated_data)

        VoteChoice.objects.bulk_create(map(lambda x: VoteChoice(content=x, vote=instance), choice_list))
        return instance
