"""
Interactive Memory Management Script
Allows user to:
1. View which sections hit memory
2. Clear memory for specific sections
3. Manually update/correct memory entries
"""
import sys
import os
import json
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.manager import memory_manager
from src.conf import MEMORY_DIR

console = Console()

def list_memories():
    """List all available memory entries."""
    if not os.path.exists(MEMORY_DIR):
        console.print("[yellow]No memory directory found.[/yellow]")
        return []

    files = [f for f in os.listdir(MEMORY_DIR) if f.endswith(".json")]
    memories = []
    
    table = Table(title="Available Memory Entries")
    table.add_column("Index", justify="right", style="cyan")
    table.add_column("Section", style="magenta")
    table.add_column("Hash", style="dim")
    table.add_column("File Path", style="dim")

    for idx, filename in enumerate(files):
        # Filename format: section_key_hash.json
        parts = filename.replace(".json", "").split("_")
        # Handle case where section_key might contain underscores
        content_hash = parts[-1]
        section_key = "_".join(parts[:-1])
        
        memories.append({
            "index": idx,
            "section": section_key,
            "hash": content_hash,
            "filename": filename
        })
        table.add_row(str(idx), section_key, content_hash[:8] + "...", filename)

    console.print(table)
    return memories

def interactive_mode():
    console.print("[bold blue]Resume Optimization - Memory Manager[/bold blue]")
    
    while True:
        console.print("\n[bold]Options:[/bold]")
        console.print("1. List Memories")
        console.print("2. Clear ALL Memory")
        console.print("3. Clear Specific Section Memory")
        console.print("4. Update/Edit Memory Entry")
        console.print("q. Quit")
        
        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "q"])
        
        if choice == "q":
            break
            
        if choice == "1":
            list_memories()
            
        elif choice == "2":
            if Confirm.ask("Are you sure you want to clear ALL memory?"):
                memory_manager.clear_memory()
                console.print("[green]All memory cleared.[/green]")
                
        elif choice == "3":
            section = Prompt.ask("Enter section name to clear (e.g., 'skills', 'title')")
            if Confirm.ask(f"Clear memory for section '{section}'?"):
                memory_manager.clear_memory(section_key=section)
                console.print(f"[green]Memory for '{section}' cleared.[/green]")
                
        elif choice == "4":
            memories = list_memories()
            if not memories:
                continue
                
            idx_str = Prompt.ask("Enter Index of memory to edit")
            try:
                idx = int(idx_str)
                if 0 <= idx < len(memories):
                    target = memories[idx]
                    file_path = os.path.join(MEMORY_DIR, target["filename"])
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    console.print(f"[cyan]Current Optimized Content for {target['section']}:[/cyan]")
                    console.print(data.get("optimized_content", "")[:200] + "...")
                    
                    new_content = Prompt.ask("Enter new content (or press Enter to keep current)")
                    if new_content.strip():
                        # Update the file
                        data["optimized_content"] = new_content
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        console.print("[green]Memory updated successfully.[/green]")
                    else:
                        console.print("[yellow]No changes made.[/yellow]")
                else:
                    console.print("[red]Invalid index.[/red]")
            except ValueError:
                console.print("[red]Invalid input.[/red]")

if __name__ == "__main__":
    interactive_mode()
