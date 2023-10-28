import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import hashlib
from colorama import Fore, Style
import pyfiglet
import time

def parse_args():
    parser = argparse.ArgumentParser(description='Web Scraper')
    parser.add_argument('-u', '--url', help='The target URL to start crawling', required=True)
    parser.add_argument('-mx', '--maxpages', type=int, default=100, help='Maximum number of pages to crawl (default: 100)')
    return parser.parse_args()

def fetch_and_parse(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return response.text, soup
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Failed to fetch {url}: {str(e)}{Style.RESET_ALL}")
    return None, None

def download_media(url, media_type, content):
    if not os.path.exists(media_directory):
        os.makedirs(media_directory, exist_ok=True)

    media_extension = url.split('.')[-1]
    media_filename = f"{media_directory}/{media_type}_{hashlib.md5(url.encode()).hexdigest()}.{media_extension}"
    with open(media_filename, 'wb') as file:
        file.write(content)
    print(f"{Fore.GREEN}Downloaded {media_type}: {url}{Style.RESET_ALL}")

def download_with_retry(url, filepath):
    retry_count = 3
    skip_urls = ["https://www.googletagmanager.com/gtag/js?id=UA-44051664-10"]
    if url in skip_urls:
        print(f"{Fore.YELLOW}Skipping URL: {url}{Style.RESET_ALL}")
        return False
    
    while retry_count > 0:
        try:
            response = requests.get(url)
            response.raise_for_status()

            with open(filepath, 'wb') as file:
                file.write(response.content)
            print(f"{Fore.GREEN}Downloaded: {url}{Style.RESET_ALL}")
            return True

        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}Error downloading {url}: {str(e)}{Style.RESET_ALL}")
            retry_count -= 1
            if retry_count > 0:
                print(f"{Fore.YELLOW}Retrying... Attempts left: {retry_count}{Style.RESET_ALL}")
                time.sleep(2)  # Delay before retrying
            else:
                print(f"{Fore.RED}Failed to download {url} after multiple attempts.{Style.RESET_ALL}")
                return False

if __name__ == '__main__':
    args = parse_args()
    start_url = args.url
    max_pages = args.maxpages

    target_dir_name = start_url.split('//')[-1]
    media_directory = os.path.join(target_dir_name, 'media')
    webdocs_directory = os.path.join(target_dir_name, 'webdocs')

    os.makedirs(media_directory, exist_ok=True)
    os.makedirs(webdocs_directory, exist_ok=True)

    os.system('cls' if os.name == 'nt' else 'clear')

    banner = pyfiglet.Figlet(font='slant')
    print(Fore.YELLOW + banner.renderText('Wev Dexer') + Style.RESET_ALL)
    print(Fore.GREEN + '* * * * Website Asset and Source Code Scraper * * * *\n' + Style.RESET_ALL)
    print(Fore.YELLOW + 'Target: ' + Fore.RED + '' + start_url + Style.RESET_ALL)
    print(Fore.YELLOW + 'Max Pages: ' + Fore.RED + '' + str(max_pages) + Style.RESET_ALL)
    print('')
    print(Fore.YELLOW + 'Master Directory: ' + Fore.RED + '' + target_dir_name + Style.RESET_ALL)
    print(Fore.YELLOW + 'Media Directory: ' + Fore.RED + '' + media_directory + Style.RESET_ALL)
    print(Fore.YELLOW + 'Webdocs Directory: ' + Fore.RED + '' + webdocs_directory + Style.RESET_ALL)
    print('')

    visited_urls = set()
    to_crawl = [start_url]

    try:
        while to_crawl and (len(visited_urls) < max_pages):
            current_url = to_crawl.pop(0)
            visited_urls.add(current_url)

            try:
                page_source, soup = fetch_and_parse(current_url)
            except Exception as e:
                print(f"{Fore.RED}Error fetching {current_url}: {str(e)}{Style.RESET_ALL}")
                continue

            if soup:
                for media_tag in soup.find_all(['img', 'video', 'audio']):
                    media_url = media_tag.get('src') or media_tag.get('href')
                    if media_url and not media_url.startswith("data:"):
                        absolute_media_url = urljoin(current_url, media_url)
                        try:
                            media_response = requests.get(absolute_media_url)
                            media_response.raise_for_status()
                            download_media(absolute_media_url, media_tag.name, media_response.content)
                        except Exception as e:
                            print(f"{Fore.RED}Error downloading {absolute_media_url}: {str(e)}{Style.RESET_ALL}")

                page_filename = f"{webdocs_directory}/{current_url.replace('https://', '').replace('/', '_')}.html"
                with open(page_filename, 'w', encoding='utf-8') as file:
                    file.write(page_source)
                print(f"{Fore.BLUE}Saved HTML source to: {page_filename}{Style.RESET_ALL}")

                for link in soup.find_all('a'):
                    href = link.get('href')
                    absolute_url = urljoin(current_url, href)
                    if absolute_url not in visited_urls and absolute_url not in to_crawl:
                        if absolute_url.startswith("data:"):
                            print(f"{Fore.YELLOW}Skipped data URI link: {absolute_url}{Style.RESET_ALL}")
                        else:
                            to_crawl.append(absolute_url)

                css_directory = os.path.join(webdocs_directory, 'css')
                js_directory = os.path.join(webdocs_directory, 'js')

                os.makedirs(css_directory, exist_ok=True)
                os.makedirs(js_directory, exist_ok=True)

                for css_tag in soup.find_all('link', rel='stylesheet'):
                    css_url = css_tag.get('href')
                    if css_url:
                        absolute_css_url = urljoin(current_url, css_url)
                        filename = absolute_css_url.split('/')[-1].split('?')[0]
                        css_filepath = os.path.join(css_directory, filename)

                        success = download_with_retry(absolute_css_url, css_filepath)
                        if not success:
                            continue

                for js_tag in soup.find_all('script', src=True):
                    js_url = js_tag.get('src')
                    if js_url:
                        absolute_js_url = urljoin(current_url, js_url)
                        filename = absolute_js_url.split('/')[-1].split('?')[0]
                        js_filepath = os.path.join(js_directory, filename)

                        success = download_with_retry(absolute_js_url, js_filepath)
                        if not success:
                            continue

    except KeyboardInterrupt:
        print(f"{Fore.RED}Crawling interrupted by the user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}An error occurred during crawling: {str(e)}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Crawling completed.{Style.RESET_ALL}")
