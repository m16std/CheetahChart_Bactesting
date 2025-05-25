from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['joblib', 'tensorflow', 'numpy', 'pandas', 'PyQt5', 'pyqt-toast-notification', 'pyqtgraph', 'requests', 'scikit-learn', 'setuptools', 'ta'],  # Укажи пакеты, которые используются в приложении
    'iconfile': 'icon.icns',  
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
