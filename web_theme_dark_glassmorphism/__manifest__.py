{
    'name': 'Backend Dark Glassmorphism Theme',
    'summary': 'Dark glassmorphism-inspired backend look and feel',
    'category': 'Themes/Backend',
    'author': 'Hoang Minh Hieu',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'web',
    ],
    'data': [
    ],
    'assets': {
        'web._assets_primary_variables': [
            (
                'before',
                'web/static/src/scss/primary_variables.scss',
                'web_theme_dark_glassmorphism/static/src/scss/dark_glass_variables.scss',
            ),
        ],
        'web.assets_backend': [
            'web_theme_dark_glassmorphism/static/src/scss/dark_glassmorphism.scss',
        ],
    },
    'installable': True,
    'images': ['static/description/main_screenshot.png'],
}
