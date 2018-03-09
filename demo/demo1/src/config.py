# -*- coding: utf-8 -*-
"""
    ProcessName_XXX.config
    ~~~~~~~~~~~~~~

    configure file

    :copyright: (c) 2017 by staugur.
    :license: MIT, see LICENSE for more details.
"""

from os import getenv

GLOBAL = {

    "ProcessName": "demo1",
    #Custom process, you can see it with "ps aux|grep ProcessName".

    "Host": getenv("demo1_host", "0.0.0.0"),
    #Application run network address, you can set it `0.0.0.0`, `127.0.0.1`, ``.

    "Port": getenv("demo1_port", 5001),
    #Application run port, default port.

    "LogLevel": getenv("demo1_loglevel", "DEBUG"),
    #Application to write the log level, currently has DEBUG, INFO, WARNING, ERROR, CRITICAL.
}


SSO = {

    "app_name": getenv("demo1_sso_app_name", GLOBAL["ProcessName"]),
    # SSO中注册的应用名

    "app_id": getenv("demo1_sso_app_id", "e368b9938746fa090d6afd3628355133"),
    # SSO中注册返回的`app_id`

    "app_secret": getenv("demo1_sso_app_secret", "MJRWGMZRMI3DAMDDMMZTINDBHA4DONTFGBSD"),
    # SSO中注册返回的`app_secret`

    "sso_server": getenv("demo1_sso_server", "https://passport.saintic.com"),
    # SSO完全合格域名根地址
}


MYSQL = getenv("demo1_mysql_url")
#MYSQL数据库连接信息
#mysql://host:port:user:password:database?charset=&timezone=


REDIS = getenv("demo1_redis_url")
#Redis数据库连接信息，格式：
#redis://[:password]@host:port/db
#host,port必填项,如有密码,记得密码前加冒号,默认localhost:6379/0


# 系统配置
SYSTEM = {

    "HMAC_SHA256_KEY": getenv("demo1_hmac_sha256_key", "273d32c8d797fa715190c7408ad73811"),
    # hmac sha256 key

    "AES_CBC_KEY": getenv("demo1_aes_cbc_key", "YRRGBRYQqrV1gv5A"),
    # utils.aes_cbc.CBC类中所用加密key

    "JWT_SECRET_KEY": getenv("demo1_jwt_secret_key", "WBlE7_#qDf2vRb@vM!Zw#lqrg@rdd3A6"),
    # utils.jwt.JWTUtil类中所用加密key

    "Sign": {
        "version": getenv("demo1_sign_version", "v1"),
        "accesskey_id": getenv("demo1_sign_accesskeyid", "accesskey_id"),
        "accesskey_secret": getenv("demo1_sign_accesskeysecret", "accesskey_secret"),
    }
    # utils.Signature.Signature签名配置
}


#插件配置段
PLUGINS = {}