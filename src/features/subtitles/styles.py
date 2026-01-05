"""
Subtitle Style Presets
Defines available styles for FFmpeg burning.
"""

SUBTITLE_STYLES = {
    'default': {
        'name': 'Default (Verdana White)',
        'Fontname': 'Verdana',
        'PrimaryColour': '&H00FFFFFF', # White
        'OutlineColour': '&H60000000', # Semi-transparent black
        'BackColour': '&H00000000',
        'BorderStyle': 3,
        'Outline': 1,
        'Shadow': 0,
        'Bold': 1,
        'MarginV': 25
    },
    'bangers': {
        'name': 'Bangers (Yellow & Black)',
        'Fontname': 'Bangers',
        'PrimaryColour': '&H0000FFFF', # Yellow (AABBGGRR)
        'OutlineColour': '&H00000000', # Black
        'BackColour': '&H00000000',
        'BorderStyle': 1,
        'Outline': 2.5, # Thicker border
        'Shadow': 1,
        'Bold': 1,
        'MarginV': 30
    },
    'montserrat': {
        'name': 'Montserrat (ExtraBold Caps)',
        'Fontname': 'Montserrat ExtraBold',
        'PrimaryColour': '&H00FFFFFF', # White
        'OutlineColour': '&H00000000', # Black
        'BackColour': '&H00000000',
        'BorderStyle': 1,
        'Outline': 5, # Strong border (4-6px)
        'Spacing': -2, # Tracking/Spacing roughly -5 in tracking units
        'Shadow': 0,
        'Bold': 1,
        'MarginV': 35
    }
}
