# -*- coding: utf-8 -*-
{
    "name": "Markdown Viewer",
    "summary": "Preview text fields as rendered Markdown.",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "author": "ADS",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "vit_md_viewer/static/src/js/md_viewer_field.js",
            "vit_md_viewer/static/src/scss/md_viewer.scss",
            "vit_md_viewer/static/src/xml/md_viewer_templates.xml",
        ],
        "web.assets_qweb": [
            "vit_md_viewer/static/src/xml/md_viewer_templates.xml",
        ],
    },
    "installable": True,
}
