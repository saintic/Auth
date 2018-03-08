# -*- coding: utf-8 -*-
"""
    ProcessName_XXX.views.FrontView
    ~~~~~~~~~~~~~~

    The blueprint for front view.

    :copyright: (c) 2017 by staugur.
    :license: MIT, see LICENSE for more details.
"""

from flask import Blueprint, g


#初始化前台蓝图
FrontBlueprint = Blueprint("front", __name__)

@FrontBlueprint.route('/')
def index():
    #首页
    return u"登录状态：{}".format(g.signin)
