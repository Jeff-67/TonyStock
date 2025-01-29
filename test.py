"""Module for crawling and cleaning web content from financial news sources."""

# mypy: ignore-errors

import asyncio
import re

from crawl4ai import AsyncWebCrawler


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


async def main():
    """Run the web crawler and clean the retrieved content."""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://finance.ettoday.net/news/2898977",
        )
        # Clean the markdown content
        cleaned_content = clean_markdown(result.markdown)
        print(cleaned_content)


if __name__ == "__main__":
    asyncio.run(main())
