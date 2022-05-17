from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination, OrderedDict
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import MethodNotAllowed

from .response import APIResponse


class Pag(PageNumberPagination):
    page_size_query_param = "limit"
    page_query_param = "page"
    page_size = 10

    def get_paginated_response(self, data):
        return APIResponse(data[0], "成功获取此页数据", OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data[1])
        ]))


class APIModelViewSet(ModelViewSet):
    exclude = []
    pagination_class = Pag
    filter_backends = (SearchFilter, DjangoFilterBackend, OrderingFilter)
    code = {}

    def is_exclude(self):
        if self.action in self.exclude:
            raise MethodNotAllowed(self.action)

    def create(self, request, *args, **kwargs):
        self.is_exclude()

        if before := getattr(self, f"before_{self.action}", None):
            if response := before(request, *args, **kwargs):
                return response

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(True)
        instance = serializer.save()

        if after := getattr(self, f"after_{self.action}", None):
            if response := after(instance, request, *args, **kwargs):
                return response

        return APIResponse(self.code["create"], "成功添加数据", serializer.data)

    def retrieve(self, request, *args, **kwargs):
        self.is_exclude()

        if before := getattr(self, f"before_{self.action}", None):
            if response := before(request, *args, **kwargs):
                return response

        instance = self.get_object()
        serializer = self.get_serializer(instance)

        if after := getattr(self, f"after_{self.action}", None):
            if response := after(instance, request, *args, **kwargs):
                return response

        return APIResponse(self.code["retrieve"], "成功获取单条数据", serializer.data)

    def update(self, request, *args, **kwargs):
        self.is_exclude()

        if before := getattr(self, f"before_{self.action}", None):
            if response := before(request, *args, **kwargs):
                return response

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(True)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        instance = serializer.save()

        if after := getattr(self, f"after_{self.action}", None):
            if response := after(instance, request, *args, **kwargs):
                return response

        return APIResponse(self.code["update"], "已更新", serializer.data)

    def list(self, request, *args, **kwargs):
        self.is_exclude()

        if before := getattr(self, f"before_{self.action}", None):
            if response := before(request, *args, **kwargs):
                return response

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response((self.code["list"], serializer.data))

        if after := getattr(self, f"after_{self.action}", None):
            if response := after(queryset, request, *args, **kwargs):
                return response

        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(self.code["list"], "成功获取此页数据", serializer.data)

    def destroy(self, request, *args, **kwargs):
        self.is_exclude()

        if before := getattr(self, f"before_{self.action}", None):
            if response := before(request, *args, **kwargs):
                return response

        instance = self.get_object()
        instance.is_active = False
        instance.save()

        if after := getattr(self, f"after_{self.action}", None):
            if response := after(instance, request, *args, **kwargs):
                return response

        return APIResponse(self.code["destroy"], "成功删除数据")
