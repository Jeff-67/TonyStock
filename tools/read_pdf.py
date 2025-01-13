from markitdown import MarkItDown
from openai import OpenAI
import os
import argparse

def convert_pdf_to_md(pdf_path, model="gpt-4o"):
    """Convert PDF to markdown using MarkItDown.
    
    Args:
        pdf_path (str): Path to the PDF file
        model (str): OpenAI model to use (default: gpt-4o)
    
    Returns:
        str: Path to the output markdown file
    """
    client = OpenAI()
    md = MarkItDown(llm_client=client, llm_model=model)
    
    # Get the directory and filename
    dir_path = os.path.dirname(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Convert PDF
    result = md.convert(pdf_path)
    
    # Create output directory if it doesn't exist
    os.makedirs(dir_path, exist_ok=True)
    
    # Save to markdown file in the same directory with .md extension
    output_path = os.path.join(dir_path, f"{base_name}.md")
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(result.text_content)
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Convert PDF to markdown using MarkItDown')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--model', default='gpt-4o', help='OpenAI model to use (default: gpt-4o)')
    
    args = parser.parse_args()
    
    try:
        output_file = convert_pdf_to_md(
            args.pdf_path,
            model=args.model
        )
        print(f"Conversion complete. Output saved to: {output_file}")
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
