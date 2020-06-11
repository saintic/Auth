# -*- coding: utf-8 -*-
"""
    passport.views.FrontView
    ~~~~~~~~~~~~~~

    The blueprint for front view.

    :copyright: (c) 2017 by staugur.
    :license: MIT, see LICENSE for more details.
"""
from config import SYSTEM
from utils.web import login_required, anonymous_required, adminlogin_required, dfr, oauth2_name2type, get_redirect_url, checkGet_ssoRequest, checkSet_ssoTicketSid, set_redirectLoginstate, set_jsonifyLoginstate, FastPushMessage
from utils.tool import logger, email_check, phone_check, md5
from libs.auth import Authentication
from urllib import urlencode
from flask import Blueprint, request, render_template, g, redirect, url_for, flash, make_response, jsonify

#初始化前台蓝图
FrontBlueprint = Blueprint("front", __name__)

@FrontBlueprint.route('/')
@login_required
def index():
    # 未登录时跳转到登录页；已登录后跳转到个人设置页面
    return redirect(url_for(".userset"))

@FrontBlueprint.route('/user/setting/')
@login_required
def userset():
    """用户基本设置"""
    Action = request.args.get("Action")
    if Action == "bindLauth":
        # 绑定
        return render_template("user/user.bind.html")
    return render_template("user/setting.html")

@FrontBlueprint.route('/user/app/')
@adminlogin_required
def userapp():
    Action = request.args.get("Action")
    if Action == "editView":
        # 编辑应用
        return render_template("user/apps.edit.html")
    # 默认返回应用选项卡
    return render_template("user/apps.html")

@FrontBlueprint.route('/sys/manager/')
@adminlogin_required
def sysmanager():
    # 系统管理
    return render_template("user/sysmanager.html")

@FrontBlueprint.route('/user/message/')
@login_required
def usermsg():
    """用户消息"""
    return render_template("user/message.html")

@FrontBlueprint.route('/user/security/')
@login_required
def usersecurity():
    """用户安全"""
    return render_template("user/security.html")

@FrontBlueprint.route('/signUp', methods=['GET', 'POST'])
@anonymous_required
def signUp():
    if request.method == 'POST':
        res = dict(msg=None, code=1, nextUrl=url_for('.signUp'))
        if True:
            account = request.form.get("account")
            vcode = request.form.get("vcode")
            password = request.form.get("password")
            repassword = request.form.get("repassword")
            auth = Authentication(g.mysql, g.redis)
            result = auth.signUp(account=account, vcode=vcode, password=password, repassword=repassword, register_ip=g.ip)
            #注册欢迎消息
            FastPushMessage(result, "欢迎您的加入！%s使用中有任何问题，都可以反馈哦。" %("" if email_check(account) else "您使用手机注册，已经完成实名认证！", ))
            if result["success"]:
                res.update(code=0, nextUrl=url_for('.signIn'))
            else:
                res.update(msg=result["msg"])
        else:
            res.update(msg="Man-machine verification failed")
        return jsonify(dfr(res))
    return render_template("auth/signUp.html")

