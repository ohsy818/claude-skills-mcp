#!/usr/bin/env python3
"""
LangChain 기반 MCP 클라이언트 예제 - LangChain 체인 구조에서 MCP 서버의 도구를 사용하는 방법

필수 패키지 설치:
    pip install langchain-mcp-adapters langchain langchain-openai

사용법:
    python mcp_client_example.py
"""

from langchain_mcp_adapters.client import MultiServerMCPClient, load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub


def example_load_mcp_tools():
    """MCP 도구를 LangChain 도구로 로드하는 예제"""
    # MCP 서버 URL (도커 컴포즈로 띄운 경우)
    # 로컬: http://localhost:8765/mcp
    # 도커 네트워크 내: http://backend:8765/mcp
    # 원격: http://your-server:8765/mcp
    mcp_server_url = "http://localhost:8765/mcp"
    
    print(f"MCP 서버 연결 중: {mcp_server_url}")
    
    # MCP 클라이언트 생성
    mcp_client = MultiServerMCPClient(
        servers={
            "claude-skills-backend": mcp_server_url,
        }
    )
    
    # MCP 도구를 LangChain 도구로 로드
    mcp_tools = load_mcp_tools(mcp_client)
    
    print(f"\n로드된 도구 수: {len(mcp_tools)}")
    for tool in mcp_tools:
        print(f"  - {tool.name}: {tool.description[:100]}...")
    
    return mcp_tools, mcp_client


def example_simple_agent():
    """간단한 LangChain 에이전트 예제"""
    print("\n" + "=" * 60)
    print("예제 1: 간단한 LangChain 에이전트")
    print("=" * 60)
    
    # MCP 도구 로드
    mcp_tools, mcp_client = example_load_mcp_tools()
    
    # LLM 설정 (사용하는 LLM으로 변경)
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # ReAct 프롬프트 로드
    prompt = hub.pull("hwchase17/react")
    
    # 에이전트 생성
    agent = create_react_agent(llm=llm, tools=mcp_tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=mcp_tools, verbose=True)
    
    # 에이전트 실행
    result = agent_executor.invoke({
        "input": "머신러닝 모델 학습을 도와줄 스킬을 찾아주세요."
    })
    
    print("\n=== 결과 ===")
    print(result["output"])
    
    # 리소스 정리
    mcp_client.close()
    
    return result


def example_integrate_with_existing_tools():
    """기존 LangChain 도구와 MCP 도구 통합 예제"""
    print("\n" + "=" * 60)
    print("예제 2: 기존 도구와 통합")
    print("=" * 60)
    
    # MCP 도구 로드
    mcp_tools, mcp_client = example_load_mcp_tools()
    
    # 기존 LangChain 도구가 있다면 여기에 추가
    # 예: from langchain_community.tools import DuckDuckGoSearchRun
    # existing_tools = [DuckDuckGoSearchRun()]
    existing_tools = []
    
    # 모든 도구 통합
    all_tools = existing_tools + mcp_tools
    
    print(f"\n통합된 도구 수: {len(all_tools)}")
    print(f"  - 기존 도구: {len(existing_tools)}")
    print(f"  - MCP 도구: {len(mcp_tools)}")
    
    # LLM 설정
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # 에이전트 생성
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm=llm, tools=all_tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=all_tools, verbose=True)
    
    # 에이전트 실행
    result = agent_executor.invoke({
        "input": "데이터 분석을 위한 Python 스크립트 작성 스킬을 찾고, 관련 문서를 읽어주세요."
    })
    
    print("\n=== 결과 ===")
    print(result["output"])
    
    # 리소스 정리
    mcp_client.close()
    
    return result


def example_direct_tool_call():
    """MCP 도구를 직접 호출하는 예제 (에이전트 없이)"""
    print("\n" + "=" * 60)
    print("예제 3: 도구 직접 호출")
    print("=" * 60)
    
    # MCP 도구 로드
    mcp_tools, mcp_client = example_load_mcp_tools()
    
    # find_helpful_skills 도구 찾기
    find_skills_tool = None
    for tool in mcp_tools:
        if tool.name == "find_helpful_skills":
            find_skills_tool = tool
            break
    
    if find_skills_tool:
        print("\n도구 직접 호출: find_helpful_skills")
        result = find_skills_tool.invoke({
            "task_description": "데이터 시각화를 위한 Python 스크립트 작성",
            "top_k": 2,
            "list_documents": True,
        })
        
        print("\n=== 결과 ===")
        print(result)
    else:
        print("find_helpful_skills 도구를 찾을 수 없습니다.")
    
    # 리소스 정리
    mcp_client.close()
    
    return result if find_skills_tool else None


class LangChainMCPClient:
    """LangChain 체인에서 MCP 도구를 사용하기 위한 클라이언트 클래스"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8765/mcp"):
        """
        Parameters
        ----------
        mcp_server_url : str
            MCP 서버 URL
        """
        self.mcp_server_url = mcp_server_url
        self.mcp_client = None
        self.mcp_tools = None
    
    def get_tools(self):
        """MCP 도구를 LangChain 도구로 로드"""
        if self.mcp_tools is None:
            self.mcp_client = MultiServerMCPClient(
                servers={
                    "claude-skills-backend": self.mcp_server_url,
                }
            )
            self.mcp_tools = load_mcp_tools(self.mcp_client)
        return self.mcp_tools
    
    def create_agent(self, llm, existing_tools=None, verbose=True):
        """LangChain 에이전트 생성"""
        mcp_tools = self.get_tools()
        
        # 기존 도구와 통합
        if existing_tools:
            all_tools = existing_tools + mcp_tools
        else:
            all_tools = mcp_tools
        
        # ReAct 프롬프트 로드
        prompt = hub.pull("hwchase17/react")
        
        # 에이전트 생성
        agent = create_react_agent(llm=llm, tools=all_tools, prompt=prompt)
        agent_executor = AgentExecutor(agent=agent, tools=all_tools, verbose=verbose)
        
        return agent_executor
    
    def close(self):
        """리소스 정리"""
        if self.mcp_client:
            self.mcp_client.close()
            self.mcp_client = None
            self.mcp_tools = None


def example_using_client_class():
    """LangChainMCPClient 클래스 사용 예제"""
    print("\n" + "=" * 60)
    print("예제 4: 클라이언트 클래스 사용")
    print("=" * 60)
    
    # 클라이언트 생성
    client = LangChainMCPClient("http://localhost:8765/mcp")
    
    try:
        # LLM 설정
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        # 에이전트 생성
        agent_executor = client.create_agent(llm, verbose=True)
        
        # 에이전트 실행
        result = agent_executor.invoke({
            "input": "사용 가능한 모든 스킬 목록을 보여주세요."
        })
        
        print("\n=== 결과 ===")
        print(result["output"])
        
    finally:
        # 리소스 정리
        client.close()
    
    return result


def main():
    """메인 함수 - 원하는 예제를 선택하여 실행"""
    print("=" * 60)
    print("LangChain 기반 MCP 클라이언트 예제")
    print("=" * 60)
    
    # 예제 선택 (원하는 예제의 주석을 해제하세요)
    
    # 1. 간단한 에이전트 예제
    example_simple_agent()
    
    # 2. 기존 도구와 통합 예제
    # example_integrate_with_existing_tools()
    
    # 3. 도구 직접 호출 예제
    # example_direct_tool_call()
    
    # 4. 클라이언트 클래스 사용 예제 (권장)
    # example_using_client_class()


if __name__ == "__main__":
    main()

