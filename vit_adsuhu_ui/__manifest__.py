{
    'name': 'AdSuhu UI',
    'version': '18.0.1.0.0',
    'summary': 'Modern OWL stepper UI for AdSuhu analysis pipeline',
    'description': """
        Reactive OWL/JavaScript frontend for the AdSuhu product analysis pipeline.
        Provides a guided stepper workflow with focus-mode stage views and
        real-time status updates over the Odoo bus.
    """,
    'category': 'Website',
    'author': 'AdSuhu',
    'website': 'https://www.example.com',
    'depends': [
        'website',
        'bus',
        'vit_ads_suhu',
        'vit_ads_suhu_inherit',
        'vit_adsuhu_frontend',
    ],
    'data': [
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'vit_adsuhu_ui/static/src/scss/variables.scss',
            'vit_adsuhu_ui/static/src/scss/base.scss',
            'vit_adsuhu_ui/static/src/scss/app.scss',
            'vit_adsuhu_ui/static/src/scss/dark.scss',
            'vit_adsuhu_ui/static/src/js/app.js',
            'vit_adsuhu_ui/static/src/js/components/stepper.js',
            'vit_adsuhu_ui/static/src/js/components/stage_view.js',
            'vit_adsuhu_ui/static/src/js/components/generate_button.js',
            'vit_adsuhu_ui/static/src/js/components/image_gallery.js',
            'vit_adsuhu_ui/static/src/xml/stepper.xml',
            'vit_adsuhu_ui/static/src/xml/stage_view.xml',
            'vit_adsuhu_ui/static/src/xml/generate_button.xml',
            'vit_adsuhu_ui/static/src/xml/image_gallery.xml',
            'vit_adsuhu_ui/static/src/xml/app.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
