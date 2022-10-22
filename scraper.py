"""
Original script: https://github.com/iw4p/proxy-scraper
"""

import asyncio
import re
import time
import httpx
from bs4 import BeautifulSoup
from termcolor import colored


class Scraper:
    def __init__(self, method, _url):
        self.method = method
        self._url = _url

    def get_url(self, **kwargs):
        return self._url.format(**kwargs, method=self.method)

    async def get_response(self, client):
        return await client.get(self.get_url())

    async def handle(self, response):
        return response.text

    async def scrape(self, client):
        response = await self.get_response(client)
        proxies = await self.handle(response)
        pattern = re.compile(r'\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?')
        return re.findall(pattern, proxies)


# From spys.me
class SpysMeScraper(Scraper):

    def __init__(self, method):
        super().__init__(method, "https://spys.me/{mode}.txt")

    def get_url(self, **kwargs):
        mode = "proxy" if self.method == "http" else "socks" if self.method == "socks" else "unknown"
        if mode == "unknown":
            raise NotImplementedError
        return super().get_url(mode=mode, **kwargs)


# From proxyscrape.com
class ProxyScrapeScraper(Scraper):

    def __init__(self, method, timeout=1000, country="All"):
        self.timeout = timeout
        self.country = country
        super().__init__(method,
                         "https://api.proxyscrape.com/?request=getproxies"
                         "&proxytype={method}"
                         "&timeout={timout}"
                         "&country={country}")

    def get_url(self, **kwargs):
        return super().get_url(timout=self.timeout, country=self.country, **kwargs)


# From proxy-list.download
class ProxyListDownloadScraper(Scraper):

    def __init__(self, method, anon):
        self.anon = anon
        super().__init__(method, "https://www.proxy-list.download/api/v1/get?type={method}&anon={anon}")

    def get_url(self, **kwargs):
        return super().get_url(anon=self.anon, **kwargs)


# For websites using table in html
class GeneralTableScraper(Scraper):
    async def handle(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        proxies = set()
        table = soup.find("table", attrs={"class": "table table-striped table-bordered"})
        for row in table.findAll("tr"):
            count = 0
            proxy = ""
            for cell in row.findAll("td"):
                if count == 1:
                    proxy += ":" + cell.text.replace("&nbsp;", "")
                    proxies.add(proxy)
                    break
                proxy += cell.text.replace("&nbsp;", "")
                count += 1
        return "\n".join(proxies)


scrapers = [
    SpysMeScraper("http"),
    ProxyScrapeScraper("http"),
    ProxyListDownloadScraper("https", "elite"),
    ProxyListDownloadScraper("http", "transparent"),
    ProxyListDownloadScraper("http", "anonymous"),
    GeneralTableScraper("https", "http://sslproxies.org"),
    GeneralTableScraper("http", "http://free-proxy-list.net"),
    GeneralTableScraper("http", "http://us-proxy.org")
]


async def scrape(method):
    now = time.time()
    methods = [method]
    if method == "socks":
        methods += ["socks4", "socks5"]
    proxy_scrapers = [s for s in scrapers if s.method in methods]
    if not proxy_scrapers:
        raise ValueError("Method not supported. Only HTTPS")
    print(colored("[SCRAPER] | [INFO] | Scrapping proxies\n", "yellow"))

    proxies = []
    task = []
    client = httpx.AsyncClient(follow_redirects=True)

    async def scrape_scraper(scraper):
        # print(f"Locking {scraper.get_url()}...")
        print(colored(f"\t[SCRAPER] | [SITES] | Locking {scraper.get_url()}", "yellow"))
        proxies.extend(await scraper.scrape(client))

    for scraper in proxy_scrapers:
        task.append(asyncio.ensure_future(scrape_scraper(scraper)))

    await asyncio.gather(*task)
    await client.aclose()

    print(colored(f"\n[SCRAPER] | [SUCCESS] | Writing {len(proxies)} proxies to file", "green"))
    with open(f"output/output.txt", "w") as file:
        file.write("\n".join(proxies))
    print(colored(
        f"[SCRAPER] | [SUCCESS] | Done! Took {time.time() - now} second\n", "green"
    ))


def run_scraper(method):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(scrape(method))
    loop.close()


if __name__ == '__main__':
    run_scraper("http")
