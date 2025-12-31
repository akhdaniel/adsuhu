{
    'name': 'AdSuhu Frontend',
    'version': '18.0.1.0.0',
    'summary': 'Website Frontend for AdSuhu Product Value Analysis',
    'description': """
        Modern website frontend for displaying Product Value Analysis and related data.
    """,
    'category': 'Website',
    'author': 'Your Name',
    'website': 'https://www.example.com',
    'depends': ['website', 'vit_ads_suhu'],
    'data': [
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'vit_adsuhu_frontend/static/src/css/style.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
