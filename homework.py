import os
import time
import requests
import telegram
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('TOKEN_PRACTICUM')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = 158736865

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
BOT = telegram.Bot(token=TELEGRAM_TOKEN)
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


class HTTPCodeError(Exception):
    """Исключение при ошибке непредвиденного ответа от ресурса."""


class EmptyDictionaryOrListError(Exception):
    """Исключение при ошибке homeworks в ответе."""


class StatusHomeworkNameIsNone(Exception):
    """Исключение при ошибке ключей в ответе."""


def send_message(bot, message):
    """Отправляем сообщение об изменении статуса."""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    """Получаем дынные с API Яндекс Практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        error_message = f'Не ожиданый ответа - {response.status_code}'
        logger.error(error_message)
        send_message(BOT, error_message)
        raise HTTPCodeError(error_message)
    return response.json()


def check_response(response):
    """Проверяем полученные данные."""
    if response['homeworks'] is None:
        error_message = (
            'Ошибка ключа homeworks или response'
            'имеет неправильное значение.')
        logger.error(error_message)
        send_message(BOT, error_message)
        raise EmptyDictionaryOrListError(error_message)
    if not response['homeworks']:
        return {}
    return response['homeworks'][0]


def parse_status(homework):
    """Анализируем статус если изменился."""
    status = homework.get('status')
    homework_name = homework.get('homework_name')
    if status is None:
        StatusHomeworkNameIsNone(
            'Ошибка пустое значение status: ', status)
    if homework_name is None:
        StatusHomeworkNameIsNone(
            'Ошибка пустое значение homework_name: ', homework_name)
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
    check_tokens()
    current_timestamp = int(time.time())
    status = {}
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework != status:
                if homework.get('id') != status.get('id'):
                    message = parse_status(homework)
                    current_timestamp = int(time.time())
                    send_message(BOT, message)
                    logger.info(f'Сообщение <{message}> успешно отправлено')
            time.sleep(RETRY_TIME)
            status = homework

        except Exception as error:
            logger.error(f'сбой при отправке сообщения в Telegram {error}')
            message = f'Сбой в работе программы: {error}'
            send_message(BOT, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
