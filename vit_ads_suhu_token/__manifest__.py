#-*- coding: utf-8 -*-

{
    "name": "Ads Suhu - AI Token",
    "version": "1.0",
    "depends": [
        "base",
        "web",
        "product",
        "vit_ads_suhu_inherit",
    ],
    "author": "Akhmad Daniel Sembiring",
    "category": "Utility",
    "website": "http://vitraining.com",
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "data/ai_token.xml",
        "view/ai_token.xml",
        "view/res_users.xml",
        "view/product_template.xml",
        "view/product_value_analysis.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vit_ads_suhu_token/static/src/js/*.js",
            "vit_ads_suhu_token/static/src/xml/*.xml",
            "vit_ads_suhu_token/static/src/scss/*.scss",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
    "odooVersion": 18
}
