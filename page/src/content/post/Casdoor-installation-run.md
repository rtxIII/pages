+++
author = "Rtx3"
title = "统一登录开源服务安装"
date = "2023-11-06"
description = "统一登录开源服务安装"
tags = [
    "安装",
    "开源服务",
]
term =  [
    "安装",
    "开源",
]
categories = [
    "教程",
]
+++
# 统一登录开源服务Casdoor部署

------

统一登录是自动运维的基础以及基石，它可以极大的减少用户的管理成本。

常用的统一登录方式有

- AD
- LDAP
- CAS
- OAUTH

开源服务提供了大部分的接入方式，并且依赖简单，值得使用。

<u>当使用在生产环境时，需使用K8S等方式实现高可用。</u>

<u>！当使用在生产环境时，将管理人员使用的登录服务与普通用户使用的登录服务隔离。</u>

## Casdoor features

1. Casdoor follows a front-end and back-end separate architecture, developed by Golang. It supports high concurrency, provides a web-based UI for management, and supports localization in 10+ languages.
2. Casdoor supports third-party application login, such as GitHub, Google, QQ, and WeChat, and it supports extending third-party login with plugins.
3. Casdoor supports authorization management based on [Casbin](https://casbin.org/). It supports ACL, RBAC, ABAC, and RESTful access control models.
4. Casdoor provides phone verification code, email verification code, and password retrieval functions.
5. Casdoor supports auditing and recording of accessing logs.
6. Casdoor integrates with Alibaba Cloud, Tencent Cloud, and Qiniu Cloud image CDN cloud storage.
7. Casdoor allows customization of registration, login, and password retrieval pages.
8. Casdoor supports integration with existing systems by database synchronization, enabling smooth transition to Casdoor.
9. Casdoor supports mainstream databases such as MySQL, PostgreSQL, and SQL Server, and it supports the extension of new databases with plugins.

------

## How Casdoor Works

Casdoor follows the authorization process built upon the OAuth 2.0 protocol. It is highly recommended to have a brief understanding of how OAuth 2.0 works. You can refer to this [introduction](https://www.digitalocean.com/community/tutorials/an-introduction-to-oauth-2) to OAuth 2.0.

![镜像](https://casdoor.org/zh/assets/images/oauth-2913ec44d8cf5851fd9dd7c359ed4e21.pn

------

## Installation

注意事项

如使用容器数据库，则去掉注释

```shell
version: '3.1'
services:
  casdoor:
    restart: always
    image: casbin/casdoor:v1.428.0
    entrypoint: /bin/sh -c './server --createDatabase=true'
    ports:
      - "8000:8000"
#    depends_on:
#      - postgres
    environment:
      RUNNING_IN_DOCKER: "true"
    volumes:
      - ./conf:/conf/
  #use local postgresql db
  #postgres:
  #  image: postgres:12-alpine
  #  user: postgres
  #  environment:
  #    POSTGRES_USER: postgres
  #    POSTGRES_PASSWORD: p0stgr3s
  #    PGDATA: /var/lib/postgresql/data/pgdata
  #  healthcheck:
  #    test: ["CMD-SHELL", "pg_isready"]
  #    interval: 10s
  #    timeout: 5s
  #    retries: 5
  #  volumes:
  #    - /srv/postgresql/data:/var/lib/postgresql/data

```

配置文件：

```

appname = casdoor
httpport = 9000
runmode = dev
SessionOn = true
copyrequestbody = true
driverName = postgres
dataSourceName = "user=postgres password=p0stgr3s host=localhost port=5432 sslmode=disable dbname=casdoor"
dbName = casdoor
tableNamePrefix =
showSql = false
redisEndpoint =
defaultStorageProvider =
isCloudIntranet = false
authState = "casdoor"
socks5Proxy =
verificationCodeTimeout = 10
initScore = 2000
logPostOnly = true

origin =  #!!
staticBaseUrl = "https://cdn.casbin.org"
isDemoMode = false
batchSize = 100
ldapServerPort = 389
languages = en,zh,es,fr,de,ja,ko,ru,vi
quota = {"organization": -1, "user": -1, "application": -1, "provider": -1}
```

置于conf目录下后启动：

```bash
docker-compose up
```



### 服务启动有坑的地方

origin =  #!! 如果这里不置空则会强制校验域名，当部署在nginx时后会出现403.