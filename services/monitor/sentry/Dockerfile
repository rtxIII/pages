FROM python:2.7

MAINTAINER rtx3 <r@rtx3.com>

# Sane defaults for pip
ENV PIP_NO_CACHE_DIR off
ENV PIP_DISABLE_PIP_VERSION_CHECK on


RUN pip install -U wheel pip setuptools 

#RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list

RUN apt-get -qq update && DEBIAN_FRONTEND=noninteractive apt-get install -y -q libxslt1-dev libxml2-dev libpq-dev libldap2-dev libsasl2-dev libssl-dev

RUN mkdir -p /conf /data /wheels

ADD requirements.txt /conf/

RUN pip wheel --wheel-dir=/wheels -r /conf/requirements.txt 

ENV SENTRY_VERSION 9.1.2

RUN set -x \
    && buildDeps=" \
        cargo g++ \
        dirmngr \
        gnupg \
        wget \
    " \
    && apt-get update && apt-get install -y --no-install-recommends $buildDeps && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /usr/src/sentry \
    && wget -O /usr/src/sentry/sentry-${SENTRY_VERSION}-py27-none-any.whl "https://github.com/getsentry/sentry/releases/download/${SENTRY_VERSION}/sentry-${SENTRY_VERSION}-py27-none-any.whl" \
    && wget -O /usr/src/sentry/sentry-${SENTRY_VERSION}-py27-none-any.whl.asc "https://github.com/getsentry/sentry/releases/download/${SENTRY_VERSION}/sentry-${SENTRY_VERSION}-py27-none-any.whl.asc" \
    && wget -O /usr/src/sentry/sentry_plugins-${SENTRY_VERSION}-py2.py3-none-any.whl "https://github.com/getsentry/sentry/releases/download/${SENTRY_VERSION}/sentry_plugins-${SENTRY_VERSION}-py2.py3-none-any.whl" \
    && wget -O /usr/src/sentry/sentry_plugins-${SENTRY_VERSION}-py2.py3-none-any.whl.asc "https://github.com/getsentry/sentry/releases/download/${SENTRY_VERSION}/sentry_plugins-${SENTRY_VERSION}-py2.py3-none-any.whl.asc" \
    && export GNUPGHOME="$(mktemp -d)" \
    && pip install --find-links=/wheels \
        /usr/src/sentry/sentry-${SENTRY_VERSION}-py27-none-any.whl \
        /usr/src/sentry/sentry_plugins-${SENTRY_VERSION}-py2.py3-none-any.whl \
    && sentry --help \
    && sentry plugins list \
    && rm -r "$GNUPGHOME" /usr/src/sentry \
    && apt-get purge -y --auto-remove $buildDeps

EXPOSE 9000

VOLUME ["/data"]

ADD sentry_docker_conf.py /conf/
ADD sentry_run /usr/local/bin/

ENTRYPOINT ["sentry"]

ENTRYPOINT ["sentry --config=$SENTRY_CONF_FILE"]

RUN pip install python-decouple dj-database-url django-cache-url django-redis django-auth-ldap
#RUN pip install -r /conf/requirements.txt 
ADD scripts/create_team_or_project.py /conf/
ADD scripts/check_db_isalive.py /conf/

# cleanup
RUN apt-get clean
RUN rm -f /wheels/*
RUN apt-get remove -y -q libxslt1-dev libxml2-dev libpq-dev libldap2-dev libsasl2-dev libssl-dev
RUN rm -rf /var/lib/apt/lists/*
