"""Script to read investment reports and save them to MongoDB."""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel

from database.utils import db_manager
from prompts.tools.investment_report import (
    get_contents_extraction_prompt,
    get_metadata_extraction_prompt,
    get_report_type_prompt,
)
from tools.investment_report_data.investment_report_monitor import DOWNLOAD_DIR
from tools.llm_api import aquery_llm
from tools.read_pdf import convert_pdf_to_md

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ReportType(BaseModel):
    """Type definition for report type."""

    level_1: str  # 個股分析/產業分析
    level_2: str  # 台股/美股/陸股 or 台灣/北美/日本
    level_3: str  # 科技股/金融股/etc or 半導體/電子/金融/etc
    level_4: str  # 股票代碼 or 特定產業


class ReportMetadata(BaseModel):
    """Type definition for report metadata."""

    publish_date: str
    source: str
    language: str


class ReportContents(BaseModel):
    """Type definition for report contents."""

    title: str
    file_path: str
    summary: str
    key_points: List[str]
    full_text: str


class ReportFilters(BaseModel):
    """Type definition for report filters."""

    report_type: ReportType
    metadata: ReportMetadata


class ReportDocument(BaseModel):
    """Type definition for complete report document."""

    filters: ReportFilters
    contents: ReportContents
    file_id: str
    source_path: str
    processed_at: str


