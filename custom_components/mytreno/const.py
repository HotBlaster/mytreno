import aiohttp

DOMAIN = "mytreno"
URL_BASE = "https://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno"
SERVICE_SET_TRAIN = "set_train"

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.viaggiatreno.it/infomobilita/index.jsp",
}
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)
