+++
author = "Rtx3"
title = "使用阿里云函数计算反向代理AI服务"
date = "2023-11-06"
description = "使用阿里云函数计算反向代理AI服务"
tags = [
    "安装",
    "AI服务",
]
term =  [
    "安装",
    "AI服务",
]
categories = [
    "教程",
]
+++
# 使用阿里云函数计算反向代理AI服务

[Simon (Yu Ma)](https://simonmy.com/) 收录于 类别 [杂技浅尝](https://simonmy.com/categories/杂技浅尝.html)

 2023-11-17 00:16 2023-11-17 00:16 约 1076 字  预计阅读 3 分钟 392 次阅读 7 条评论 

本文的主要思路是使用`阿里云`的`函数计算服务`来代理 OpenAI 的 API 地址，配合自己的域名即可在境内实现访问。

至于是不是永久免费，我不知道。但是每个人都有点免费额度，个人做技术探究应该是够用了。

## 前期准备

1. 需要一个阿里云账号， 没有账号的可自行注册( [点击此处注册](https://account.aliyun.com/register/qr_register.htm?oauth_callback=https%3A%2F%2Fwww.aliyun.com) )
2. 需要一个自己注册的域名， 没有的可以注册 ( [点击注册域名](https://wanwang.aliyun.com/) )

## 创建代理服务

### 1. 登录并开通函数计算服务

登录地址：https://fcnext.console.aliyun.com/overview



[![https://image.simonmy.com/file/1d6632ef21d3bc90bd433.png](https://image.simonmy.com/file/1d6632ef21d3bc90bd433.png)](https://image.simonmy.com/file/1d6632ef21d3bc90bd433.png)



### 2. 通过模板创建Nginx应用

这是整个过程中最重要的一步！

首先在函数计算管理的应用面板，找到创建应用。



[![https://image.simonmy.com/file/7d807fee13a6dad8264b0.png](https://image.simonmy.com/file/7d807fee13a6dad8264b0.png)](https://image.simonmy.com/file/7d807fee13a6dad8264b0.png)



选择 `通过模板创建应用`， 在搜索框输入 `Nginx` ，找到对应模板 `立即创建`



[![https://image.simonmy.com/file/663c870c0944c153a9e7c.png](https://image.simonmy.com/file/663c870c0944c153a9e7c.png)](https://image.simonmy.com/file/663c870c0944c153a9e7c.png)



填写一些服务关键信息。 这里要注意一下几个点

1. 选择 `直接部署`
2. 区域选择可以访问OpenAI的区域，例如：日本、美国、新加坡等
3. 函数名、角色等信息不要修改



[![https://image.simonmy.com/file/b7575e2fb19e9b5eac059.png](https://image.simonmy.com/file/b7575e2fb19e9b5eac059.png)](https://image.simonmy.com/file/b7575e2fb19e9b5eac059.png)



### 3 Nginx配置修改

1. 在`函数及服务` 面板中，找到刚创建的服务，点击进入 `Nginx`

   

   [![https://image.simonmy.com/file/fe4a744210e3e78629c01.png](https://image.simonmy.com/file/fe4a744210e3e78629c01.png)](https://image.simonmy.com/file/fe4a744210e3e78629c01.png)

   

2. 选择函数代码，并进行编辑，仅修改 `nginx.conf` 即可， 代码全文如下:

   | ` 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 ` | `# nginx -c /code/nginx.conf -g 'daemon off;' events { worker_connections 1024; } http {    server {        error_log  /dev/stderr;        access_log /dev/stdout;         gzip on;        gzip_min_length 1k;        gzip_comp_level 2;        gzip_types text/html text/plain application/javascript application/x-javascript text/css application/xml text/javascript application/x-httpd-php image/jpeg image/gif image/png image/svg+xml;        gzip_vary on;        gzip_disable "MSIE [1-6]\.";        include /etc/nginx/mime.types;        add_header Access-Control-Allow-Origin *;        proxy_set_header Host api.openai.com;        proxy_http_version 1.1;        proxy_set_header Host $host;         listen 9000;         location ~* ^\/v1\/((engines\/.+\/)?(?:chat\/completions|completions|edits|moderations|answers|embeddings))$ {            proxy_pass https://api.openai.com;            proxy_set_header Connection '';            proxy_read_timeout 8m;            proxy_ignore_headers Cache-Control;            client_body_buffer_size 4m;            proxy_ssl_server_name on;            proxy_ssl_session_reuse off;        }         location /v1 {            proxy_pass https://api.openai.com;            proxy_ssl_server_name on;            proxy_ssl_session_reuse off;        }     } } ` |
   | ------------------------------------------------------------ | ------------------------------------------------------------ |
   |                                                              |                                                              |

3. 别忘了`部署代码`

### 4 域名绑定

由于阿里云提供的默认公网访问地址是不能进行函数服务的，我们需要配置自己的域名。



[![https://image.simonmy.com/file/660fc225fa2242351d084.png](https://image.simonmy.com/file/660fc225fa2242351d084.png)](https://image.simonmy.com/file/660fc225fa2242351d084.png)



通过函数计算面板，找到域名管理页面，并进入`添加自定义域名`



[![https://image.simonmy.com/file/7c07cb31e5a773197c31d.png](https://image.simonmy.com/file/7c07cb31e5a773197c31d.png)](https://image.simonmy.com/file/7c07cb31e5a773197c31d.png)



注意以下标出的几个重要信息

1. 域名输入后，先去解析 `CNAME`，如果没有解析，最终是无法提交的。 这一步不会做，自己去搜索引擎学习
2. 路由配置
   1. 路径如图使用 `/*`
   2. 服务名称： 即为刚才创建的服务
   3. 函数名: nginx
   4. 版本: LATEST
3. 强烈建议配置HTTPS
   1. 如果你已经有了，可以上传。
   2. 如果没有，直接使用免费的HTTPS申请教程: [点击学习](https://developer.aliyun.com/article/1212043)



[![https://image.simonmy.com/file/d9f219f4403dd3ab3c638.png](https://image.simonmy.com/file/d9f219f4403dd3ab3c638.png)](https://image.simonmy.com/file/d9f219f4403dd3ab3c638.png)



详细的配置文档：https://help.aliyun.com/zh/fc/user-guide/configure-a-custom-domain-name

## 其他操作

### Nginx服务资源调整(非必须)

由于模板考虑到的是通用性，所以Nginx的资源申请的比较大。对于反向代理Open AI服务来说，就是大材小用、资源浪费了，我们还是能省则省。

1. 从函数计算面板，找到`服务及函数`，找到Nginx服务，点击函数名进入
2. 将Nginx调整为：`0.1核, 128MB`即可， 其他参数不要去修改
3. 不要忘记保存



[![https://image.simonmy.com/file/b4d738c7cece00a47edb3.png](https://image.simonmy.com/file/b4d738c7cece00a47edb3.png)](https://image.simonmy.com/file/b4d738c7cece00a47edb3.png)





[![https://image.simonmy.com/file/c219e20e7f73992c2bccb.png](https://image.simonmy.com/file/c219e20e7f73992c2bccb.png)](https://image.simonmy.com/file/c219e20e7f73992c2bccb.png)





[![https://image.simonmy.com/file/f7a9db50b2e6e7d829753.png](https://image.simonmy.com/file/f7a9db50b2e6e7d829753.png)](https://image.simonmy.com/file/f7a9db50b2e6e7d829753.png)



## 写在最后

之前我也是使用Cloudflare Worker 反代 Open AI的API，今天突然用不成了。此文仅抛砖引玉，用于个人技术研究。