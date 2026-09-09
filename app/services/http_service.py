import requests  


# Return the response, allowing network and HTTP errors to reach the caller.
def get_http_response(url: str) -> requests.Response:
    response = requests.get(url)
    response.raise_for_status()
    return response
