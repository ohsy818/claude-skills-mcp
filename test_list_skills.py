#!/usr/bin/env python3
"""Test script to call list_skills via MCP Streamable HTTP client."""

import asyncio
from mcp.client.streamable_http import streamablehttp_client


async def main():
    """Main test function."""
    from mcp import ClientSession
    backend_url = "http://localhost:8765/mcp"
    
    print(f"Connecting to backend at {backend_url}...")
    
    async with streamablehttp_client(backend_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            print("Connected! Calling list_skills...")
            
            # Initialize the connection
            await session.initialize()
            
            # Call list_skills tool
            result = await session.call_tool("list_skills", arguments={})
            
            print(f"\nResult type: {type(result)}")
            print(f"Result: {result}")
            
            if hasattr(result, 'content'):
                for item in result.content:
                    print(f"\nContent type: {item.type}")
                    if hasattr(item, 'text'):
                        print(f"Text (first 500 chars):\n{item.text[:500]}")
            

if __name__ == "__main__":
    asyncio.run(main())

