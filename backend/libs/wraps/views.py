from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination, OrderedDict
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.request import Request

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

    def before_create(self, request, *args, **kwargs):
        pass

    def create(self, request: Request, *args, **kwargs):
        self.is_exclude()

        self.before_create(request, *args, **kwargs)

        serializer = self.get_serializer(data=request.data, args=args, kwargs=kwargs)
        serializer.is_valid(True)
        instance = serializer.save()

        self.after_create(instance, request, *args, **kwargs)

        return APIResponse(self.code["create"], "成功添加数据", serializer.data)

    def after_create(self, instance, request, *args, **kwargs):
        pass

    def before_retrieve(self, request, *args, **kwargs):
        pass

    def retrieve(self, request, *args, **kwargs):
        self.is_exclude()

        self.before_retrieve(request, *args, **kwargs)

        instance = self.get_object()
        serializer = self.get_serializer(instance, args=args, kwargs=kwargs)

        self.after_retrieve(instance, request, *args, **kwargs)
        return APIResponse(self.code["retrieve"], "成功获取单条数据", serializer.data)

    def after_retrieve(self, instance, request, *args, **kwargs):
        pass

    def before_update(self, request, *args, **kwargs):
        pass

    def update(self, request, *args, **kwargs):
        self.is_exclude()

        self.before_update(request, *args, **kwargs)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, args=args, kwargs=kwargs)
        serializer.is_valid(True)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        instance = serializer.save()

        self.after_update(instance, request, *args, **kwargs)

        return APIResponse(self.code["update"], "已更新", serializer.data)

    def after_update(self, instance, request, *args, **kwargs):
        pass

    def before_list(self, request, *args, **kwargs):
        pass

    def list(self, request, *args, **kwargs):
        self.is_exclude()

        self.before_list(request, *args, **kwargs)

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, args=args, kwargs=kwargs)
            self.after_list(queryset, request, *args, **kwargs)

            return self.get_paginated_response((self.code["list"], serializer.data))

        self.after_list(queryset, request, *args, **kwargs)

        serializer = self.get_serializer(queryset, many=True, args=args, kwargs=kwargs)
        return APIResponse(self.code["list"], "成功获取此页数据", serializer.data)

    def after_list(self, queryset, request, *args, **kwargs):
        pass

    def before_destroy(self, request, *args, **kwargs):
        pass

    def destroy(self, request, *args, **kwargs):
        self.is_exclude()

        self.before_destroy(request, *args, **kwargs)

        instance = self.get_object()
        instance.is_active = False
        instance.save()

        self.after_destroy(instance, request, *args, **kwargs)

        return APIResponse(self.code["destroy"], "成功删除数据")

    def after_destroy(self, instance, request, *args, **kwargs):
        pass

    def get_serializer(self, *args, **kwargs):
        _args = kwargs.pop("args", None)
        _kwargs = kwargs.pop("kwargs", None)
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_context(_args, _kwargs))
        return serializer_class(*args, **kwargs)

    def get_context(self, _args, _kwargs):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self,
            'args': _args,
            'kwargs': _kwargs
        }
