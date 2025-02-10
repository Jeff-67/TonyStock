"""Test suite for investment report functionality."""

import asyncio
import os

from tools.investment_report_data.investment_report_reader import InvestmentReportReader
from tools.read_pdf import convert_pdf_to_md


class TestInvestmentReport:
    """Test class for investment report functionality."""

    @classmethod
    async def setup_class(cls):
        """Set up test class."""
        cls.pdf_path = (
            "/Users/jeffyang/Desktop/TonyStock/downloads/reports/2025-02-07/87380.pdf"
        )
        cls.reader = InvestmentReportReader()

        # Convert PDF to markdown once for all tests
        print("Converting PDF to markdown...")
        cls.markdown_content = (
            await convert_pdf_to_md(cls.pdf_path)
            if not os.path.exists(
                "/Users/jeffyang/Desktop/TonyStock/markdown_content.md"
            )
            else open(
                "/Users/jeffyang/Desktop/TonyStock/markdown_content.md", "r"
            ).read()
        )

        # save the markdown content to a file for inspection
        if not os.path.exists("/Users/jeffyang/Desktop/TonyStock/markdown_content.md"):
            with open(
                "/Users/jeffyang/Desktop/TonyStock/markdown_content.md", "w"
            ) as f:
                f.write(cls.markdown_content)

    async def test_parallel_extraction(self):
        """Test parallel extraction of metadata, report type, and contents."""
        print("\nTesting parallel extraction...")

        # Run all extractions in parallel
        metadata, report_type, contents = await asyncio.gather(
            self.reader._extract_metadata(self.markdown_content),
            self.reader._extract_report_type(self.markdown_content),
            self.reader._extract_contents(self.markdown_content, self.pdf_path),
        )

        # Test metadata
        print("\nExtracted Metadata:")
        print(f"Type: {type(metadata)}")
        print(f"Publish Date: {metadata.publish_date}")
        print(f"Source: {metadata.source}")
        print(f"Language: {metadata.language}")

        # Basic metadata assertions
        assert metadata.publish_date, "Publish date should not be empty"
        assert metadata.source, "Source should not be empty"
        assert metadata.language, "Language should not be empty"

        # Test report type
        print("\nExtracted Report Type:")
        print(f"Type: {type(report_type)}")
        print(f"Level 1 (Report Type): {report_type.level_1}")
        print(f"Level 2 (Market): {report_type.level_2}")
        print(f"Level 3 (Industry): {report_type.level_3}")
        print(f"Level 4 (Identifier): {report_type.level_4}")

        # Basic report type assertions
        assert report_type.level_1 in [
            "個股分析",
            "產業分析",
        ], "Level 1 should be valid"
        assert report_type.level_2 in [
            "台股",
            "美股",
            "陸股",
            "其他",
        ], "Level 2 should be valid"
        assert report_type.level_3, "Level 3 should not be empty"
        assert report_type.level_4, "Level 4 should not be empty"

        # Test contents
        print("\nExtracted Contents:")
        print(f"Type: {type(contents)}")
        print(f"\nTitle: {contents.title}")
        print(f"\nSummary: {contents.summary}")
        print("\nKey Points:")
        for i, point in enumerate(contents.key_points, 1):
            print(f"{i}. {point}")
        print(f"\nFile Path: {contents.file_path}")
        print(f"Full Text Length: {len(contents.full_text)} characters")

        # Basic contents assertions
        assert contents.title, "Title should not be empty"
        assert contents.summary, "Summary should not be empty"
        assert len(contents.key_points) >= 3, "Should have at least 3 key points"
        assert contents.file_path == self.pdf_path, "File path should match"
        assert contents.full_text == self.markdown_content, "Full text should match"

    async def test_process_pdf(self):
        """Test the complete PDF processing pipeline."""
        print("\nTesting complete PDF processing...")
        document = await self.reader.process_pdf(self.pdf_path)

        # Basic document assertions
        assert document is not None, "Document should not be None"
        assert document["file_id"], "File ID should not be empty"
        assert document["filters"]["report_type"], "Report type should not be empty"
        assert document["filters"]["metadata"], "Metadata should not be empty"
        assert document["contents"], "Contents should not be empty"
        assert document["source_path"] == self.pdf_path, "Source path should match"
        assert document["processed_at"], "Processed timestamp should not be empty"


async def run_tests():
    """Run all tests asynchronously."""
    test = TestInvestmentReport()
    test.setup_class()
    await asyncio.gather(test.test_parallel_extraction(), test.test_process_pdf())


if __name__ == "__main__":
    asyncio.run(run_tests())