@FrontBlueprint.route('/signIn', methods=['GET', 'POST'])
def signIn():
    """ 单点登录流程
        1. Client跳转到Server的登录页，携带参数sso(所需sso信息的加密串)，验证并获取应用数据。
        2. 未登录时，GET请求显示登录表单，输入用户名密码或第三方POST登录成功后(一处是signIn post；一处是OAuthDirectLogin post；一处是OAuthBindAccount post)，创建全局会话(设置Server登录态)、授权令牌ticket，根据ticket生成sid(全局会话id)写入redis，ReturnUrl组合ticket跳转；
           已登录后，检查是否有sid，没有则创建ticket，ReturnUrl组合ticket跳转。
        3. 校验参数通过后，设置ReturnUrl(从数据库读取)为Client登录地址；校验未通过时ReturnUrl为系统redirect_uri。
        4. Client用ticket到Server校验(通过api方式)，通过redis校验cookie是否存在；存在则创建局部会话(设置Client登录态)，否则登录失败。
        -- sso加密规则：
            aes_cbc(jwt_encrypt("app_name:app_id.app_secret"))
        -- sso校验流程：
            根据sso参数，验证是否有效，解析参数获取name、id、secret等，并用name获取到对应信息一一校验
        -- 备注：
            第3步，需要signIn、OAuthGuide方面路由设置
            第4步，需要在插件内增加api路由
    """
    # 加密的sso参数值
    sso = request.args.get("sso") or None
    sso_isOk, sso_returnUrl, sso_appName = checkGet_ssoRequest(sso)
    logger.debug("method: {}, sso_isOk: {}, ReturnUrl: {}".format(request.method, sso_isOk, sso_returnUrl))
    if g.signin:
        # 已登录后流程
        # 如果没有sid说明是本地登录，需要重置登录态
        if sso_isOk:
            if g.sid:
                # 创建ticket，返回为真即是ticket
                tickets = g.api.usersso.ssoCreateTicket(sid=g.sid, agent=g.agent, ip=g.ip)
                if tickets:
                    ticket, sid = tickets
                    returnUrl = "{}&ticket={}".format(sso_returnUrl, ticket)
                    return redirect(returnUrl)
                else:
                    flash(dfr(dict(msg="Failed to create authorization ticket")))
            else:
                sessionId, returnUrl = checkSet_ssoTicketSid(sso_isOk, sso_returnUrl, sso_appName, g.uid, get_redirect_url("front.userset"))
                return set_redirectLoginstate(sessionId, returnUrl)
        return redirect(url_for("front.userset"))
    else:
        # 未登录时流程
        if request.method == 'POST':
            # POST请求不仅要设置登录态、还要设置全局会话
            res = dict(msg=None, code=1, nextUrl=url_for('.signIn', sso=sso) if sso_isOk else url_for('.signIn'))
            if True:
                auth = Authentication(g.mysql, g.redis)
                result = auth.signIn(account=request.form.get("account"), password=request.form.get("password"))
                if result["success"]:
                    # 记录登录日志
                    auth.brush_loginlog(result, login_ip=g.ip, user_agent=g.agent)
                    sessionId, returnUrl = checkSet_ssoTicketSid(sso_isOk, sso_returnUrl, sso_appName, result["uid"], get_redirect_url("front.userset"))
                    logger.debug("signIn post returnUrl: {}".format(returnUrl))
                    res.update(nextUrl=returnUrl, code=0)
                    return set_jsonifyLoginstate(sessionId, dfr(res))
                    #return set_redirectLoginstate(sessionId, returnUrl)
                else:
                    res.update(msg=result["msg"])
            else:
                res.update(msg="Man-machine verification failed")
            return jsonify(dfr(res))
            #return redirect(url_for('.signIn', sso=sso)) if sso_isOk else redirect(url_for('.signIn'))
        else:
            # GET请求仅用于渲染
            return render_template("auth/signIn.html")

