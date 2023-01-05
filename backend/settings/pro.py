from .dev import *

DEBUG = False

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{PRO_REDIS_HOST}:6379',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connection': 100},
            'PASSWORD': PRO_REDIS_KEY
        }
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'bc_db',
        'USER': 'root',
        'HOST': PRO_MYSQL_HOST,
        'PASSWORD': PRO_MYSQL_KEY,
    }
}
