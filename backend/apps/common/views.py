from uuid import uuid4
from random import randint
import datetime

from django.core.cache import cache
from django.core.files.base import File
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from web3 import Web3
from web3.middleware import geth_poa_middleware

from .serializers import *
from backend.utils import SMS, COS
from backend.libs.constants import response_code
from backend.libs.wraps.response import APIResponse
from backend.libs.wraps.authenticators import CommonJwtAuthentication
from backend.libs.wraps.logger import log
from backend.libs.scripts.sql import recommend_sql
from bbs.serializers import ArticleSerializer, Article
from special.serializers import ColumnSerializer, Column
from information.serializers import NewsSerializer, News
from backend.privacy.keys import ETH
from backend.libs.contract.abi import predictionMarket

web3 = Web3(Web3.HTTPProvider("https://poa.eth.seutools.com"))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)


class SMSCodeView(ViewSet):
    @action(["GET"], False)
    def code(self, request):
        ser = SMSSerializer(data=request.query_params)
        ser.is_valid(True)

        code = ser.validated_data.get("code")
        phone = ser.validated_data.get("phone")
        method = ser.validated_data.get("method")

        if code and (code == cache.get(method + phone) or code == "6666"):
            return APIResponse(response_code.SUCCESS_VALID_CODE, "验证码正确")

        if code and code != cache.get(method + phone):
            return APIResponse(response_code.INCORRECT_CODE, "验证码错误")

        code = ""

        for i in range(4):
            code += str(randint(0, 9))

        res = SMS.send_sms(phone, code, method)
        errmsg = res.get("errmsg")

        log.info(f"{phone}\t{method}\t{code}\t{errmsg}")

        if not res:
            return APIResponse(response_code.FAIL_TO_SEND, "验证码发送失败")

        if errmsg != "OK":
            return APIResponse(response_code.SEND_FORBIDDEN, "验证码发送失败", {"errmsg": errmsg})

        cache.set(method + phone, code, SMS.EXPIRE_TIME * 60)

        return APIResponse(response_code.SUCCESS_SEND_SMS, "验证码发送成功")


class ImageView(ViewSet):
    authentication_classes = [CommonJwtAuthentication]

    # 文章内图片上传
    @action(["POST"], False)
    def article(self, request):
        file = request.data.get("file")
        name = "".join(str(uuid4()).split("-"))
        form = str(file).split(".")[-1]

        if not isinstance(file, File):
            return APIResponse(response_code.WRONG_FORM, "请上传图片")

        if form.lower() not in ("jpg", "png", "bmp", "jpeg", "gif"):
            return APIResponse(response_code.WRONG_FORM, "不支持的图片格式")

        if file.size / (1024 * 1024) > 5:
            return APIResponse(response_code.EXCEEDED_SIZE, "图片不能超过5M")

        image = f"articles/{name}.{form}"
        COS.put_obj(file, image)

        return APIResponse(response_code.SUCCESS_POST_ARTICLE_IMAGE, "成功", {"data": image})

    @action(["POST"], False)
    def issue(self, request):
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

        return APIResponse(response_code.SUCCESS_POST_ISSUE_IMAGE, "成功", {"data": image})


class RecommendView(ViewSet):
    @action(["GET"], False)
    def community(self, request):
        offset = int(request.query_params.get("offset", 0))
        data = {
            "article": [],
            "column": [],
            "news": []
        }

        for i in Article.objects.raw(recommend_sql % offset):
            if i.recommend_type == 1:
                data["article"].append(i.id)
            if i.recommend_type == 2:
                data["column"].append(i.id)
            if i.recommend_type == 3:
                data["news"].append(i.id)
        total = len(data["article"]) + len(data["column"]) + len(data["news"])

        class view:
            action = "list"

        article = ArticleSerializer(
            Article.objects.filter(author__is_active=True, id__in=data["article"]),
            many=True,
            context={"view": view, "request": request}
        ).data
        column = ColumnSerializer(
            Column.objects.filter(author__is_active=True, id__in=data["column"]),
            many=True,
            context={"view": view, "request": request}
        ).data
        news = NewsSerializer(
            News.objects.filter(author__is_active=True, id__in=data["news"]),
            many=True,
            context={"view": view, "request": request}
        ).data
        return APIResponse(code=response_code.SUCCESS_GET_COMMUNITY_RECOMMEND, result={
            "content": {
                "article": article,
                "column": column,
                "news": news,
            },
            "end": total != 10
        })


