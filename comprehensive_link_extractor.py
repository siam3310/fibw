
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import sys
import json
import re
from datetime import datetime

def find_all_watch_links(url: str, session) -> list:
    """
    Finds all unique links on a page that contain '/watch/' and end with '.html'.
    """
    print(f"Finding all 'watch' links on: {url}")
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)
        watch_links = set()

        for link in links:
            href = link.get('href')
            if not href:
                continue
            
            full_url = urljoin(url, href)

            if '/watch/' in full_url and full_url.endswith('.html'):
                watch_links.add(full_url)
        
        print(f"Found {len(watch_links)} unique watch links.")
        return list(watch_links)

    except Exception as e:
        print(f"Error fetching URL: {str(e)}")
        return []

def extract_media_info(url: str):
    """Extracts name, year, and quality from a media URL."""
    filename = url.split('/')[-1]
    # Remove the prefix and file extension
    cleaned_name = filename.replace('[Fibwatch.Com]', '').replace('.mkv', '').replace('.mp4', '')

    # Year extraction
    year_match = re.search(r'\((\d{4})\)', cleaned_name)
    year = year_match.group(1) if year_match else None

    # Quality extraction
    quality_match = re.search(r'(\d{3,4}p)', cleaned_name, re.IGNORECASE)
    quality = quality_match.group(1) if quality_match else None

    # Name extraction
    name = cleaned_name
    if year:
        name = name.replace(f'({year})', '')
    if quality:
        name = name.replace(quality, '')
    
    # Remove season/episode details
    name = re.split(r'S\d{1,2}E\d{1,4}|S\d{1,2}', name, flags=re.IGNORECASE)[0]

    name = name.replace('.', ' ').strip()

    return {
        "name": name,
        "year": year,
        "quality": quality,
        "link": url
    }

def find_media_links_on_page(url: str, session) -> list:
    """
    Scrapes a 'watch' page to find all actual media links (.mkv, .mp4) and returns a list of dicts with extracted info.
    """
    print(f"\nSearching for media links on: {url}")
    media_info_list = []
    found_links_on_this_page = set()
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        links = soup.find_all('a', href=True)

        for link in links:
            href = link.get('href')
            if not href:
                continue

            extracted_media_url = None

            if 'urlshortlink.top' in href:
                parsed_href = urlparse(href)
                query_params = parse_qs(parsed_href.query)
                redirect_url = query_params.get('url', [None])[0]
                if redirect_url and (redirect_url.endswith('.mkv') or redirect_url.endswith('.mp4')):
                    extracted_media_url = redirect_url
            
            elif href.endswith('.mkv') or href.endswith('.mp4'):
                extracted_media_url = urljoin(url, href)

            if extracted_media_url and extracted_media_url not in found_links_on_this_page:
                found_links_on_this_page.add(extracted_media_url)
                
                media_info = extract_media_info(extracted_media_url)
                media_info_list.append(media_info)
                print(f"  - Found: {media_info['name']} ({media_info['year']}) - {media_info['quality']}")

    except Exception as e:
        print(f"Error fetching page {url}: {str(e)}")
    
    return media_info_list

if __name__ == "__main__":
    base_url = "https://fibwatch.art/videos/latest"
    all_media_info = []
    all_collected_links = set()

    session = cloudscraper.create_scraper() # Use cloudscraper

    for page_number in range(1, 8):
        if page_number == 1:
            current_url = base_url
        else:
            current_url = f"{base_url}?page_id={page_number}"
        
        watch_links = find_all_watch_links(current_url, session)
        if not watch_links:
            print(f"\nNo more watch links found on page {page_number}. Ending scrape.")
            break
        
        for link in watch_links:
            media_on_page = find_media_links_on_page(link, session)
            for media_info in media_on_page:
                if media_info['link'] not in all_collected_links:
                    all_media_info.append(media_info)
                    all_collected_links.add(media_info['link'])

    if all_media_info:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        output_data = {
            "made_by": "@siam3310",
            "last_update_time": now,
            "scraped_media": all_media_info
        }

        with open('scraped-links.json', 'w') as json_file:
            json.dump(output_data, json_file, indent=4)
        print(f"\nSuccessfully saved {len(all_media_info)} unique media items to scraped-links.json")
    else:
        print("\nNo media links were found across all pages.")
