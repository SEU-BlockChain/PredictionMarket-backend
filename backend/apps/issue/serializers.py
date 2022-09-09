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



