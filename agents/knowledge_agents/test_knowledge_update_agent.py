"""Main script to test KnowledgeUpdateAgent functionality."""

import asyncio
import logging
from typing import List

from agents.knowledge_agents.knowledge_update_agent import KnowledgeUpdateAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_auto_fetch_update(agent: KnowledgeUpdateAgent, company_codes: List[str]):
    """Test updating knowledge by auto-fetching from MongoDB."""
    logger.info("Testing auto-fetch update...")

    for company_code in company_codes:
        logger.info(f"Processing company {company_code}")
        try:
            # This will automatically fetch from MongoDB
            await agent.update_from_report(company_code)
        except Exception as e:
            logger.error(f"Error processing company {company_code}: {str(e)}")


async def test_direct_update(
    agent: KnowledgeUpdateAgent, company_code: str, new_content: str
):
    """Test updating knowledge with directly provided content."""
    logger.info("Testing direct content update...")

    try:
        await agent.update_from_report(company_code, new_content)
    except Exception as e:
        logger.error(f"Error updating company {company_code}: {str(e)}")


async def main():
    """Run the main test sequence for the KnowledgeUpdateAgent."""
    # Initialize agent
    agent = KnowledgeUpdateAgent()

    # Test cases
    company_codes = ["2454"]  # Example company codes

    # Test 1: Auto-fetch from MongoDB
    logger.info("=== Test 1: Auto-fetch from MongoDB ===")
    await test_auto_fetch_update(agent, company_codes)


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
