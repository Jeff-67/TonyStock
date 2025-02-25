"""Script to run the knowledge update agent."""

import asyncio
import logging

from agents.knowledge_agents.knowledge_update_agent import KnowledgeUpdateAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
BATCH_SIZE = 40  # Number of reports to process in one run


async def main():
    """Run the knowledge update agent to process unprocessed reports."""
    try:
        # Initialize the agent with configured batch size
        agent = KnowledgeUpdateAgent(batch_size=BATCH_SIZE)

        logger.info(f"Starting knowledge update with batch size: {BATCH_SIZE}")

        # Process unprocessed reports
        await agent.process_unprocessed_reports()

        logger.info("Knowledge update process completed")

    except Exception as e:
        logger.error(f"Error running knowledge update agent: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
