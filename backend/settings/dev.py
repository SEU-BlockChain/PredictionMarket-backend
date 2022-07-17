from .base import *

DEBUG = True

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379',
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
        'PASSWORD': MYSQL_KEY,
        'HOST': '127.0.0.1'
        # 'HOST': '1.13.159.138'
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
]
