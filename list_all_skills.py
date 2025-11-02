#!/usr/bin/env python3
"""Extract and display all skills in a clean format."""

import asyncio
import re
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession


async def main():
    """Main function to list all skills."""
    backend_url = "http://localhost:8765/mcp"
    
    print("Connecting to backend...\n")
    
    async with streamablehttp_client(backend_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Call list_skills
            result = await session.call_tool("list_skills", arguments={})
            
            # Extract text content
            text = result.content[0].text
            
            # Parse skills
            skills = []
            lines = text.split('\n')
            current_skill = {}
            
            for line in lines:
                # Match skill number and name
                match = re.match(r'^(\d+)\.\s+(.+)$', line)
                if match:
                    if current_skill:
                        skills.append(current_skill)
                    current_skill = {
                        'number': match.group(1),
                        'name': match.group(2)
                    }
                elif line.strip().startswith('Description:'):
                    desc = line.split('Description:', 1)[1].strip()
                    current_skill['description'] = desc
                elif line.strip().startswith('Source:'):
                    source = line.split('Source:', 1)[1].strip()
                    current_skill['source'] = source
                elif line.strip().startswith('Documents:'):
                    docs = line.split('Documents:', 1)[1].strip()
                    current_skill['documents'] = docs
            
            # Add last skill
            if current_skill:
                skills.append(current_skill)
            
            # Print summary
            print(f"총 {len(skills)}개의 스킬이 로드되었습니다.\n")
            print("=" * 80)
            
            # Print all skills
            for skill in skills:
                print(f"\n{skill['number']}. {skill['name']}")
                if 'source' in skill:
                    print(f"   출처: {skill['source']}")
                if 'documents' in skill:
                    print(f"   문서: {skill['documents']}")
                if 'description' in skill:
                    desc = skill['description']
                    if len(desc) > 150:
                        desc = desc[:150] + "..."
                    print(f"   설명: {desc}")
            
            print("\n" + "=" * 80)
            
            # Print by category
            anthropic_skills = [s for s in skills if 'anthropics/skills' in s.get('source', '')]
            scientific_skills = [s for s in skills if 'K-Dense-AI' in s.get('source', '')]
            
            print(f"\n📊 카테고리별 통계:")
            print(f"   - Anthropic 공식 스킬: {len(anthropic_skills)}개")
            print(f"   - K-Dense AI 과학 스킬: {len(scientific_skills)}개")
            print(f"   - 총합: {len(skills)}개")
            

if __name__ == "__main__":
    asyncio.run(main())


