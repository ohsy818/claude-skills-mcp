#!/usr/bin/env python3
"""Download pptx skill files from GitHub to local directory."""

import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
import json
from pathlib import Path


async def download_pptx_skill():
    """Download pptx skill documents."""
    backend_url = "http://localhost:8765/mcp"
    
    async with streamablehttp_client(backend_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Get pptx skill documents
            result = await session.call_tool(
                "read_skill_document",
                arguments={
                    "skill_name": "pptx",
                    "document_path": "*"  # Get all documents
                }
            )
            
            # Save to local directory
            output_dir = Path("/Users/uengine/claude-skills-mcp/pptx_skill_files")
            output_dir.mkdir(exist_ok=True)
            
            print(f"Downloading pptx skill files to: {output_dir}\n")
            
            text_content = result.content[0].text
            
            # Save full content
            with open(output_dir / "full_content.txt", "w") as f:
                f.write(text_content)
            
            print(f"✅ Downloaded all pptx skill content")
            print(f"📄 Saved to: {output_dir}/full_content.txt")
            print(f"\nContent preview (first 500 chars):")
            print(text_content[:500])
            

if __name__ == "__main__":
    asyncio.run(download_pptx_skill())


