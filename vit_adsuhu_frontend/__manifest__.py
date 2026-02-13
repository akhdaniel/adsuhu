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
    'depends': ['website', 
                'vit_ads_suhu',
                'vit_ads_suhu_credits'
                ],
    'data': [
        'views/templates.xml',
        'views/portal.xml',
        'views/web_brand_override.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'vit_adsuhu_frontend/static/src/css/style.css',
            'vit_adsuhu_frontend/static/src/js/product_analysis_detail.js',
            'vit_adsuhu_frontend/static/src/js/customer_credits.js',
            'vit_adsuhu_frontend/static/src/css/skeleton/index.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
