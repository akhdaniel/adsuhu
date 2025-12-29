{
    'name': "Audio video Player Widget",
    'author': 'Odoocrafts LLP',
    'version': "0.1",
    'sequence': "0",
    'depends': ['base','web'],
    'data': [
    ],
    "assets": {
        "web.assets_backend": [
            'audio_player_widget/static/src/views/fields/audio_player/audio_player.scss',
            'audio_player_widget/static/src/views/fields/audio_player/audio_player.xml',
            'audio_player_widget/static/src/views/fields/audio_player/audio_player.js',
            'audio_player_widget/static/src/views/fields/video_player/video_player.scss',
            'audio_player_widget/static/src/views/fields/video_player/video_player.xml',
            'audio_player_widget/static/src/views/fields/video_player/video_player.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'demo': [],
    'summary': "Audio Player Widget",
    'description': "Audio Player Widget",
    'installable': True,
    'auto_install': False,
    'license': "LGPL-3",
    'application': False
}