class InvestmentReportReader:
    """Reads investment reports and saves them to MongoDB."""

    def __init__(self):
        """Initialize the report reader."""
        self.db_manager = db_manager

    async def _generate_file_id(
        self, original_file_id: str, metadata: ReportMetadata, report_type: ReportType
    ) -> str:
        """
        Generate a meaningful file ID combining multiple pieces of information.

        Format: {date}_{source}_{report_type}_{original_id}
        Example: 20240207_yuanta_stock_7737_89345

        Args:
            original_file_id (str): Original file ID from the PDF
            metadata (ReportMetadata): Metadata information
            report_type (ReportType): Report type information

        Returns:
            str: Generated file ID
        """
        # Clean date format (assuming date_dir is in YYYY-MM-DD format)
        clean_date = metadata.publish_date.replace("-", "")

        # Get source identifier (lowercase, no spaces)
        source_id = metadata.source  # Can be made dynamic based on source

        # Get report type identifier
        if report_type.level_1 == "個股分析":
            type_id = (
                f"stock_{report_type.level_4.split('.')[0]}"  # Extract stock number
            )
        else:
            type_id = "industry"

        # Combine all parts
        return f"{clean_date}_{source_id}_{type_id}_{original_file_id}"

    async def _extract_report_type(self, content: str) -> ReportType:
        """
        Extract report type information from content using LLM.

        Args:
            content (str): The markdown content of the report

        Returns:
            ReportType: Extracted report type information including level 1-4 classifications
        """
        # Get the formatted prompt
        prompt = get_report_type_prompt(content)

        # Query LLM with the prompt
        messages = [{"role": "user", "content": prompt}]
        response, _ = await aquery_llm(
            messages=messages,
            model="gpt-4o",
            provider="openai",
            response_format=ReportType,
        )

        # Extract and return the report type
        json_response = json.loads(response.choices[0].message.content)
        return ReportType(**json_response)

    async def _extract_metadata(self, content: str) -> ReportMetadata:
        """
        Extract metadata from content using LLM.

        Args:
            content (str): The markdown content of the report

        Returns:
            ReportMetadata: Extracted metadata including publish date, source, and language
        """
        # Get the formatted prompt
        prompt = get_metadata_extraction_prompt(content)

        # Query LLM with the prompt
        messages = [{"role": "user", "content": prompt}]
        response, _ = await aquery_llm(
            messages=messages,
            model="gpt-4o",
            provider="openai",
            response_format=ReportMetadata,
        )

        # Extract and return the metadata
        json_response = json.loads(response.choices[0].message.content)
        return ReportMetadata(**json_response)

    async def _extract_contents(self, content: str, file_path: str) -> ReportContents:
        """
        Extract report contents using LLM.

        Args:
            content (str): The markdown content of the report
            file_path (str): Path to the original PDF file

        Returns:
            ReportContents: Extracted contents including title, summary, and key points
        """
        # Get the formatted prompt
        prompt = get_contents_extraction_prompt(content)

        # Query LLM with the prompt
        messages = [{"role": "user", "content": prompt}]
        response, _ = await aquery_llm(
            messages=messages,
            model="gpt-4o",
            provider="openai",
            json_mode=True,
        )

        # Extract the content parts
        json_response = json.loads(response.choices[0].message.content)

        # Add file path and full text to the response
        json_response["file_path"] = file_path
        json_response["full_text"] = content

        # Convert to ReportContents model
        return ReportContents(**json_response)

    async def process_pdf(self, pdf_path: str) -> Optional[Dict]:
        """
        Process a single PDF file and convert it to markdown.

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            Optional[Dict]: Document to be stored in MongoDB, or None if processing fails
        """
        try:
            # Get file information
            original_file_id = os.path.splitext(os.path.basename(pdf_path))[0]

            # Convert PDF to markdown
            logger.info(f"Converting PDF to markdown: {pdf_path}")
            try:
                markdown_content = await convert_pdf_to_md(pdf_path)
            except Exception as e:
                logger.error(f"Error converting PDF to markdown: {e}")
                return None

            if not markdown_content:
                logger.error(f"Failed to convert PDF to markdown: {pdf_path}")
                return None

            # Extract structured information in parallel
            metadata, report_type, contents = await asyncio.gather(
                self._extract_metadata(markdown_content),
                self._extract_report_type(markdown_content),
                self._extract_contents(markdown_content, pdf_path),
            )

            # Generate meaningful file ID
            file_id = await self._generate_file_id(
                original_file_id, metadata, report_type
            )

            # Create document for MongoDB
            document = {
                "filters": {
                    "report_type": report_type.model_dump(),
                    "metadata": metadata.model_dump(),
                },
                "contents": contents.model_dump(),
                "file_id": file_id,
                "source_path": pdf_path,
                "processed_at": datetime.now().isoformat(),
            }

            return document

        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return None

    async def process_directory(
        self, date_dir: str, max_files: Optional[int] = None
    ) -> bool:
        """
        Process PDFs in a specific date directory.

        Args:
            date_dir (str): Date directory name (YYYY-MM-DD)
            max_files (int, optional): Maximum number of files to process. If None, process all files.

        Returns:
            bool: True if successful, False otherwise
        """
        dir_path = os.path.join(DOWNLOAD_DIR, date_dir)
        if not os.path.exists(dir_path):
            logger.error(f"Directory does not exist: {dir_path}")
            return False

        # Get all PDF files in directory
        pdf_files = [f for f in os.listdir(dir_path) if f.endswith(".pdf")]
        if not pdf_files:
            logger.info(f"No PDF files found in {dir_path}")
            return True

        # Limit number of files if max_files is specified
        if max_files is not None:
            pdf_files = pdf_files[:max_files]
            logger.info(
                f"Processing {len(pdf_files)} files (limited by max_files={max_files})"
            )

        # Process PDFs concurrently
        pdf_paths = [os.path.join(dir_path, pdf_file) for pdf_file in pdf_files]
        documents = await asyncio.gather(
            *[self.process_pdf(pdf_path) for pdf_path in pdf_paths]
        )

        # Filter out None values and save to MongoDB
        processed_documents = [doc for doc in documents if doc is not None]
        if processed_documents:
            return self.save_to_mongodb(processed_documents)
        return True

    async def process_all_directories(
        self, max_files_per_dir: Optional[int] = None
    ) -> bool:
        """
        Process all date directories in the download directory.

        Args:
            max_files_per_dir (int, optional): Maximum number of files to process per directory.
                                             If None, process all files.

        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(DOWNLOAD_DIR):
            logger.error(f"Download directory does not exist: {DOWNLOAD_DIR}")
            return False

        success = True
        for date_dir in os.listdir(DOWNLOAD_DIR):
            if os.path.isdir(os.path.join(DOWNLOAD_DIR, date_dir)):
                logger.info(f"Processing directory: {date_dir}")
                if not await self.process_directory(
                    date_dir, max_files=max_files_per_dir
                ):
                    success = False
                    logger.error(f"Failed to process directory: {date_dir}")

        return success

    def save_to_mongodb(self, documents: List[Dict]) -> bool:
        """
        Save processed documents to MongoDB.

        Args:
            documents (List[Dict]): List of documents to save

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.db_manager.insert_data(
                db_type="mongo",
                data=documents,
                collection="investment_reports",
                key="file_id",
            )
            if result:
                logger.info(f"Successfully saved {len(documents)} documents to MongoDB")
            else:
                logger.error("Failed to save documents to MongoDB")
            return result
        except Exception as e:
            logger.error(f"Error saving to MongoDB: {str(e)}")
            return False


def main():
    """Execute the investment report reader to process reports."""
    reader = InvestmentReportReader()
    # Process only 6 files per directory
    if asyncio.run(reader.process_all_directories(max_files_per_dir=6)):
        logger.info("Successfully processed all investment reports")
    else:
        logger.error("Errors occurred while processing investment reports")


if __name__ == "__main__":
    main()
