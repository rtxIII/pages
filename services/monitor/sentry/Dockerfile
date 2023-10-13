FROM sentry:9.1

MAINTAINER rtx3 <r@rtx3.com>

# Sane defaults for pip
ENV PIP_NO_CACHE_DIR off
ENV PIP_DISABLE_PIP_VERSION_CHECK on


RUN apt-get -qq update && DEBIAN_FRONTEND=noninteractive apt-get install -y -q libxslt1-dev libxml2-dev libpq-dev libldap2-dev libsasl2-dev libssl-dev

EXPOSE 9000

VOLUME ["/data"]

ADD requirements.txt /tmp/

RUN pip install -r /tmp/requirements.txt 
RUN mkdir /scripts
ADD scripts/create_team_or_project.py /scripts/
ADD scripts/check_db_isalive.py /scripts/

# cleanup
RUN apt-get clean
RUN rm -f /tmp/*
RUN apt-get remove -y -q libxslt1-dev libxml2-dev libpq-dev libldap2-dev libsasl2-dev libssl-dev
RUN rm -rf /var/lib/apt/lists/*
