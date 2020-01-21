FROM python:3.7.6-alpine
LABEL maintainer="Kristijan Rebernisak<kristijan.rebernisak@gmail.com>"

# set work directory
WORKDIR /usr/src/app

# copy python dependencies config file
COPY ./requirements ./requirements/

# alpine image variants only include the absolute bare minimum and
# we need to install gcc (and other libraries) to install & compile our python dependencies
RUN apk update \
    && apk add --no-cache --update --virtual .build-deps build-base postgresql-dev linux-headers gcc musl-dev libffi-dev openssl-dev python3-dev \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r ./requirements/prod.txt \
    && apk del .build-deps

# copy project
COPY ./src ./