@FrontBlueprint.route("/OAuthGuide", methods=["GET", "POST"])
@anonymous_required
def OAuthGuide():
    """OAuth2登录未注册时引导路由(来源于OAuth goto_signUp)，选择绑定已有账号或直接登录(首选)"""
    if request.method == 'POST':
        Action = request.args.get("Action")
        sso = request.args.get("sso") or None
        logger.debug("OAuthGuide, sso type: {}, content: {}".format(type(sso), sso))
        res = dict(msg=None, code=1)
        if Action == "bindLogin":
            if True:
                auth = Authentication()
                result = auth.oauth2_bindLogin(openid=request.form.get("openid"), account=request.form.get("account"), password=request.form.get("password"))
                if result["success"]:
                    # 记录登录日志
                    auth.brush_loginlog(result, login_ip=g.ip, user_agent=g.agent)
                    sso_isOk, sso_returnUrl, sso_appName = checkGet_ssoRequest(sso)
                    sessionId, returnUrl = checkSet_ssoTicketSid(sso_isOk, sso_returnUrl, sso_appName, result["uid"], url_for("front.userset", _anchor="bind"))
                    logger.debug("OAuthGuide bindLogin post returnUrl: {}".format(returnUrl))
                    res.update(nextUrl=returnUrl, code=0)
                    return set_jsonifyLoginstate(sessionId, dfr(res))
                    #return set_redirectLoginstate(sessionId, returnUrl)
                else:
                    res.update(msg=result["msg"])
            else:
                res.update(msg="Man-machine verification failed")
            return jsonify(dfr(res))
            #return redirect(url_for('.OAuthBindAccount', openid=openid, sso=sso))
        elif Action == "directLogin":
            auth = Authentication()
            # 直接注册新账号并设置登录态
            result = auth.oauth2_signUp(request.form.get("openid"), g.ip)
            if result["success"]:
                # 记录登录日志
                auth.brush_loginlog(result, login_ip=g.ip, user_agent=request.headers.get("User-Agent"))
                sso_isOk, sso_returnUrl, sso_appName = checkGet_ssoRequest(sso)
                sessionId, returnUrl = checkSet_ssoTicketSid(sso_isOk, sso_returnUrl, sso_appName, result["uid"], url_for("front.userset", _anchor="bind"))
                logger.debug("OAuthGuide directLogin post returnUrl: {}".format(returnUrl))
                res.update(nextUrl=returnUrl, code=0)
                return set_jsonifyLoginstate(sessionId, dfr(res))
                #return set_redirectLoginstate(sessionId, returnUrl)
            else:
                res.update(msg=result["msg"])
            return jsonify(dfr(res))
            #return redirect(url_for("front.OAuthGuide", openid=openid, sso=sso))
    else:
        if request.args.get("openid"):
            return render_template("auth/OAuthGuide.html")
        else:
            return redirect(g.redirect_uri)

@FrontBlueprint.route("/signOut")
@login_required
def signOut():
    """ 单点注销流程
        1. 根据sid查找注册的clients
        2. pop一个client并跳转到其注销页面，携带参数为`NextUrl=当前路由地址`，如果有`ReturnUrl`同样携带。
           client处理：检测通过注销局部会话并跳转回当前路由
        3. 循环第2步，直到clients为空（所有已注册的局部会话已经注销）
        4. 注销本地全局会话，删除相关数据，跳转到登录页面
    """
    # 最终跳转回地址
    ReturnUrl = request.args.get("ReturnUrl") or url_for(".signOut", _external=True)
    if g.sid:
        clients = g.api.usersso.ssoGetRegisteredClient(g.sid)
        logger.debug("has sid, get clients: {}".format(clients))
        if clients and isinstance(clients, list) and len(clients) > 0:
            clientName = clients.pop()
            clientData = g.api.userapp.getUserApp(clientName)
            if clientData:
                if g.api.usersso.clearRegisteredClient(g.sid, clientName):
                    NextUrl = "{}/sso/authorized?{}".format(clientData["app_redirect_url"].strip("/"), urlencode(dict(Action="ssoLogout", ReturnUrl=ReturnUrl, app_name=clientName)))
                    return redirect(NextUrl)
            return redirect(url_for(".signOut"))
    # 没有sid时，或者存在sid已经注销到第4步
    g.api.usersso.clearRegisteredUserSid(g.uid, g.sid)
    response = make_response(redirect(ReturnUrl))
    response.set_cookie(key='sessionId', value='', expires=0)
    return response

@FrontBlueprint.route("/unbind")
@login_required
def unbind():
    # 解绑账号
    identity_name = request.args.get("identity_name")
    if identity_name:
        auth = Authentication(g.mysql, g.redis)
        res = auth.unbind(g.uid, oauth2_name2type(identity_name))
        res = dfr(res)
        if res["code"] == 0:
            flash(u"解绑成功")
        else:
            flash(res["msg"])
    else:
        flash(u"无效参数")
    return redirect(url_for("front.userset", _anchor="bind"))

@FrontBlueprint.route("/forgotpass/")
@anonymous_required
def fgp():
    # 忘记密码重置页
    return render_template("auth/forgot.html")

@FrontBlueprint.route("/terms.html")
def terms():
    # 服务条款
    return render_template("public/terms.html")

@FrontBlueprint.route("/feedback.html")
def feedback():
    # 意见反馈
    return render_template("public/feedback.html")
