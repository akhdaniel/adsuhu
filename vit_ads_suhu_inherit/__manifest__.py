#-*- coding: utf-8 -*-

{
	"name": "Ads Suhu - magic ads creator Inherited",
	"version": "1.0",
	"depends": [
		"base","web",
		"vit_ads_suhu",
		"audio_player_widget",
        "vit_json_viewer",
        "vit_md_viewer",
	],
	"author": "Akhmad Daniel Sembiring",
	"category": "Utility",
	"website": "http://vitraining.com",
	"images": [
		"static/description/images/main_screenshot.jpg"
	],
	"price": "100",
	"license": "OPL-1",
	"currency": "USD",
	"summary": "",
	"description": "",
    "assets": {
        "web.assets_backend": [
            "vit_ads_suhu_inherit/static/src/js/*.js",
            "vit_ads_suhu_inherit/static/src/xml/*.xml",
            "vit_ads_suhu_inherit/static/src/scss/*.scss",
        ],
    },
	"data": [
        "security/ir.model.access.csv",
        "security/ir.rule.xml",
        "data/params.xml",
        "data/prompt.xml",
        "data/gpts.xml",
        "data/gpt_model.xml",
		"view/res_users.xml",
		"view/product_value_analysis.xml",
		"view/market_mapper.xml",
		"view/audience_profiler.xml",
		"view/angle_hook.xml",
		"view/hook.xml",
		"view/ads_copy.xml",
		"view/script_writer.xml",
		"view/visual_concept.xml",
		"view/compliance_checker.xml",
		"view/landing_page_builder.xml",
		"view/campaign_builder.xml",
		"view/image_generator.xml",
		"view/video_director.xml"
	],
	"installable": True,
	"auto_install": False,
	"application": True,
	"odooVersion": 18
}
