# -*- coding: utf-8 -*-
{
    "name": "JSON Viewer",
    "summary": "Preview text fields as formatted JSON with syntax highlighting.",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "author": "ADS",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "vit_json_viewer/static/src/js/json_viewer_field.js",
            "vit_json_viewer/static/src/scss/json_viewer.scss",
            "vit_json_viewer/static/src/xml/json_viewer_templates.xml",
        ],
        "web.assets_qweb": [
            "vit_json_viewer/static/src/xml/json_viewer_templates.xml",
        ],
    },
    "installable": True,
}
