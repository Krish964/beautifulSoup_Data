import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import time
import json
import concurrent.futures

BASE_URL = "https://www.hindustantimes.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    )
}

# CSS selectors based on inspection — adjust if site layout changes
outerSectionID = "dataHolder"
divBox = "cartHolder"
anchorClass = "a"
h2Selector = "h2"
DateTimeDiv = "storyShortDetail"
dateTimeClass = "dateTime"

secondMainDivId = "storyMainDiv"
shortDescrip = "sortDec"  # Double-check this for typos like 'shortDec'
ImageOuterDiv = "storyDetails"
paragraphTag = "p"


def clean_paragraph(text):
    """
    Cleans paragraph text by:
    - Removing unwanted characters except basic punctuation.
    - Normalizing whitespace to single spaces.
    """
    text = re.sub(r'[\n\t\r]+', ' ', text)
    text = re.sub(r"[^a-zA-Z0-9\s.,?!']+", ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def scrape_outer_page(url):
    """
    Scrapes one outer page to extract list of articles with heading, anchor link and time.
    """
    print(f"Fetching outer page: {url}")
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    cards = soup.select(f"#{outerSectionID} .{divBox}")
    articles = []

    for card in cards:
        try:
            anchor = card.find(anchorClass)
            link = anchor["href"] if anchor and anchor.has_attr("href") else None
            if link and not link.startswith("http"):
                link = urljoin(BASE_URL, link)

            heading_el = card.find(h2Selector)
            heading = heading_el.get_text(strip=True) if heading_el else "No Heading"

            time_div = card.find(class_=DateTimeDiv)
            date_time = (
                time_div.find(class_=dateTimeClass).get_text(strip=True)
                if time_div and time_div.find(class_=dateTimeClass)
                else "No Date"
            )

            articles.append({
                "heading": heading,
                "anchorLink": link,
                "time": date_time
            })
        except Exception as e:
            print(f"⚠️ Error processing a card: {e}")

    return articles


def scrape_inner_page(url):
    """
    Scrapes inner article page for short description, image link, and cleaned paragraphs.
    """
    print(f"Fetching inner page: {url}")
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    short_content = "No short content found"
    image_link = ""
    paragraph = "No paragraph found"

    try:
        short_desc = soup.select_one(f"#{secondMainDivId} .{shortDescrip}")
        if short_desc:
            short_content = short_desc.get_text(strip=True)
    except Exception:
        pass

    try:
        image_outer_div = soup.select_one(f"#{secondMainDivId} .{ImageOuterDiv}")
        if image_outer_div:
            img_tag = image_outer_div.find("img")
            if img_tag and img_tag.has_attr("src"):
                image_link = img_tag["src"]
    except Exception:
        pass

    try:
        story_details_div = soup.select_one(f"#{secondMainDivId} .{ImageOuterDiv}")
        if story_details_div:
            paragraphs = story_details_div.find_all(paragraphTag)
            if paragraphs:
                raw_text = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                paragraph = clean_paragraph(raw_text)
    except Exception:
        pass

    return {
        "ShortContent": short_content,
        "ImageLink": image_link,
        "paragraph": paragraph
    }


def reorder_article(article):
    """
    Returns a new dict with keys in desired order for clean JSON output.
    """
    return {
        "id": article.get("id"),
        "heading": article.get("heading"),
        "ShortContent": article.get("ShortContent"),
        "time": article.get("time"),
        "ImageLink": article.get("ImageLink"),
        "anchorLink": article.get("anchorLink"),
        "paragraph": article.get("paragraph"),
    }


def scrape_hindustan(max_pages=7, max_workers=10):
    """
    Scrape multiple outer pages and concurrently scrape inner pages.

    Params:
    - max_pages: Number of India News pages to scrape (default 7)
    - max_workers: Number of parallel threads for inner scraping (default 10)

    Returns list of articles with all data.
    """
    all_articles = []

    for page_num in range(1, max_pages + 1):
        if page_num == 1:
            page_url = f"{BASE_URL}/india-news"
        else:
            page_url = f"{BASE_URL}/india-news/page-{page_num}"

        print(f"\n🔎 Scraping outer page {page_num}: {page_url}")
        page_articles = scrape_outer_page(page_url)
        print(f"Found {len(page_articles)} articles on page {page_num}")
        all_articles.extend(page_articles)

    print(f"\n⏳ Total articles found across {max_pages} pages: {len(all_articles)}")

    # Concurrently scrape inner article pages for details
    def enrich_article(article):
        link = article.get("anchorLink")
        if link:
            try:
                inner_data = scrape_inner_page(link)
                article.update(inner_data)
            except Exception as e:
                print(f"⚠️ Failed scraping inner page {link}: {e}")
        return article

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        all_articles = list(executor.map(enrich_article, all_articles))

    # Assign IDs and reorder keys before returning
    reordered_articles = []
    for idx, article in enumerate(all_articles, start=1):
        article["id"] = idx
        reordered_articles.append(reorder_article(article))

    print(f"✅ Completed scraping {len(reordered_articles)} articles with detailed info.")
    return reordered_articles


if __name__ == "__main__":
    start_time = time.perf_counter()
    data = scrape_hindustan(max_pages=7, max_workers=10)
    end_time = time.perf_counter()

    print(f"\nScraping finished in {end_time - start_time:.2f} seconds")
    print(json.dumps(data, indent=2, ensure_ascii=False))
