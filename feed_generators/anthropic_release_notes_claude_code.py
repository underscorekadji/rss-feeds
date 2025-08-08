import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from feedgen.feed import FeedGenerator
import logging
from pathlib import Path
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_project_root():
    return Path(__file__).parent.parent


def ensure_feeds_directory():
    feeds_dir = get_project_root() / "feeds"
    feeds_dir.mkdir(exist_ok=True)
    return feeds_dir


def fetch_release_notes_content(url="https://docs.anthropic.com/en/release-notes/claude-code"):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Error fetching release notes content: {str(e)}")
        raise


def parse_date(date_text):
    date_text = re.sub(r'[^\w\s,]', '', date_text).strip()
    date_text = re.sub(r'(\d+)(?:st|nd|rd|th)', r'\1', date_text)
    
    try:
        date = datetime.strptime(date_text, "%B %d, %Y")
        return date.replace(tzinfo=pytz.UTC)
    except ValueError:
        logger.warning(f"Could not parse date: {date_text}")
        return None


def parse_release_notes_html(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        items = []

        for hdr in soup.find_all("h2"):
            date_text = hdr.get_text(" ", strip=True)
            date_obj = parse_date(date_text)
            if not date_obj:
                continue

            next_element = hdr.next_sibling
            while next_element:
                if next_element.name == "ul":
                    ul = next_element
                    break
                next_element = next_element.next_sibling
            else:
                ul = hdr.find_next("ul")

            if not ul:
                continue

            for li in ul.find_all("li", recursive=False):
                title = li.get_text(" ", strip=True)
                if not title:
                    continue
                
                items.append({
                    "title": title,
                    "link": "https://docs.anthropic.com/en/release-notes/claude-code",
                    "description": title,
                    "date": date_obj,
                    "category": "Release Notes",
                })

        logger.info(f"Successfully parsed {len(items)} release note items")
        return items

    except Exception as e:
        logger.error(f"Error parsing HTML content: {str(e)}")
        raise


def generate_rss_feed(items, feed_name="anthropic_release_notes_claude_code"):
    try:
        fg = FeedGenerator()
        fg.title("Anthropic — Claude Code Release Notes")
        fg.description("Updates to Claude Code from Anthropic docs.")
        fg.link(href="https://docs.anthropic.com/en/release-notes/claude-code")
        fg.language("en")

        fg.author({"name": "Anthropic"})
        fg.logo("https://www.anthropic.com/images/icons/apple-touch-icon.png")
        fg.subtitle("Claude Code Release Notes")
        fg.link(href="https://docs.anthropic.com/en/release-notes/claude-code", rel="alternate")
        fg.link(href=f"https://anthropic.com/feed_{feed_name}.xml", rel="self")

        items.sort(key=lambda x: x["date"], reverse=True)

        for item in items:
            fe = fg.add_entry()
            fe.title(item["title"])
            fe.description(item["description"])
            fe.link(href=item["link"])
            fe.published(item["date"])
            fe.category(term=item["category"])
            fe.id(f"{item['link']}#{hash(item['title'])}")

        logger.info("Successfully generated RSS feed")
        return fg

    except Exception as e:
        logger.error(f"Error generating RSS feed: {str(e)}")
        raise


def save_rss_feed(feed_generator, feed_name="anthropic_release_notes_claude_code"):
    try:
        feeds_dir = ensure_feeds_directory()
        output_filename = feeds_dir / f"feed_{feed_name}.xml"
        feed_generator.rss_file(str(output_filename), pretty=True)
        logger.info(f"Successfully saved RSS feed to {output_filename}")
        return output_filename
    except Exception as e:
        logger.error(f"Error saving RSS feed: {str(e)}")
        raise


def main(feed_name="anthropic_release_notes_claude_code"):
    try:
        html_content = fetch_release_notes_content()
        items = parse_release_notes_html(html_content)

        if not items:
            logger.warning("No release note items found")
            return False

        feed = generate_rss_feed(items, feed_name)
        output_file = save_rss_feed(feed, feed_name)

        logger.info(f"Successfully generated RSS feed with {len(items)} items")
        return True

    except Exception as e:
        logger.error(f"Failed to generate RSS feed: {str(e)}")
        return False


if __name__ == "__main__":
    main()