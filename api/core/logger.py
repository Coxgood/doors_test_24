"""
Настройка логирования для API.
"""
import logging
import sys
from datetime import datetime


def setup_logging():
    """Настраивает логирование: в файл и в консоль"""

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Логирование в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Логирование в файл
    file_handler = logging.FileHandler(f'api_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Отключаем лишние логи от библиотек
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

    return root_logger