#!/usr/bin/env python3
"""Find pptx skill and get its documents."""

import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession


async def main():
    """Find pptx skill."""
    backend_url = "http://localhost:8765/mcp"
    
    async with streamablehttp_client(backend_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Find pptx skill
            result = await session.call_tool(
                "find_helpful_skills",
                arguments={
                    "task_description": "create powerpoint presentation with slides",
                    "top_k": 2,
                    "list_documents": True
                }
            )
            
            print(result.content[0].text)
            

if __name__ == "__main__":
    asyncio.run(main())


