import requests


def status_home_work(params, url, headers):
    homework_statuses = requests.get(url, headers=headers,
                                     params=params).json()
    return homework_statuses
