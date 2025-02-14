"""Agent for updating company knowledge base from new information sources."""

import json
import logging
from datetime import datetime
from typing import Optional

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

    def __init__(
        self,
        collection: str = "company_knowledge",
        new_knowledge_collection: str = "investment_reports",
        provider: str = "openai",
        model: str = "o3-mini",
    ):
        """Initialize the Knowledge Update Agent.

        Args:
            collection: The name of the collection to store company knowledge.
            new_knowledge_collection: The name of the collection containing new reports.
            provider: The LLM provider to use.
            model: The specific model to use from the provider.
        """
        self.collection = collection
        self.new_knowledge_collection = new_knowledge_collection
        self.provider = provider
        self.model = model

    async def _fetch_latest_report(self, company_code: str) -> Optional[str]:
        """Fetch the latest report from MongoDB investment_reports collection."""
        try:
            # Construct the query to match only the known fields
            query = {
                "filters.report_type.level_1": "個股分析",
                "filters.report_type.level_4": f"{company_code}.TT",
            }

            # Log the full query for debugging
            logger.info(f"Full query: {json.dumps(query, ensure_ascii=False)}")

            # Fetch the latest report
            report = db_manager.get_data(
                db_type="mongo",
                key="filters",
                query=query,
                collection_or_table=self.new_knowledge_collection,
            )

            if not report:
                logger.info(f"No reports found for company {company_code}")
                return None

            # If multiple reports exist, get the latest one based on publish_date
            if isinstance(report, list):
                # Sort reports by publish_date - metadata is already a dict
                sorted_reports = sorted(
                    report,
                    key=lambda x: x["filters"]["metadata"]["publish_date"],
                    reverse=True,
                )
                return sorted_reports[0]["contents"] if sorted_reports else None

            return report["contents"]

        except Exception as e:
            logger.error(f"Error fetching report for {company_code}: {str(e)}")
            return None

    @track(project_name="knowledge_update_agent")
    async def update_from_report(
        self,
        company_code: str,
        new_knowledge: Optional[str] = None,
    ):
        """Update company knowledge from new report."""
        try:
            # If new_knowledge is None, fetch from MongoDB
            if new_knowledge is None:
                new_knowledge = await self._fetch_latest_report(company_code)
                if new_knowledge is None:
                    logger.error(f"No knowledge update available for {company_code}")
                    return

            # Read current knowledge
            current_knowledge = await self._read_knowledge(company_code)

            # Get update prompt
            prompt = get_knowledge_update_prompt(
                current_knowledge=current_knowledge,
                new_content=new_knowledge,
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

        except Exception as e:
            logger.error(f"Error updating knowledge for {company_code}: {str(e)}")

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
                logger.info(
                    f"No existing knowledge found in MongoDB for company {company_code}"
                )
                return ""

            # If multiple documents exist (shouldn't happen due to unique key), get the latest one
            if isinstance(result, list):
                # Sort by last_updated
                sorted_results = sorted(
                    result, key=lambda x: x["last_updated"], reverse=True
                )
                return sorted_results[0]["content"] if sorted_results else ""

            return result["content"]

        except Exception as e:
            logger.error(
                f"Error reading knowledge from MongoDB for {company_code}: {str(e)}"
            )
            return ""

    async def _save_knowledge(self, company_code: str, content: str):
        """Save updated knowledge to MongoDB."""
        try:
            # Prepare document for MongoDB
            document = {
                "company_code": company_code,
                "content": content,
                "last_updated": datetime.now(),
                "company_name": stock_id_to_name(company_code),
            }

            # Save to MongoDB
            success = db_manager.insert_data(
                db_type="mongo",
                data=document,
                collection="company_knowledge",
                key="company_code",
            )

            if not success:
                logger.error(
                    f"Failed to save knowledge to MongoDB for company {company_code}"
                )

        except Exception as e:
            logger.error(f"Error saving knowledge for {company_code}: {str(e)}")
            raise
