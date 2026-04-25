from langchain_core.tools import tool
from rich.console import Console
from src.tools.pdf_generator import convert_markdown_to_pdf

console = Console()

@tool
def generate_pdf_tool(markdown_content: str, output_path: str) -> str:
    """
    (Deprecated) Legacy tool wrapper. Redirects to new PDF generator.
    """
    console.print("[yellow]Warning: generate_pdf_tool is deprecated. Using new PDF generator.[/yellow]")
    if convert_markdown_to_pdf(markdown_content, output_path):
        return f"Successfully generated PDF at {output_path}"
    else:
        return "Failed to generate PDF"
