FROM python:3.7.6-alpine
LABEL maintainer="Kristijan Rebernisak<kristijan.rebernisak@gmail.com>"

# set work directory
WORKDIR /usr/src/app

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements /usr/src/app/requirements/
RUN pip install -r ./requirements/prod.txt

# copy project
COPY ./src /usr/src/app/
