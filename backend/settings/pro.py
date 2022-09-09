from .dev import *

DEBUG = False

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://1.13.161.219:6379',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': REDIS_KEY
        }
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'bc_db',
        'USER': 'root',
        'PASSWORD': MYSQL_KEY,
        'HOST': '1.13.159.138'
    }
}
