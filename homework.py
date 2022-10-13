import os
import telegram
import time
from homework_api.api_praktikum import status_home_work
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
LAST_WORK = 0


def send_message(bot, message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    res = status_home_work(params, ENDPOINT, HEADERS)
    return res


def check_response(response):
    if isinstance(response, dict):
        if 'current_date' in response and 'homeworks' in response:
            return response['homeworks']
        else:
            raise IndexError('Не найден ключ current_date и/или homeworks')
    else:
        raise TypeError('Неверный тип данных')


def parse_status(homework):
    homework_name = homework[LAST_WORK]['lesson_name']
    homework_status = homework[LAST_WORK]['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if TELEGRAM_TOKEN and PRACTICUM_TOKEN:
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    status = []
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework != status:
                message = parse_status(homework)
                current_timestamp = int(time.time())
                send_message(bot, message)
            time.sleep(RETRY_TIME)
            status = homework

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
