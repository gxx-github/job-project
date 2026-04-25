"""
Memory Manager for Resume Optimization System.
Handles storage, retrieval, and caching of optimized resume sections.
"""
import os
import json
import hashlib
from typing import Dict, Optional, Any
from src.conf import MEMORY_DIR, ENABLE_MEMORY, CLEAR_MEMORY_ON_START
from rich.console import Console

console = Console()

class MemoryManager:
    def __init__(self, memory_dir: str = MEMORY_DIR):
        self.memory_dir = memory_dir
        self.enabled = ENABLE_MEMORY
        self._ensure_memory_dir()
        
        if self.enabled and CLEAR_MEMORY_ON_START:
            self.clear_memory()

    def _ensure_memory_dir(self):
        """Ensure the memory directory exists."""
        if self.enabled and not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)

    def _get_hash(self, content: str) -> str:
        """Generate SHA-256 hash for content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _get_file_path(self, section_key: str, content_hash: str) -> str:
        """Get the file path for a specific memory entry."""
        return os.path.join(self.memory_dir, f"{section_key}_{content_hash}.json")

    def get_optimized_content(self, section_key: str, original_content: str, context: Dict[str, Any] = None) -> Optional[str]:
        """
        Retrieve optimized content from memory if it exists.
        
        Args:
            section_key: The section identifier (e.g., 'skills', 'work_experience').
            original_content: The original content before optimization.
            context: Additional context dict (e.g., job_name) to include in hash calculation for uniqueness.
        
        Returns:
            Optimized content string if found, else None.
        """
        if not self.enabled:
            return None

        # Create a unique signature for the request: section + original_content + context
        signature = f"{original_content}"
        if context:
            # Sort keys to ensure consistent hash
            context_str = json.dumps(context, sort_keys=True)
            signature += f"|{context_str}"
            
        content_hash = self._get_hash(signature)
        file_path = self._get_file_path(section_key, content_hash)

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    console.print(f"[dim]Memory Hit for [{section_key}][/dim]")
                    return data.get("optimized_content")
            except Exception as e:
                console.print(f"[red]Error reading memory for {section_key}: {e}[/red]")
                return None
        
        return None

    def save_optimized_content(self, section_key: str, original_content: str, optimized_content: str, context: Dict[str, Any] = None):
        """
        Save optimized content to memory.
        """
        if not self.enabled:
            return

        signature = f"{original_content}"
        if context:
            context_str = json.dumps(context, sort_keys=True)
            signature += f"|{context_str}"

        content_hash = self._get_hash(signature)
        file_path = self._get_file_path(section_key, content_hash)

        data = {
            "section_key": section_key,
            "original_content": original_content,
            "optimized_content": optimized_content,
            "context": context,
            "hash": content_hash
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            console.print(f"[dim]Memory Saved for [{section_key}][/dim]")
        except Exception as e:
            console.print(f"[red]Error saving memory for {section_key}: {e}[/red]")

    def clear_memory(self, section_key: str = None):
        """
        Clear memory files.
        Args:
            section_key: If provided, only clear memory for this specific section.
                         Otherwise, clear all memory.
        """
        if not self.enabled:
            return
            
        msg = f"Clearing Memory Store for [{section_key}]..." if section_key else "Clearing ALL Memory Store..."
        console.print(f"[yellow]{msg}[/yellow]")
        
        if os.path.exists(self.memory_dir):
            for filename in os.listdir(self.memory_dir):
                # Filter by section_key if provided
                if section_key and not filename.startswith(f"{section_key}_"):
                    continue
                    
                file_path = os.path.join(self.memory_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    console.print(f"[red]Failed to delete {file_path}. Reason: {e}[/red]")

    def update_memory(self, section_key: str, original_content: str, new_optimized_content: str, context: Dict[str, Any] = None):
        """
        Manually update (overwrite) a memory entry with new optimized content.
        This is useful when user manually corrects a section.
        """
        if not self.enabled:
            console.print("[yellow]Memory is disabled. Cannot update.[/yellow]")
            return

        # Same logic as save, effectively overwrites
        self.save_optimized_content(section_key, original_content, new_optimized_content, context)
        console.print(f"[green]Memory Updated for [{section_key}][/green]")

# Singleton instance
memory_manager = MemoryManager()
