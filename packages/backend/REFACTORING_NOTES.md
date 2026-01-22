# 스킬 엔진 리팩터링 노트

## 변경 개요

멀티테넌트 SaaS 환경에서 스킬 검색 엔진을 scope 기반 필터링으로 리팩터링했습니다.

## 핵심 변경 사항

### 1. Skill 모델에 scope 필드 추가

- `scope: Literal["global", "tenant"]` 필드 추가
- `global`: 기본 스킬 (모든 에이전트가 항상 조회 가능)
- `tenant`: 업로드 스킬 (tenant_id와 allowed_skill_names로 필터링)

### 2. 검색 API 시그니처 변경

**변경 전:**
```python
search(query: str, top_k: int, agent_id: str | None, tenant_id: str | None)
```

**변경 후:**
```python
search(query: str, top_k: int, tenant_id: str | None, allowed_skill_names: list[str] | None)
```

### 3. 필터링 규칙

검색 결과는 다음 규칙으로 필터링됩니다:

1. **Global 스킬** (`scope == "global"`):
   - 항상 포함됨
   - 어떤 에이전트든 조회 가능

2. **Tenant 스킬** (`scope == "tenant"`):
   - 다음 조건을 **모두** 만족해야 포함:
     - `skill.tenant_id == tenant_id` (동일한 테넌트)
     - `skill.name in allowed_skill_names` (명시적으로 허용된 스킬)
   - **중요**: `allowed_skill_names`가 비어있거나 `None`이면 Tenant 스킬은 절대 조회되지 않음
   - 업로드된 스킬은 기본 스킬처럼 자동으로 모든 테넌트/에이전트에게 조회되지 않음

### 4. 책임 분리

- ❌ 스킬 엔진은 DB(users 테이블)를 직접 조회하지 않음
- ❌ 스킬 엔진은 SQL/Supabase SDK를 호출하지 않음
- ✅ 에이전트 권한 판단 → API 서버 책임
- ✅ 스킬 가시성 판단 → 스킬 엔진의 "순수 함수" 책임

## 변경 전/후 검색 흐름

### 변경 전
```
1. API 서버가 agent_id, tenant_id를 전달
2. 스킬 엔진이 agent_id와 tenant_id로 필터링
3. Public 스킬(agent_id=None, tenant_id=None)은 항상 포함
```

### 변경 후
```
1. API 서버가 users.skills 컬럼을 조회하여 allowed_skill_names 생성
2. API 서버가 tenant_id와 allowed_skill_names를 스킬 엔진에 전달
3. 스킬 엔진이 scope 기반으로 필터링:
   - Global 스킬: 항상 포함
   - Tenant 스킬: tenant_id 일치 + allowed_skill_names에 포함된 경우만
```

## API 서버 통합 가이드

API 서버에서 스킬 검색을 호출할 때:

```python
# 1. users 테이블에서 에이전트 정보 조회
agent = db.query("SELECT tenant_id, skills FROM users WHERE id = ?", [agent_id])
tenant_id = agent.tenant_id
allowed_skill_names = agent.skills.split(",") if agent.skills else []

# 2. 스킬 엔진에 검색 요청
results = skill_engine.search(
    query="analyze data",
    top_k=3,
    tenant_id=tenant_id,
    allowed_skill_names=allowed_skill_names
)
```

## 호환성

- 기존 global 스킬 검색 기능은 그대로 동작합니다
- 업로드 스킬은 이제 scope="tenant"로 자동 설정됩니다
- agent_id 파라미터는 더 이상 검색에 사용되지 않지만, 하위 호환성을 위해 일부 엔드포인트에서 유지됩니다

## 검증 체크리스트

- [x] 스킬 엔진이 users 테이블을 전혀 모르고 있는가?
- [x] 에이전트가 DB에 명시하지 않은 업로드 스킬은 절대 검색되지 않는가?
- [x] 기본 스킬은 어떤 에이전트든 항상 조회 가능한가?
- [x] 이 구조를 role/policy 기반 권한 모델로 확장할 수 있는가?

