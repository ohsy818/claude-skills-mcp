# MCP 클라이언트 사용 가이드 (LangChain 기반)

이 문서는 LangChain 체인 구조를 사용하는 파이썬 코드에서 도커 컴포즈로 띄운 MCP 서버의 도구를 호출하는 방법을 설명합니다.

## 필수 패키지 설치

```bash
pip install langchain-mcp-adapters langchain langchain-openai
```

또는 `pyproject.toml`에 추가:

```toml
dependencies = [
    "langchain-mcp-adapters>=0.1.0",
    "langchain>=0.1.0",
    "langchain-openai>=0.1.0",
]
```

## 기본 사용법

### 1. MCP 도구를 LangChain 도구로 로드

```python
from langchain_mcp_adapters.client import MultiServerMCPClient, load_mcp_tools

# MCP 서버 URL (도커 컴포즈로 띄운 경우)
mcp_server_url = "http://localhost:8765/mcp"

# MCP 클라이언트 생성
mcp_client = MultiServerMCPClient(
    servers={
        "claude-skills-backend": mcp_server_url,
    }
)

# MCP 도구를 LangChain 도구로 로드
mcp_tools = load_mcp_tools(mcp_client)

# 이제 mcp_tools를 LangChain 에이전트나 체인에서 사용할 수 있습니다
```

### 2. LangChain 에이전트에 통합

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain_mcp_adapters.client import MultiServerMCPClient, load_mcp_tools

# MCP 도구 로드
mcp_client = MultiServerMCPClient(
    servers={"claude-skills-backend": "http://localhost:8765/mcp"}
)
mcp_tools = load_mcp_tools(mcp_client)

# LLM 설정
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

print(result["output"])

# 리소스 정리
mcp_client.close()
```

### 3. 기존 LangChain 도구와 통합

```python
from langchain_mcp_adapters.client import MultiServerMCPClient, load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub

# MCP 도구 로드
mcp_client = MultiServerMCPClient(
    servers={"claude-skills-backend": "http://localhost:8765/mcp"}
)
mcp_tools = load_mcp_tools(mcp_client)

# 기존 LangChain 도구 (예시)
# from langchain_community.tools import DuckDuckGoSearchRun
# existing_tools = [DuckDuckGoSearchRun()]
existing_tools = []

# 모든 도구 통합
all_tools = existing_tools + mcp_tools

# LLM 및 에이전트 설정
llm = ChatOpenAI(model="gpt-4o", temperature=0)
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm=llm, tools=all_tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=all_tools, verbose=True)

# 에이전트 실행
result = agent_executor.invoke({
    "input": "데이터 분석 스킬을 찾고 관련 문서를 읽어주세요."
})

# 리소스 정리
mcp_client.close()
```

## 사용 가능한 도구

MCP 서버에서 제공하는 도구들은 자동으로 LangChain 도구로 변환됩니다:

### 1. find_helpful_skills - 스킬 검색

가장 유용한 스킬을 검색합니다.

**파라미터:**
- `task_description` (필수): 작업 설명
- `tenant_id` (선택): 테넌트 ID
- `top_k` (선택, 기본값: 3): 반환할 상위 결과 수
- `list_documents` (선택, 기본값: True): 문서 목록 포함 여부
- `allowed_skill_names` (선택): 허용된 스킬 이름 목록

**LangChain 에이전트에서 사용:**
에이전트가 자연어로 요청하면 자동으로 호출됩니다:
```python
result = agent_executor.invoke({
    "input": "데이터 시각화를 위한 스킬을 찾아주세요."
})
```

**직접 호출:**
```python
# 도구 찾기
find_skills_tool = None
for tool in mcp_tools:
    if tool.name == "find_helpful_skills":
        find_skills_tool = tool
        break

# 도구 호출
result = find_skills_tool.invoke({
    "task_description": "데이터 시각화",
    "top_k": 5,
    "list_documents": True
})
```

### 2. read_skill_document - 스킬 문서 읽기

특정 스킬의 문서를 읽습니다.

**파라미터:**
- `skill_name` (필수): 스킬 이름
- `document_path` (선택): 문서 경로 (예: "scripts/analyze.py")
- `include_base64` (선택, 기본값: False): 바이너리 파일을 base64로 인코딩할지 여부

**LangChain 에이전트에서 사용:**
```python
result = agent_executor.invoke({
    "input": "Python Data Analysis 스킬의 analyze.py 파일을 읽어주세요."
})
```

### 3. list_skills - 스킬 목록 조회

모든 사용 가능한 스킬 목록을 조회합니다.

**LangChain 에이전트에서 사용:**
```python
result = agent_executor.invoke({
    "input": "사용 가능한 모든 스킬 목록을 보여주세요."
})
```

## 도커 컴포즈 환경에서 사용

도커 컴포즈로 MCP 서버를 띄운 경우:

1. **같은 네트워크 내에서**: 서비스 이름을 사용
   ```python
   backend_url = "http://backend:8765/mcp"  # docker-compose.yml의 서비스 이름
   ```

2. **호스트에서 접근**: localhost 사용
   ```python
   backend_url = "http://localhost:8765/mcp"  # 포트가 매핑된 경우
   ```

3. **원격 서버에서 접근**: 서버 IP 또는 도메인 사용
   ```python
   backend_url = "http://your-server.com:8765/mcp"
   ```

## 에러 처리

```python
from langchain_mcp_adapters.client import MultiServerMCPClient, load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub

try:
    # MCP 클라이언트 생성
    mcp_client = MultiServerMCPClient(
        servers={"claude-skills-backend": "http://localhost:8765/mcp"}
    )
    
    # MCP 도구 로드
    mcp_tools = load_mcp_tools(mcp_client)
    
    # LLM 및 에이전트 설정
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm=llm, tools=mcp_tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=mcp_tools, verbose=True)
    
    # 에이전트 실행
    result = agent_executor.invoke({
        "input": "데이터 분석 스킬을 찾아주세요."
    })
    
    print("성공:", result["output"])
    
except ConnectionError as e:
    print(f"연결 오류: {e}")
    print("MCP 서버가 실행 중인지 확인하세요.")
except Exception as e:
    print(f"오류 발생: {e}")
finally:
    # 리소스 정리
    if 'mcp_client' in locals():
        mcp_client.close()
```

## 완전한 예제 코드

`mcp_client_example.py` 파일을 참고하세요. 이 파일에는:
- MCP 도구를 LangChain 도구로 로드하는 예제
- LangChain 에이전트 생성 및 실행 예제
- 기존 도구와 통합하는 예제
- 재사용 가능한 `LangChainMCPClient` 클래스
- 에러 처리 예제

가 포함되어 있습니다.

## 주의사항

1. **리소스 정리**: `MultiServerMCPClient` 사용 후 반드시 `close()`를 호출하여 리소스를 정리하세요.
2. **도구 자동 변환**: `load_mcp_tools()`를 통해 MCP 도구가 자동으로 LangChain 도구로 변환됩니다.
3. **에이전트 사용**: LangChain 에이전트는 자연어 입력을 받아 자동으로 적절한 도구를 선택하고 호출합니다.
4. **도구 통합**: 기존 LangChain 도구와 MCP 도구를 함께 사용할 수 있습니다.
5. **연결 유지**: 여러 도구를 호출할 때는 같은 `mcp_client` 인스턴스를 재사용하는 것이 효율적입니다.

## 추가 리소스

- MCP 공식 문서: https://modelcontextprotocol.io
- 백엔드 README: `README.md`
- 예제 코드: `mcp_client_example.py`

