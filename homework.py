import os
import time
from typing import Any

import requests
import telegram
import logging
import excepts
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('TOKEN_PRACTICUM')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('my_logger.log', maxBytes=50000000,
                              backupCount=5)
logger.addHandler(handler)


def send_message(bot, message) -> Any:
    """Отправляем сообщение об изменении статуса."""
    logger.info('Запущен процесс отправки сообщения')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Сообщение отправлено')
    except excepts.EcxeptSendMessage('Не удалось отправить сообщение'):
        logger.error('Не удалось отправить сообщение')


def get_api_answer(current_timestamp):
    """Получаем дынные с API Яндекс Практикума."""
    request_params = {
        'url': ENDPOINT,
        'headers': {'Authorization': f'OAuth {PRACTICUM_TOKEN}'},
        'params': {'from_date': current_timestamp or int(time.time())}
    }
    try:
        response = requests.get(
            **request_params
        )
        logger.info('Получаем информацию API')
        if response.status_code != 200:
            error_message = f'Запрос к ресурсу ' \
                            f'{ENDPOINT}' \
                            f'код ответа - {response.status_code}'
            bot = telegram.Bot(token=TELEGRAM_TOKEN)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=error_message)
            raise excepts.WrongAPIResponseCodeError(error_message)
        return response.json()
    except excepts.EcxeptGetApi('Не удалось получить API данные'):
        logger.error('Не удалось получить API данные')


def check_response(response):
    """Проверяем полученные данные."""
    logger.info('Проверяем полученные данные.')
    if not response or not isinstance(
            response['homeworks'], list):
        error_message = (
            'Ошибка ключа homeworks или response'
            'имеет неправильное значение.')
        logger.error(error_message)
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        send_message(bot, error_message)
        raise excepts.StatusHomeworkNameIsNone(error_message)
    return response['homeworks']


def parse_status(homework):
    """Проверяем изменился ли статус."""
    status = homework.get('status')
    homework_name = homework.get('homework_name')
    if status is None:
        raise excepts.StatusHomeworkNameIsNone('Ключ status не найден')
    if HOMEWORK_STATUSES[status] is None:
        raise excepts.StatusHomeworkNameIsNone(
            'Ключ status не найден в списке статусов'
        )
    verdict = HOMEWORK_STATUSES[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Прооверяем наличие переменных окружения."""
    status_bool_token = True
    fail = 'Ошибка переменных окружения'
    if not TELEGRAM_TOKEN:
        logging.critical(f'{fail} TELEGRAM_TOKEN')
        status_bool_token = False
        return status_bool_token
    if not PRACTICUM_TOKEN:
        logging.critical(f'{fail} PRACTICUM_TOKEN')
        status_bool_token = False
        return status_bool_token
    if not TELEGRAM_CHAT_ID:
        logging.critical(f'{fail} TELEGRAM_CHAT_ID')
        status_bool_token = False
    return status_bool_token


def main():
    """Основная логика работы бота."""
    first_object = 0
    check_tokens()
    if not check_tokens():
        exit()
        logger.critical('Не найден один из токенов')
        raise excepts.TelegramError('Не найден один из токенов')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    status = []
    current_report = {}
    prev_report = {}
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework != status:
                homework = homework[first_object]
                if homework.get('id') != status:
                    message = parse_status(homework)
                    current_timestamp = int(time.time())
                    send_message(bot, message)
            status = homework
        except excepts.NotForSendingError as error:
            logging.error(error)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            current_report['output'] = message
            logging.error(message, exc_info=True)
            if current_report != prev_report:
                send_message(bot, current_report)
                prev_report = current_report.copy()
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
