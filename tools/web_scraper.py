"""Web scraper module for extracting content from URLs.

This module provides functionality to scrape web content from URLs,
with support for concurrent requests, proxy rotation, and JavaScript rendering.
Can be used as a command-line tool or imported as a module.
"""

import argparse
import asyncio
import logging
import random
import sys
from typing import List, Optional, Dict, Union
import aiohttp
import time
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import os
from bs4 import BeautifulSoup
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 30
MAX_CONCURRENT = 5
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1

# Proxy configuration
PROXY_LIST = [
    'http://156.228.109.7:3128',
    'http://156.228.104.132:3128',
    'http://154.213.193.17:3128',
    'http://154.94.15.112:3128',
    'http://156.253.167.233:3128',
    'http://154.214.1.75:3128'
]

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Edge/120.0.0.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

async def validate_proxy(session: aiohttp.ClientSession, proxy: str) -> bool:
    """Validate if a proxy is working."""
    try:
        async with session.get(
            'http://www.google.com',
            proxy=proxy,
            timeout=5
        ) as response:
            return response.status == 200
    except Exception:
        return False

async def get_working_proxy() -> Optional[str]:
    """Get a working proxy from the proxy list."""
    async with aiohttp.ClientSession() as session:
        for proxy in PROXY_LIST:
            if await validate_proxy(session, proxy):
                return proxy
    return None

async def scrape_with_playwright(url: str, proxy: Optional[str] = None) -> Optional[Dict[str, str]]:
    """Scrape JavaScript-rendered content using Playwright."""
    try:
        async with async_playwright() as p:
            browser_args = [
                '--disable-web-security',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
            if proxy:
                browser_args.append(f'--proxy-server={proxy}')
            
            browser = await p.chromium.launch(
                args=browser_args,
                headless=True
            )
            
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1920, 'height': 1080}
            )
            
            try:
                page = await context.new_page()
                await page.goto(url, timeout=DEFAULT_TIMEOUT * 1000, wait_until='domcontentloaded')
                
                # Extract content immediately without scrolling
                content = await page.evaluate("""() => {
                    function extractMainContent() {
                        const selectors = [
                            'article',
                            'main',
                            '.article-content',
                            '.content',
                            '#content'
                        ];
                        
                        for (const selector of selectors) {
                            const element = document.querySelector(selector);
                            if (element && element.innerText.trim().length > 100) {
                                return element.innerText.trim();
                            }
                        }
                        
                        return document.body.innerText.trim();
                    }
                    
                    return {
                        title: document.title,
                        content: extractMainContent(),
                        url: window.location.href
                    };
                }""")
                
                return content
                
            except PlaywrightTimeout:
                logger.warning(f"Timeout while loading {url}")
                return None
            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                return None
            finally:
                await context.close()
                await browser.close()
                
    except Exception as e:
        logger.error(f"Fatal error scraping {url}: {str(e)}")
        return None

async def scrape_url(url: str, max_retries: int = 3) -> Optional[Dict[str, str]]:
    """
    Scrape content from a URL with retries and proxy support.
    Returns a dictionary containing title, date, and content if successful.
    """
    for attempt in range(max_retries):
        try:
            # Try without proxy first
            content = await scrape_with_playwright(url)
            if not content:
                # If failed, try with proxy
                proxy = await get_working_proxy()
                if proxy:
                    content = await scrape_with_playwright(url, proxy)
            
            if content:
                # Validate and clean content
                if not isinstance(content, dict):
                    logger.warning(f"Invalid content format from {url}")
                    continue
                    
                # Clean and validate each field
                cleaned_content = {
                    'title': content.get('title', '').strip(),
                    'date': content.get('date', ''),
                    'content': content.get('content', '').strip()
                }
                
                # Basic validation
                if not cleaned_content['content']:
                    logger.warning(f"No content extracted from {url}")
                    continue
                    
                cleaned_content['url'] = url
                return cleaned_content
                
            logger.warning(f"No content retrieved from {url} on attempt {attempt + 1}")
            
        except Exception as e:
            logger.error(f"Error scraping {url} on attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(1)  # Brief delay before retry
    
    return None

async def scrape_urls(urls: List[str], max_concurrent: int = 5) -> List[Dict[str, str]]:
    """
    Scrape multiple URLs concurrently.
    Returns a list of dictionaries containing title, date, and content for each successful scrape.
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_scrape(url: str) -> Optional[Dict[str, str]]:
        async with semaphore:
            return await scrape_url(url)
    
    tasks = [bounded_scrape(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    # Filter out None results and log statistics
    valid_results = [r for r in results if r is not None]
    logger.info(f"Successfully scraped {len(valid_results)}/{len(urls)} URLs")
    
    return valid_results

def main():
    """Main entry point for the web scraper."""
    parser = argparse.ArgumentParser(description='Scrape content from URLs')
    parser.add_argument('urls', nargs='+', help='URLs to scrape')
    parser.add_argument('--max-concurrent', type=int, default=5,
                      help='Maximum number of concurrent requests')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug logging')
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    results = asyncio.run(scrape_urls(args.urls, args.max_concurrent))
    
    # Print results in a structured format
    for result in results:
        print(f"\nURL: {result['url']}")
        print(f"Title: {result['title']}")
        if result['date']:
            print(f"Date: {result['date']}")
        print("\nContent:")
        print("-" * 80)
        print(result['content'])
        print("-" * 80)
        print()

if __name__ == '__main__':
    main()

