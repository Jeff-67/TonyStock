"""Module for crawling and cleaning web content from financial news sources."""

import asyncio
import json
import re
from typing import List

from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv
from opik import track
from pydantic import BaseModel

from tools.llm_api import aquery_llm

load_dotenv()


class FilteredContent(BaseModel):
    """Pydantic model for structured parsing of filtered content from LLM response.

    Attributes:
        filtered_content (str): The filtered and cleaned content extracted from the raw text.
        time (str): The time information extracted from the content.
    """

    filtered_content: str
    time: str


@track()
async def LLMfilter(scrapped_content: str, query: str) -> FilteredContent:
    """Filter the scrapped content by the query.

    Args:
        scrapped_content (str): The raw content to filter
        query (str): The query to filter with

    Returns:
        FilteredContent: A model containing the filtered content and time

    Note:
        In case of error, returns a FilteredContent with the original content
        and current timestamp.
    """
    prompt = f"""
    Given web-scraped raw content in Markdown format and a specific query, extract and return only the most relevant portion that may answer the query. Remove clearly irrelevant elements such as navigation menus, sidebars, and footer content, while preserving the exact language and structure of the original content.
    Here is the query: {query}
    Here is the scrapped content: {scrapped_content}

    return the filtered content and the time of the content.
    """
    try:
        # Format messages properly for LLM API
        messages = [{"role": "user", "content": prompt}]
        response, _ = await aquery_llm(
            messages=messages,
            model="gpt-4o-2024-08-06",
            provider="openai",
            response_format=FilteredContent,
        )
        json_response = json.loads(response.choices[0].message.content)
        return FilteredContent(**json_response)
    except Exception as e:
        print(f"Error parsing response: {str(e)}, response: {response}")
        # Return a FilteredContent with original content and current time
        from datetime import datetime

        return FilteredContent(
            filtered_content=scrapped_content, time=datetime.now().isoformat()
        )


def clean_markdown(text: str) -> str:
    """Clean markdown content by removing messy hyperlinks and formatting.

    Args:
        text (str): The markdown text to clean

    Returns:
        str: Cleaned text with hyperlinks removed
    """
    # Remove markdown links while keeping the text
    # This pattern matches [text](url) and keeps only the text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove any remaining URLs
    text = re.sub(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        "",
        text,
    )

    # Remove empty lines and excessive whitespace
    text = "\n".join(line.strip() for line in text.split("\n") if line.strip())

    return text


@track()
async def scrape_url(url: str, query: str, crawler: AsyncWebCrawler) -> str:
    """Run the web crawler and clean the retrieved content.

    Args:
        url (str): The URL to scrape
        query (str): The query to filter content with
        crawler (AsyncWebCrawler): The crawler instance to use

    Returns:
        str: A JSON string containing:
            - content: The filtered content relevant to the query
            - time: The time of the content
            - url: The source URL
    """
    result = await crawler.arun(url=url)
    # Clean the markdown content
    cleaned_content = clean_markdown(result.markdown)
    filtered_result = await LLMfilter(cleaned_content, query)
    # Create a dictionary with all the information we want to return
    response_dict = {
        "content": filtered_result.filtered_content,
        "time": filtered_result.time,
        "url": url,
    }
    return json.dumps(response_dict, ensure_ascii=False)


@track()
async def scrape_urls(urls: List[str], query: str) -> List[str]:
    """Process multiple URLs concurrently using AsyncWebCrawler.

    Args:
        urls: List of URLs to scrape
        query: Query to extract relevant content
        max_concurrent: Maximum number of concurrent crawlers

    Returns:
        List of cleaned markdown content strings, one per URL
    """
    async with AsyncWebCrawler() as crawler:  # Single shared crawler instance
        tasks = []
        for url in urls:
            task = scrape_url(url, query, crawler)  # Pass the shared crawler
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        return results


if __name__ == "__main__":
    # Test URLs - using known valid financial news URLs with different domains
    test_urls = [
        "https://finance.ettoday.net/news/2898977",  # ETtoday
        "https://money.udn.com/money/story/5607/7704246",  # UDN
    ]

    print("Starting to scrape URLs...")

    # Run scrape_urls and print results
    results = asyncio.run(scrape_urls(test_urls))

    # Print results for each URL
    for url, content in zip(test_urls, results):
        print(f"\n=== Content from {url} ===")
        print(content[:500] + "..." if len(content) > 500 else content)
        print("=" * 80)
