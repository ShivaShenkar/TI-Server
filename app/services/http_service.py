import requests


def get_http_response(url:str)->requests.Response:
    response = requests.get(url)
    response.raise_for_status()
    return response