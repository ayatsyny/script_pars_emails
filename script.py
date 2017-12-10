# coding=utf-8
import re
import requests
from requests import exceptions
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

IGNORE_FORMATS = ('.pdf', '.gif', '.jpg', '.png')
IGNORE_HREF_CONTEXT = ('#', 'javascript', 'mailto')

emails = set()


def get_site(start_url):
    site = start_url.split('//')[1]
    return site


def usage():
    print('usage:    Enter the url with the scheme(http, https) and the depth of the page search from the first url')
    print('          <str>url <int>depth([url1 [url2 [...]]])')
    print('example:  http://www.miet.ac.in 5')


def smoke_test(start_url):
    try:
        if start_url.startswith('http'):
            raise exceptions.MissingSchema
        requests.get(start_url)
    except (exceptions.MissingSchema, exceptions.ConnectionError):
        print('Error: not valid url addresses')
        usage()
        exit()


def spider_depth_with_pars_emails(start_url, depth):
    site = get_site(start_url)
    unprocessed_urls = [start_url]                  # a list of urls to be crawled
    error_urls = []                                 # error urls list
    processed_urls = set()                          # set of already crawled urls for email
    last_url = start_url                            # url when finished depth
    base_url = '{0.scheme}://{0.netloc}'.format(urlsplit(start_url))

    while len(unprocessed_urls):
        url = unprocessed_urls.pop(0)               # move next url from the list to the set of processed urls
        processed_urls.add(url)
        try:
            response = requests.get(url)
        except (exceptions.MissingSchema, exceptions.ConnectionError):
            error_urls.append(url)
            continue
        new_emails = set(re.findall(r'[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+', response.text, re.I))
        emails.update(new_emails)
        soup = BeautifulSoup(response.text, 'lxml')
        if not depth and (last_url in processed_urls or last_url in error_urls):
            return
        for anchor in soup.find_all('a'):
            link = anchor.get('href', '')
            netloc = urlsplit(link).netloc
            if (netloc and netloc not in site) or link.endswith(IGNORE_FORMATS) \
                    or any(link.startswith(c) for c in IGNORE_HREF_CONTEXT):
                continue
            if link.startswith('/'):
                link = base_url + link
            elif not link.startswith('http'):
                link = base_url + '/' + link
            if not link in unprocessed_urls and not link in processed_urls:     # add the new url to the list if it was
                unprocessed_urls.append(link)                       # not in unprocessed list nor in processed list yet
        if depth and unprocessed_urls and (last_url == url or last_url in error_urls):
            depth -= 1
            last_url = unprocessed_urls[-1]


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 3:
        usage()
        raise SystemExit

    start_url = sys.argv[1].strip()
    smoke_test(start_url)
    try:
        depth = int(sys.argv[2])
        if depth < 1:
            depth = 1
    except ValueError:
        print('Error: you need to enter the correct second argument')
        usage()
        raise SystemExit
    spider_depth_with_pars_emails(start_url, depth)
    if not emails:
        print("don't find any emails")
        exit()
    print(emails)
