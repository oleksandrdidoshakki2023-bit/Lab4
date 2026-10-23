import sys
import os

# Додаємо src/ до шляху Python, щоб тести могли імпортувати notes та app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
