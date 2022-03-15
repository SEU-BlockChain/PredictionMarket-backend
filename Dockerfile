FROM python:3.8.8
MAINTAINER realhuhu
EXPOSE 8000
ADD docs/requriements.txt /home/
RUN pip install -r /home/requriements.txt -i https://pypi.douban.com/simple/
RUN pip install gunicorn -i https://pypi.douban.com/simple/
RUN pip install uvicorn -i https://pypi.douban.com/simple/
VOLUME ["/home"]
WORKDIR /home/backend
CMD ["gunicorn", "-c", "gunicorn.py", "backend.asgi:application"]