"""Agent for updating company knowledge base from new information sources."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List

import pytz
from opik import track
from pydantic import BaseModel

from database.utils import db_manager
from prompts.agents.knowledge import get_knowledge_update_prompt
from tools.llm_api import aquery_llm
from utils.stock_utils import stock_id_to_name

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KnowledgeUpdateResponse(BaseModel):
    """Response from the Knowledge Update Agent."""

    updated_instruction: str


class KnowledgeUpdateAgent:
    """Agent responsible for maintaining and updating company knowledge."""

    AGENT_NAME = "knowledge_update_agent"  # Unique identifier for this agent
    DEFAULT_BATCH_SIZE = 3  # Default number of reports to process in one run
    UPDATE_INTERVAL = timedelta(hours=12)  # Minimum time between updates

    def __init__(
        self,
        collection: str = "company_knowledge",
        new_knowledge_collection: str = "investment_reports",
        provider: str = "openai",
        model: str = "o3-mini",
        batch_size: int = DEFAULT_BATCH_SIZE,
    ):
        """Initialize the Knowledge Update Agent.

        Args:
            collection: The name of the collection to store company knowledge.
            new_knowledge_collection: The name of the collection containing new reports.
            provider: The LLM provider to use.
            model: The specific model to use from the provider.
            batch_size: Maximum number of reports to process in one run. Defaults to DEFAULT_BATCH_SIZE.
        """
        self.collection = collection
        self.new_knowledge_collection = new_knowledge_collection
        self.provider = provider
        self.model = model
        self.batch_size = batch_size

    async def _fetch_unprocessed_reports(self) -> List[Dict]:
        """Fetch all unprocessed reports from MongoDB investment_reports collection."""
        try:
            # Construct the query to match individual stock analysis reports
            # that haven't been processed by this agent yet
            query = {
                "filters.report_type.level_1": "個股分析",  # Only individual stock analysis
                "$or": [
                    {
                        "processed_by_agents": {"$exists": False}
                    },  # No processed_by_agents field
                    {
                        "processed_by_agents": {"$ne": self.AGENT_NAME}
                    },  # Not processed by this agent
                ],
            }

            # Log the full query for debugging
            logger.info(f"Full query: {json.dumps(query, ensure_ascii=False)}")

            # Fetch reports
            reports = db_manager.get_data(
                db_type="mongo",
                key="filters",
                query=query,
                collection_or_table=self.new_knowledge_collection,
            )

            if not reports:
                logger.info("No reports found")
                return []

            # Convert to list if single report
            if not isinstance(reports, list):
                reports = [reports]

            # Sort reports by publish date
            sorted_reports = sorted(
                reports,
                key=lambda x: x["filters"]["metadata"]["publish_date"],
                reverse=True,
            )

            # Filter reports that need updating
            current_time = datetime.now(pytz.UTC)  # Use UTC timezone
            filtered_reports = []

            for report in sorted_reports:
                company_code = report["filters"]["report_type"]["level_4"].split(".")[0]
                last_update = await self._get_last_update_time(company_code)

                # Convert last_update to UTC if it's naive
                if last_update.tzinfo is None:
                    last_update = pytz.UTC.localize(last_update)

                if (current_time - last_update) > self.UPDATE_INTERVAL:
                    filtered_reports.append(report)
                    if len(filtered_reports) >= self.batch_size:
                        break

            if filtered_reports:
                logger.info(
                    f"Found {len(filtered_reports)} reports needing updates (from total {len(sorted_reports)})"
                )
            else:
                logger.info("No reports need updating at this time")

            return filtered_reports

        except Exception as e:
            logger.error(f"Error fetching reports: {str(e)}")
            return []

    async def _get_last_update_time(self, company_code: str) -> datetime:
        """Get the last update time for a company from the knowledge collection.

        Returns datetime.min if no data exists for the company.
        """
        try:
            # Construct query to find company knowledge
            query = {"company_code": company_code}

            # Fetch from MongoDB
            result = db_manager.get_data(
                db_type="mongo",
                key="company_code",
                query=query,
                collection_or_table=self.collection,
            )

            if not result:
                return pytz.UTC.localize(datetime.min)

            # If multiple documents exist, get the latest one
            if isinstance(result, list):
                # Convert last_updated strings to datetime objects before sorting
                sorted_results = sorted(
                    result,
                    key=lambda x: (
                        datetime.fromisoformat(x["last_updated"])
                        if "last_updated" in x
                        else datetime.min
                    ),
                    reverse=True,
                )
                result = sorted_results[0] if sorted_results else None

            if result and "last_updated" in result:
                dt = datetime.fromisoformat(result["last_updated"])
                # Ensure timezone awareness
                return dt if dt.tzinfo else pytz.UTC.localize(dt)

            return pytz.UTC.localize(datetime.min)

        except Exception as e:
            logger.error(f"Error getting last update time for {company_code}: {str(e)}")
            return pytz.UTC.localize(datetime.min)

    async def _save_knowledge(self, company_code: str, content: str):
        """Save updated knowledge to MongoDB."""
        try:
            # Prepare update document for MongoDB
            update = {
                "company_code": company_code,  # Include company_code in update
                "content": content,
                "last_updated": datetime.now(pytz.UTC).isoformat(),  # Use UTC time
                "company_name": stock_id_to_name(company_code),
            }

            # Update MongoDB using upsert
            success = db_manager.update_data(
                db_type="mongo",
                collection_or_table=self.collection,
                query={"company_code": company_code},
                update=update,
                key="company_code",
            )

            if not success:
                logger.error(f"Failed to save knowledge for company {company_code}")

        except Exception as e:
            logger.error(f"Error saving knowledge for {company_code}: {str(e)}")
            raise

    async def _mark_report_as_processed(self, report_id: str):
        """Mark a report as processed by this agent in MongoDB.

        Args:
            report_id: The file_id of the processed report
        """
        try:
            # Get current document
            result = db_manager.get_data(
                db_type="mongo",
                key="file_id",
                query={"file_id": report_id},
                collection_or_table=self.new_knowledge_collection,
            )

            if not result:
                logger.error(f"Could not find report {report_id} to mark as processed")
                return

            # Convert to list if single document
            if not isinstance(result, list):
                result = [result]

            document = result[0]

            # Add this agent to processed_by_agents if not already there
            processed_by_agents = document.get("processed_by_agents", [])
            if self.AGENT_NAME not in processed_by_agents:
                processed_by_agents.append(self.AGENT_NAME)

                # Update document in MongoDB
                success = db_manager.update_data(
                    db_type="mongo",
                    collection_or_table=self.new_knowledge_collection,
                    query={"file_id": report_id},
                    update={"processed_by_agents": processed_by_agents},
                    key="file_id",
                )

                if not success:
                    logger.error(f"Failed to mark report {report_id} as processed")

        except Exception as e:
            logger.error(f"Error marking report as processed: {str(e)}")

    async def _process_single_report(self, report: Dict):
        """Process a single report and update company knowledge.

        Args:
            report: The report document to process
        """
        try:
            # Extract company code from the report
            company_code = report["filters"]["report_type"]["level_4"].split(".")[0]

            # Read current knowledge for this company
            current_knowledge = await self._read_knowledge(company_code)

            # Get update prompt
            prompt = get_knowledge_update_prompt(
                current_knowledge=current_knowledge,
                new_content=report["contents"],
                company_name=stock_id_to_name(company_code),
            )

            # Query LLM for updates
            messages = [{"role": "user", "content": prompt}]
            response, _ = await aquery_llm(
                messages=messages,
                model=self.model,
                provider=self.provider,
                response_format=KnowledgeUpdateResponse,
            )

            json_response = json.loads(response.choices[0].message.content)
            updated_instruction = KnowledgeUpdateResponse(
                **json_response
            ).updated_instruction

            # Save updates
            await self._save_knowledge(company_code, updated_instruction)

            # Mark report as processed by this agent
            await self._mark_report_as_processed(report["file_id"])

            logger.info(f"Successfully processed report for company {company_code}")

        except Exception as e:
            logger.error(f"Error processing report: {str(e)}")

    @track(project_name="knowledge_update_agent")
    async def process_unprocessed_reports(self):
        """Process all unprocessed reports and update company knowledge concurrently."""
        try:
            # Fetch reports that need updating
            reports = await self._fetch_unprocessed_reports()
            if not reports:
                logger.info("No reports to process")
                return

            logger.info(f"Found {len(reports)} reports to process")

            # Process reports concurrently using asyncio.gather
            await asyncio.gather(
                *[self._process_single_report(report) for report in reports]
            )

        except Exception as e:
            logger.error(f"Error in process_unprocessed_reports: {str(e)}")

    async def _read_knowledge(self, company_code: str) -> str:
        """Read current knowledge from MongoDB company_knowledge collection."""
        try:
            # Construct query to find company knowledge
            query = {"company_code": company_code}

            # Fetch from MongoDB
            result = db_manager.get_data(
                db_type="mongo",
                key="company_code",
                query=query,
                collection_or_table="company_knowledge",
            )

            if not result:
                logger.info(f"No existing knowledge found for company {company_code}")
                return ""

            # If multiple documents exist (shouldn't happen due to unique key), get the latest one
            if isinstance(result, list):
                sorted_results = sorted(
                    result, key=lambda x: x["last_updated"], reverse=True
                )
                return sorted_results[0]["content"] if sorted_results else ""

            return result["content"]

        except Exception as e:
            logger.error(f"Error reading knowledge for {company_code}: {str(e)}")
            return ""
