"""
Original script: https://github.com/iw4p/proxy-scraper
"""

import re
import threading
import urllib.request
from time import time
from datetime import datetime
from fake_useragent import UserAgent
from termcolor import colored


class Proxy:
    def __init__(self, method, proxy):
        self.method = method
        self.proxy = proxy

    def is_valid(self):
        return re.match(r"\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?$", self.proxy)

    def check(self, user_agent):
        url = self.method + "://" + self.proxy
        proxy_support = urllib.request.ProxyHandler({self.method: url})
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)
        req = urllib.request.Request(self.method + "://" + "google.com")
        req.add_header("User-Agent", user_agent)
        try:
            start_time = time()
            urllib.request.urlopen(req, timeout=10.0)
            end_time = time()
            time_taken = end_time - start_time
            return True, time_taken, None
        except Exception as ex:
            return False, 0, ex

    def __str__(self):
        return self.proxy


def check(method):
    ua = UserAgent()
    check_date = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")

    proxies = []
    with open("output/output.txt", "r") as file:
        for line in file:
            proxies.append(Proxy(method, line.replace("\n", "")))

    print(colored(f"[CHECKER] | [INFO] | Started DDOS...", "green"))
    print(colored(f"[CHECKER] | [INFO] | Checking {len(proxies)} proxies\n", "green"))
    proxies = filter(lambda x: x.is_valid(), proxies)
    valid_proxies = []
    user_agent = ua.random

    def check_proxy(proxy, user_agent):
        new_user_agent = user_agent
        valid, time_taken, error = proxy.check(new_user_agent)
        message = {
            True: colored(f"\t[CHECKER] | [VALID]   | {proxy} is valid, took {time_taken} seconds", "green"),
            False: colored(f"\t[CHECKER] | [INVALID] | {proxy} is invalid: {repr(error)}", "red")

        }[valid]
        print(message)
        valid_proxies.extend([proxy] if valid else [])

    threads = []
    for proxy in proxies:
        t = threading.Thread(target=check_proxy, args=(proxy, user_agent))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # with open(f"output/valid_proxies-{check_date}.txt", "w") as file:
    with open("output/valid_proxies.txt", "w") as file:
        for proxy in valid_proxies:
            file.write(str(proxy) + "\n")

    print(colored(f"\n[CHECKER] | [INFO] | Found {len(valid_proxies)} valid proxies\n", "green"))


def run_checker(method):
    check(method)


if __name__ == '__main__':
    run_checker("http")