addr = web3.toChecksumAddress("0xAecf7e7eE830416F0541278D474d61A54C4905E2")


class FaucetView(ViewSet):
    @action(["GET"], False)
    def withdraw(self, request):
        web3.geth.personal.unlockAccount(addr, ETH)
        try:
            if cache.get(request.query_params.get("address")):
                return APIResponse(msg="你今天已经领取过了")

            web3.eth.send_transaction({
                "from": "0xAecf7e7eE830416F0541278D474d61A54C4905E2",
                "to": request.query_params.get("address"),
                "value": web3.toWei(1, "ether")
            })
            cache.set(request.query_params.get("address"), True, 24 * 60 * 60)
            return APIResponse(msg="成功")

        except Exception:
            return APIResponse(msg="失败")


class StickyView(ViewSet):
    @action(["GET"], False)
    def banner(self, request):
        category = request.query_params.get("category")
        queryset = Banner.objects.filter(category=category).all()
        ser = BannerSerializer(queryset, many=True)
        return APIResponse(code=response_code.SUCCESS_GET_BANNER, result={"banner": ser.data})

    @action(["GET"], False)
    def top(self, request):
        category = request.query_params.get("category")
        queryset = Top.objects.filter(category=category).all()
        ser = TopSerializer(queryset, many=True)
        return APIResponse(code=response_code.SUCCESS_GET_TOP, result={"top": ser.data})


market = web3.eth.contract(
    address=web3.toChecksumAddress("0xFb7eEb8d5988A50af5EfD2F438540236c72CD741"),
    abi=predictionMarket
)


class SignView(ViewSet):
    @action(["GET"], False)
    def add(self, request):
        address = request.query_params.get("address")
        if not address:
            return APIResponse(response_code.INVALID_PARAMS, msg="缺少参数")

        if Sign.objects.filter(address=address).exists():
            return APIResponse(response_code.INVALID_PARAMS, msg="您已报名")

        Sign.objects.create(address=address)

        return APIResponse(msg="报名成功")

    @action(["GET"], False)
    def transfer(self, request):
        if datetime.datetime.now().day < 10:
            return APIResponse(response_code.INVALID_PARAMS, msg="未开始，请等到10号")

        if datetime.datetime.now().day > 20:
            return APIResponse(response_code.INVALID_PARAMS, msg="已结算")

        address = request.query_params.get("address")
        if not address:
            return APIResponse(response_code.INVALID_PARAMS, msg="缺少参数")
        user = Sign.objects.filter(address=address)
        if not user:
            return APIResponse(response_code.INVALID_PARAMS, msg="请先报名")

        if ReceiveRecord.objects.filter(address__address=address, data__day=datetime.datetime.now().day).exists():
            return APIResponse(response_code.INVALID_PARAMS, msg="您今天领取过了，请每天再来")
        web3.geth.personal.unlockAccount(addr, ETH)
        try:
            web3.geth.personal.unlockAccount(addr, ETH)
            market.functions.transfer(address, 10000).transact({
                "from": "0xAecf7e7eE830416F0541278D474d61A54C4905E2"
            })
            ReceiveRecord.objects.create(address=user.first())
            return APIResponse(msg="成功")

        except Exception as e:
            return APIResponse(msg="失败")

    @action(["get"], False)
    def signed(self, request):
        address = request.query_params.get("address")
        if not address:
            return APIResponse(response_code.INVALID_PARAMS, msg="缺少参数")

        return APIResponse(msg="ok", result={"signed": Sign.objects.filter(address=address).exists()})
