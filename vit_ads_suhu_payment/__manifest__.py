#-*- coding: utf-8 -*-

{
    "name": "Ads Suhu - AI Token Payment",
    "version": "1.0",
    "depends": [
        "base",
        "account",
        "payment",
        "vit_ads_suhu_token",
    ],
    "author": "Akhmad Daniel Sembiring",
    "category": "Accounting",
    "website": "http://vitraining.com",
    "license": "OPL-1",
    "data": [
        "security/ir.model.access.csv",
        "view/account_move.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
    "odooVersion": 18
}
