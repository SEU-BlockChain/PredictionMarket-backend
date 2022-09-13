import re
from datetime import datetime

from lxml import etree
from django.db.models import F

from .models import *
from user.models import User
from backend.libs.wraps.serializers import EmptySerializer, serializers, APIModelSerializer, OtherUserSerializer, \
    SimpleAuthorSerializer
from backend.libs.wraps.errors import SerializerError
from backend.libs.constants import response_code


class ChildrenCommentSerializer(APIModelSerializer):
    author = OtherUserSerializer(read_only=True)
    address = serializers.CharField(write_only=True)
    parent_id = serializers.IntegerField(write_only=True)
    target_id = serializers.IntegerField(allow_null=True, default=None)
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        if request := self.context.get("request"):
            author_id = request.user.id
            if not author_id:
                return None
            comment_id = instance.id
            obj = IssueCommentVote.objects.filter(comment_id=comment_id, author_id=author_id).first()
            if not obj:
                return None

            return obj.is_up

    class Meta:
        model = IssueComment
        fields = [
            "id",
            "author",
            "author_id",
            "address",
            "parent_id",
            "target_id",
            "content",
            "up_num",
            "down_num",
            "comment_time",
            "is_up",
        ]

    def create(self, validated_data):
        if validated_data.get("target_id"):
            validated_data["content"] = self._add_mention_prefix(validated_data["content"], validated_data)
        validated_data["issue"] = Issue.objects.get(address=validated_data.pop("address"))
        validated_data["content"] = self._add_mention(validated_data["content"])
        validated_data["description"] = self._get_description(validated_data["content"])
        validated_data["author"] = self.context["request"].user

        return super().create(validated_data)

    def _add_mention_prefix(self, content, validated_data):
        address = validated_data["address"]
        parent_id = validated_data["parent_id"]
        target_id = validated_data["target_id"]
        comment = IssueComment.objects.filter(
            id=target_id,
            issue__address=address,
            parent_id=parent_id
        )
        if not comment:
            raise SerializerError("评论不存在", response_code.NOT_FOUND)
        comment = comment.first()
        content = "".join([
            content[:3],
            f'回复&nbsp;<span style="color: rgb(54, 88, 226);" uid="{comment.author.id}">@{comment.author.username}:</span>',
            content[3:]
        ])
        return content

    def _get_description(self, content):
        text = etree.HTML(content).xpath("string(.)")
        if len(text) <= 40:
            html_text = f'<span>{text}</span>'
        else:
            html_text = f'<span>{text[:40]}...</span>'

        img_urls = re.findall('<img src="(.*?)" .*?/>', content)

        if not img_urls:
            return html_text

        return html_text + "<span>[图片]</span>"

    def _add_mention(self, html):
        self.context["mention"] = []
        tree = etree.HTML(html)
        for i in tree.xpath("//span[@data-w-e-type='mention']"):
            uid = i.xpath("@data-info")[0]
            username = i.xpath("text()")[0].replace("@", "")
            user = User.objects.filter(id=uid, username=username)
            if user:
                self.context["mention"].append(user.first())
                i.set("style", "color: rgb(54, 88, 226);")
                i.set("uid", uid)

        return etree.tostring(tree).decode("utf-8")[12:-14]


class IssueCommentSerializer(APIModelSerializer):
    author = OtherUserSerializer(read_only=True)
    children_comment = serializers.SerializerMethodField(read_only=True)
    is_up = serializers.SerializerMethodField(read_only=True)

    def get_is_up(self, instance):
        author_id = self.context["request"].user.id
        if not author_id:
            return None

        comment_id = instance.id
        obj = IssueCommentVote.objects.filter(comment_id=comment_id, author_id=author_id).first()
        if not obj:
            return None

        return obj.is_up

    def get_children_comment(self, instance: IssueComment):
        author_id = self.context["request"].user.id
        if children := instance.parent_comments.all().filter(is_active=True).order_by("-up_num")[:2]:
            data = ChildrenCommentSerializer(children, many=True, context=self.context).data
            for i in data:
                if not author_id:
                    i["is_up"] = None
                else:
                    comment_id = i["id"]
                    obj = IssueCommentVote.objects.filter(comment_id=comment_id, author_id=author_id).first()
                    if not obj:
                        i["is_up"] = None
                    else:
                        i["is_up"] = obj.is_up
            return data
        else:
            return []

    class Meta:
        model = IssueComment
        fields = [
            "id",
            "author",
            "author_id",
            "content",
            "up_num",
            "down_num",
            "comment_num",
            "comment_time",
            "children_comment",
            "issue_id",
            "is_up"
        ]

    def create(self, validated_data):
        validated_data["content"] = self._add_mention(validated_data["content"])
        validated_data["author"] = self.context["request"].user
        validated_data["issue"] = Issue.objects.get(address=self.context["kwargs"].get("address"))
        validated_data["description"] = self._get_description(validated_data["content"])
        return super().create(validated_data)

    def _get_description(self, content):
        text = etree.HTML(content).xpath("string(.)")
        if len(text) <= 40:
            html_text = f'<span>{text}</span>'
        else:
            html_text = f'<span>{text[:40]}...</span>'

        img_urls = re.findall('<img src="(.*?)" .*?/>', content)

        if not img_urls:
            return html_text

        return html_text + "<span>[图片]</span>"

    def _add_mention(self, html):
        self.context["mention"] = []
        tree = etree.HTML(html)
        for i in tree.xpath("//span[@data-w-e-type='mention']"):
            uid = i.xpath("@data-info")[0]
            username = i.xpath("text()")[0].replace("@", "")
            user = User.objects.filter(id=uid, username=username)
            if user:
                self.context["mention"].append(user.first())
                i.set("style", "color: rgb(54, 88, 226);")
                i.set("uid", uid)

        return etree.tostring(tree).decode("utf-8")[12:-14]


class VoteCommentSerializer(EmptySerializer):
    comment_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    is_up = serializers.ChoiceField([0, 1])

    def create(self, validated_data):
        comment_id = validated_data.get("comment_id")
        user_id = validated_data.get("user_id")
        is_up = validated_data.get("is_up")

        instance = IssueCommentVote.objects.filter(comment_id=comment_id, author_id=user_id).first()

        if not instance:
            if is_up:
                User.objects.get(id=user_id).daily.add("like")
                IssueComment.objects.get(id=comment_id).author.daily.add("comment_liked")

            instance = IssueCommentVote.objects.create(comment_id=comment_id, is_up=is_up, author_id=user_id)
            self._update_num(comment_id, is_up, 1 - is_up)
        else:
            if instance.is_up == is_up:
                instance.delete()
                self._update_num(comment_id, -is_up, is_up - 1)
            else:
                instance.is_up = is_up
                instance.save()
                self._update_num(comment_id, 2 * is_up - 1, 1 - 2 * is_up)

        return instance

    @staticmethod
    def _update_num(comment_id, up, down):
        IssueComment.objects.filter(id=comment_id).update(up_num=F("up_num") + up, down_num=F("down_num") + down)
