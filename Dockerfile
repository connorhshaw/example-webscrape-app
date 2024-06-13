FROM python:3.11.5-alpine

COPY ./requirements.txt /requirements.txt
COPY ./.env /.env
COPY ["src", "/src"]

RUN apk add libffi-dev && \
apk add gcc libc-dev libffi-dev && \
python -m pip install --no-cache-dir --upgrade -r /requirements.txt

#Labels as key value pair
LABEL Maintainer="connor"

WORKDIR /

CMD ["python", "src/retrieve_post_data_test.py"]