SUPPORTED_LANGUAGES = {'en': 'English', 'hi': 'हिन्दी', 'bn': 'বাংলা', 'ta': 'தமிழ்', 'te': 'తెలుగు', 'mr': 'मराठी', 'gu': 'ગુજરાતી', 'kn': 'ಕನ್ನಡ', 'ml': 'മലയാളം', 'pa': 'ਪੰਜਾਬੀ'}


def normalize_language(value):
    value = (value or 'en').strip().lower()
    return value if value in SUPPORTED_LANGUAGES else 'en'
