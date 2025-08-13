FROM python:3.13

ENV PYTHONUNBUFFERED 1
ENV PIPENV_DONT_LOAD_ENV 1
ENV APP_HOME=/usr/src/app

RUN apt-get update -y && apt-get install -y wait-for-it build-essential automake pkg-config libtool libyaml-dev libsecp256k1-dev libffi-dev libgmp-dev
RUN mkdir -p $APP_HOME
RUN mkdir $APP_HOME/static
WORKDIR $APP_HOME
COPY ./Pipfile ./Pipfile
COPY ./Pipfile.lock ./Pipfile.lock
COPY ./entrypoint* ./
RUN chmod a+x ./entrypoint.sh
RUN pip install --upgrade pip
RUN pip install pipenv
RUN pipenv install
RUN pipenv install gunicorn
RUN pipenv install psycopg2


CMD ./entrypoint.sh
