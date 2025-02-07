"""PDF to Markdown conversion module.

This module provides functionality to convert PDF documents to markdown format
using the MarkItDown library with OpenAI's language models. It handles file
path management, conversion process, and output file generation.
"""

import argparse
import os

from docling.datamodel.pipeline_options import TableFormerMode
from docling.document_converter import DocumentConverter, InputFormat, PdfFormatOption
from docling.pipeline.standard_pdf_pipeline import PdfPipelineOptions


def convert_pdf_to_md(pdf_path, output_path=None, model="gpt-4o"):
    """Convert PDF to markdown using MarkItDown.

    Args:
        pdf_path (str): Path to the PDF file
        model (str): OpenAI model to use (default: gpt-4o)

    Returns:
        str: Path to the output markdown file
    """
    # Configure pipeline options with the new recommended settings
    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_page_images = True  # Required for table images
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

    # Create format options with our configured pipeline options
    pdf_format_option = PdfFormatOption(pipeline_options=pipeline_options)
    format_options = {InputFormat.PDF: pdf_format_option}

    # Initialize converter with format options
    converter = DocumentConverter(format_options=format_options)
    result = converter.convert(pdf_path)

    # Get the directory and filename
    dir_path = os.path.dirname(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    # Convert PDF
    result_md = result.document.export_to_markdown()

    # Create output directory if it doesn't exist
    os.makedirs(dir_path, exist_ok=True)

    # Generate output path with numeric suffix if file exists
    if output_path is None:
        output_path = os.path.join(dir_path, f"{base_name}.md")
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(dir_path, f"{base_name}_{counter}.md")
            counter += 1

    # Save to markdown file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result_md)

    return output_path


def main():
    """Command-line interface for PDF to markdown conversion.

    Provides a command-line interface for converting PDF files to markdown format
    using MarkItDown. Supports custom model selection and handles errors gracefully.

    Command-line Arguments:
        pdf_path: Path to the PDF file to convert
        --model: OpenAI model to use (default: gpt-4o)

    Raises:
        SystemExit: If an error occurs during conversion
    """
    parser = argparse.ArgumentParser(
        description="Convert PDF to markdown using MarkItDown"
    )
    parser.add_argument("--pdf_path", help="Path to the PDF file")
    parser.add_argument(
        "--model", default="gpt-4o", help="OpenAI model to use (default: gpt-4o)"
    )

    args = parser.parse_args()

    try:
        output_file = convert_pdf_to_md(args.pdf_path, model=args.model)
        print(f"Conversion complete. Output saved to: {output_file}")
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
