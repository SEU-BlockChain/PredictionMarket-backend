from .base import *

DEBUG = True

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{DEV_REDIS_HOST}:6379',
        'OPTIONS': {
            'CLIENT_CLASS''django_redis.client.DefaultClient'
            'CONNECTION_POOL_KWARGS': {'max_connection': 100}
        }
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'bc_db',
        'USER': 'root',
        'PASSWORD': DEV_MYSQL_KEY,
        'HOST': DEV_MYSQL_HOST
    }
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    "ask",
    "bbs",
    "special",
    "information",
    "other",
    "task",
    "common",
    "message",
    "user",
    "vote",
    "issue",
]
