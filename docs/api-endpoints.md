# HTTP API 엔드포인트 문서

Claude Skills MCP Backend에서 제공하는 모든 HTTP API 엔드포인트 목록과 사용 예시입니다.

**기본 URL**: `http://localhost:8765` (기본 포트)

---

## 목차

1. [헬스 체크](#1-헬스-체크)
2. [스킬 업로드](#2-스킬-업로드)
3. [스킬 다운로드](#3-스킬-다운로드)
4. [업로드된 스킬 목록](#4-업로드된-스킬-목록)
5. [스킬 존재 확인](#5-스킬-존재-확인)
6. [스킬 파일 목록](#6-스킬-파일-목록)
7. [스킬 파일 조회](#7-스킬-파일-조회)
8. [스킬 파일 업데이트](#8-스킬-파일-업데이트)
9. [스킬 파일 삭제](#9-스킬-파일-삭제)
10. [스킬 삭제](#10-스킬-삭제)
11. [멀티테넌트 및 권한 관리](#11-멀티테넌트-및-권한-관리)

---

## 1. 헬스 체크

서버 상태와 로드된 스킬 정보를 확인합니다.

### 엔드포인트
```
GET /health
```

### 사용 예시

**cURL:**
```bash
curl http://localhost:8765/health
```

**Python:**
```python
import requests

response = requests.get("http://localhost:8765/health")
print(response.json())
```

### 응답 예시
```json
{
  "status": "ok",
  "version": "1.0.6",
  "skills_loaded": 78,
  "models_loaded": true,
  "loading_complete": true,
  "auto_update_enabled": true,
  "next_update_check": "2024-01-01T12:00:00",
  "last_update_check": "2024-01-01T11:00:00",
  "github_api_calls_this_hour": 5,
  "github_api_limit": 60,
  "github_authenticated": false
}
```

---

## 2. 스킬 업로드

ZIP 파일로 스킬을 업로드하고 서버에 추가/업데이트합니다.

### 엔드포인트
```
POST /skills/upload
```

### 요청 형식
- **Content-Type**: `multipart/form-data`
- **필드명**: `file` (ZIP 파일)
- **파일 형식**: ZIP 아카이브 (내부에 `SKILL.md` 포함)
- **선택 파라미터**:
  - `tenant_id` (문자열): 테넌트 ID. 제공 시 스킬이 `scope="tenant"`로 설정됩니다.
  - `agent_id` (문자열, 선택): 에이전트 ID (하위 호환성을 위해 유지, 검색에는 사용되지 않음)

### 스킬 Scope

업로드된 스킬은 두 가지 scope를 가집니다:

- **Global 스킬** (`scope="global"`): 
  - 기본 스킬 (GitHub에서 로드된 스킬)
  - 모든 에이전트가 항상 조회 가능
  - `tenant_id`가 없으면 자동으로 global로 설정

- **Tenant 스킬** (`scope="tenant"`):
  - 업로드된 스킬 (`tenant_id` 제공 시)
  - 동일한 `tenant_id`에 속해야 하며
  - 에이전트가 DB(`users.skills` 컬럼)에 명시적으로 보유한 스킬 이름만 조회 가능

### 사용 예시

**cURL:**
```bash
# 기본 업로드 (global 스킬)
curl -X POST http://localhost:8765/skills/upload \
  -F "file=@my-skill.zip"

# Tenant 스킬로 업로드
curl -X POST http://localhost:8765/skills/upload \
  -F "file=@my-skill.zip" \
  -F "tenant_id=tenant-123"
```

**Python:**
```python
import requests

# 기본 업로드 (global 스킬)
with open("my-skill.zip", "rb") as f:
    files = {"file": ("my-skill.zip", f, "application/zip")}
    response = requests.post(
        "http://localhost:8765/skills/upload",
        files=files
    )
    print(response.json())

# Tenant 스킬로 업로드
with open("my-skill.zip", "rb") as f:
    files = {"file": ("my-skill.zip", f, "application/zip")}
    data = {"tenant_id": "tenant-123"}
    response = requests.post(
        "http://localhost:8765/skills/upload",
        files=files,
        data=data
    )
    print(response.json())
```

**JavaScript (fetch):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8765/skills/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### 응답 예시
```json
{
  "status": "ok",
  "skills_added": ["My Custom Skill"],
  "total_skills": 79,
  "persistent_storage_path": "/path/to/skills",
  "message": "Skills saved to /path/to/skills and will be available after server restart"
}
```

**참고**: `tenant_id`를 제공한 경우, 업로드된 스킬은 `scope="tenant"`로 설정되며, 해당 테넌트의 에이전트만 `users.skills` 컬럼에 명시된 스킬 이름을 통해 접근할 수 있습니다.

### 에러 응답
- `400`: 잘못된 파일 형식 또는 빈 파일
- `409`: 스킬 로딩이 진행 중
- `500`: 로컬 스토리지 설정 오류

---

## 3. 스킬 다운로드

업로드된 스킬을 ZIP 파일로 다운로드합니다.

### 엔드포인트
```
GET /skills/download?name={skill_name}
```

### 파라미터
- `name` (필수): 다운로드할 스킬 이름

### 사용 예시

**cURL:**
```bash
curl "http://localhost:8765/skills/download?name=My%20Custom%20Skill" \
  -o my-skill.zip
```

**Python:**
```python
import requests

skill_name = "My Custom Skill"
response = requests.get(
    f"http://localhost:8765/skills/download",
    params={"name": skill_name}
)

if response.status_code == 200:
    with open("my-skill.zip", "wb") as f:
        f.write(response.content)
    print("Downloaded successfully")
else:
    print(f"Error: {response.json()}")
```

**JavaScript (fetch):**
```javascript
const skillName = encodeURIComponent("My Custom Skill");
fetch(`http://localhost:8765/skills/download?name=${skillName}`)
  .then(response => response.blob())
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'skill.zip';
    a.click();
  });
```

### 응답
- **성공 (200)**: ZIP 파일 (Content-Type: `application/zip`)
- **실패 (404)**: JSON 에러 메시지

### 에러 응답 예시
```json
{
  "detail": "Skill 'My Custom Skill' not found in local storage"
}
```

---

## 4. 업로드된 스킬 목록

로컬 스토리지에 업로드된 모든 스킬 목록을 조회합니다.

### 엔드포인트
```
GET /skills/list
```

### 사용 예시

**cURL:**
```bash
curl http://localhost:8765/skills/list
```

**Python:**
```python
import requests

response = requests.get("http://localhost:8765/skills/list")
data = response.json()
print(f"Found {data['count']} uploaded skills")
for skill in data['skills']:
    print(f"- {skill['name']}: {skill['file_count']} files")
```

### 응답 예시
```json
{
  "skills": [
    {
      "name": "My Custom Skill",
      "description": "A custom skill for data analysis",
      "directory": "my-custom-skill",
      "file_count": 5,
      "path": "/path/to/skills/my-custom-skill"
    },
    {
      "name": "Another Skill",
      "description": "Another custom skill",
      "directory": "another-skill",
      "file_count": 3,
      "path": "/path/to/skills/another-skill"
    }
  ],
  "count": 2,
  "storage_path": "/path/to/skills"
}
```

---

## 5. 스킬 존재 확인

스킬이 인덱스에 존재하는지 확인합니다.

### 엔드포인트
```
GET /skills/check?name={skill_name}
```

### 파라미터
- `name` (필수): 확인할 스킬 이름

### 사용 예시

**cURL:**
```bash
curl "http://localhost:8765/skills/check?name=My%20Custom%20Skill"
```

**Python:**
```python
import requests

skill_name = "My Custom Skill"
response = requests.get(
    "http://localhost:8765/skills/check",
    params={"name": skill_name}
)
data = response.json()

if data.get("exists"):
    print(f"Skill found: {data['name']}")
    print(f"Description: {data['description']}")
    print(f"Documents: {data['document_count']}")
else:
    print(f"Skill not found: {data['detail']}")
```

### 응답 예시 (존재함)
```json
{
  "name": "My Custom Skill",
  "description": "A custom skill for data analysis",
  "source": "/path/to/skills/my-custom-skill/SKILL.md",
  "document_count": 4,
  "exists": true
}
```

### 응답 예시 (존재하지 않음)
```json
{
  "name": "NonExistent Skill",
  "exists": false,
  "detail": "Skill 'NonExistent Skill' not found. Available skills: 78 total"
}
```

---

## 6. 스킬 파일 목록

특정 스킬의 모든 파일 목록을 조회합니다.

### 엔드포인트
```
GET /skills/{skill_name}/files
```

### 파라미터
- `skill_name` (경로): 스킬 이름

### 사용 예시

**cURL:**
```bash
curl "http://localhost:8765/skills/My%20Custom%20Skill/files"
```

**Python:**
```python
import requests
from urllib.parse import quote

skill_name = "My Custom Skill"
response = requests.get(
    f"http://localhost:8765/skills/{quote(skill_name)}/files"
)
data = response.json()

print(f"Files in '{data['skill_name']}':")
for file_info in data['files']:
    print(f"  - {file_info['path']} ({file_info['size']} bytes)")
```

**JavaScript (fetch):**
```javascript
const skillName = encodeURIComponent("My Custom Skill");
fetch(`http://localhost:8765/skills/${skillName}/files`)
  .then(response => response.json())
  .then(data => {
    console.log(`Files in ${data.skill_name}:`);
    data.files.forEach(file => {
      console.log(`  - ${file.path} (${file.size} bytes)`);
    });
  });
```

### 응답 예시
```json
{
  "skill_name": "My Custom Skill",
  "files": [
    {
      "path": "SKILL.md",
      "size": 1234,
      "modified": 1704067200.0
    },
    {
      "path": "scripts/example.py",
      "size": 5678,
      "modified": 1704067300.0
    },
    {
      "path": "references/guide.md",
      "size": 2345,
      "modified": 1704067400.0
    }
  ],
  "count": 3
}
```

---

## 7. 스킬 파일 조회

특정 스킬의 파일 내용을 조회합니다.

### 엔드포인트
```
GET /skills/{skill_name}/files/{file_path}
```

### 파라미터
- `skill_name` (경로): 스킬 이름
- `file_path` (경로): 파일 경로 (URL 인코딩 필요, 예: `scripts%2Fexample.py`)

### 사용 예시

**cURL:**
```bash
# 텍스트 파일 조회
curl "http://localhost:8765/skills/My%20Custom%20Skill/files/scripts%2Fexample.py"

# 루트 파일 조회
curl "http://localhost:8765/skills/My%20Custom%20Skill/files/SKILL.md"
```

**Python:**
```python
import requests
from urllib.parse import quote

skill_name = "My Custom Skill"
file_path = "scripts/example.py"

response = requests.get(
    f"http://localhost:8765/skills/{quote(skill_name)}/files/{quote(file_path)}"
)
data = response.json()

if data.get("type") == "text":
    print(f"File: {data['file_path']}")
    print(f"Size: {data['size']} bytes")
    print(f"Content:\n{data['content']}")
else:
    print(f"Binary file: {data['file_path']}")
    print(f"Size: {data['size']} bytes")
    print(f"Base64 content: {data['content_base64'][:50]}...")
```

**JavaScript (fetch):**
```javascript
const skillName = encodeURIComponent("My Custom Skill");
const filePath = encodeURIComponent("scripts/example.py");

fetch(`http://localhost:8765/skills/${skillName}/files/${filePath}`)
  .then(response => response.json())
  .then(data => {
    if (data.type === 'text') {
      console.log('File content:', data.content);
    } else {
      console.log('Binary file, base64:', data.content_base64.substring(0, 50));
    }
  });
```

### 응답 예시 (텍스트 파일)
```json
{
  "skill_name": "My Custom Skill",
  "file_path": "scripts/example.py",
  "type": "text",
  "size": 5678,
  "modified": 1704067300.0,
  "content": "print('Hello, World!')\n# Example script"
}
```

### 응답 예시 (바이너리 파일)
```json
{
  "skill_name": "My Custom Skill",
  "file_path": "assets/image.png",
  "type": "binary",
  "size": 12345,
  "modified": 1704067500.0,
  "content_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

### 에러 응답
- `404`: 스킬 또는 파일을 찾을 수 없음
- `400`: 잘못된 파일 경로

---

## 8. 스킬 파일 업데이트

특정 스킬의 파일을 업데이트합니다.

### 엔드포인트
```
PUT /skills/{skill_name}/files/{file_path}
```

### 파라미터
- `skill_name` (경로): 스킬 이름
- `file_path` (경로): 파일 경로 (URL 인코딩 필요)

### 요청 본문
```json
{
  "content": "file content as text"  // 텍스트 파일의 경우
}
```
또는
```json
{
  "content_base64": "base64_encoded_content"  // 바이너리 파일의 경우
}
```

### 사용 예시

**cURL:**
```bash
# 텍스트 파일 업데이트
curl -X PUT \
  "http://localhost:8765/skills/My%20Custom%20Skill/files/scripts%2Fexample.py" \
  -H "Content-Type: application/json" \
  -d '{"content": "print(\"Updated content!\")"}'

# 바이너리 파일 업데이트
curl -X PUT \
  "http://localhost:8765/skills/My%20Custom%20Skill/files/assets%2Fimage.png" \
  -H "Content-Type: application/json" \
  -d '{"content_base64": "iVBORw0KGgoAAAANSUhEUgAA..."}'
```

**Python:**
```python
import requests
from urllib.parse import quote
import base64

skill_name = "My Custom Skill"
file_path = "scripts/example.py"

# 텍스트 파일 업데이트
response = requests.put(
    f"http://localhost:8765/skills/{quote(skill_name)}/files/{quote(file_path)}",
    json={"content": "print('Updated!')\n# New content"}
)
print(response.json())

# 바이너리 파일 업데이트
with open("new_image.png", "rb") as f:
    content_b64 = base64.b64encode(f.read()).decode("utf-8")
    
response = requests.put(
    f"http://localhost:8765/skills/{quote(skill_name)}/files/{quote('assets/image.png')}",
    json={"content_base64": content_b64}
)
print(response.json())
```

**JavaScript (fetch):**
```javascript
const skillName = encodeURIComponent("My Custom Skill");
const filePath = encodeURIComponent("scripts/example.py");

fetch(`http://localhost:8765/skills/${skillName}/files/${filePath}`, {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    content: "print('Updated!')\n# New content"
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

**JavaScript (axios):**
```javascript
import axios from 'axios';

const skillName = "My Custom Skill";
const filePath = "scripts/example.py";

// 텍스트 파일 업데이트
try {
  const response = await axios.put(
    `http://localhost:8765/skills/${encodeURIComponent(skillName)}/files/${encodeURIComponent(filePath)}`,
    {
      content: "print('Updated!')\n# New content"
    },
    {
      headers: {
        'Content-Type': 'application/json'
      }
    }
  );
  console.log('File updated:', response.data);
} catch (error) {
  console.error('Error updating file:', error.response?.data || error.message);
}

// 바이너리 파일 업데이트 (File 객체에서)
const fileInput = document.querySelector('input[type="file"]');
const file = fileInput.files[0];

if (file) {
  const reader = new FileReader();
  reader.onload = async () => {
    const base64Content = reader.result.split(',')[1]; // data:image/png;base64, 제거
    
    try {
      const response = await axios.put(
        `http://localhost:8765/skills/${encodeURIComponent(skillName)}/files/${encodeURIComponent('assets/image.png')}`,
        {
          content_base64: base64Content
        },
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      console.log('Binary file updated:', response.data);
    } catch (error) {
      console.error('Error updating binary file:', error.response?.data || error.message);
    }
  };
  reader.readAsDataURL(file);
}

// 또는 Promise 기반으로
const updateTextFile = async (skillName, filePath, content) => {
  try {
    const response = await axios.put(
      `http://localhost:8765/skills/${encodeURIComponent(skillName)}/files/${encodeURIComponent(filePath)}`,
      { content },
      { headers: { 'Content-Type': 'application/json' } }
    );
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || error.message);
  }
};

// 사용 예시
updateTextFile("My Custom Skill", "scripts/example.py", "print('Hello!')")
  .then(data => console.log('Success:', data))
  .catch(error => console.error('Error:', error));
```

### 응답 예시
```json
{
  "skill_name": "My Custom Skill",
  "file_path": "scripts/example.py",
  "size": 25,
  "modified": 1704067600.0,
  "message": "File updated successfully"
}
```

### 주의사항
- 파일 업데이트 후 스킬이 자동으로 재로드되고 인덱스가 업데이트됩니다.
- 존재하지 않는 파일 경로를 지정하면 새 파일이 생성됩니다.
- 부모 디렉토리가 없으면 자동으로 생성됩니다.

---

## 9. 스킬 파일 삭제

특정 스킬의 파일을 삭제합니다.

### 엔드포인트
```
DELETE /skills/{skill_name}/files/{file_path}
```

### 파라미터
- `skill_name` (경로): 스킬 이름
- `file_path` (경로): 파일 경로 (URL 인코딩 필요)

### 사용 예시

**cURL:**
```bash
curl -X DELETE \
  "http://localhost:8765/skills/My%20Custom%20Skill/files/scripts%2Fold_script.py"
```

**Python:**
```python
import requests
from urllib.parse import quote

skill_name = "My Custom Skill"
file_path = "scripts/old_script.py"

response = requests.delete(
    f"http://localhost:8765/skills/{quote(skill_name)}/files/{quote(file_path)}"
)
print(response.json())
```

**JavaScript (fetch):**
```javascript
const skillName = encodeURIComponent("My Custom Skill");
const filePath = encodeURIComponent("scripts/old_script.py");

fetch(`http://localhost:8765/skills/${skillName}/files/${filePath}`, {
  method: 'DELETE'
})
.then(response => response.json())
.then(data => console.log(data));
```

**JavaScript (axios):**
```javascript
import axios from 'axios';

const skillName = "My Custom Skill";
const filePath = "scripts/old_script.py";

// 기본 사용법
try {
  const response = await axios.delete(
    `http://localhost:8765/skills/${encodeURIComponent(skillName)}/files/${encodeURIComponent(filePath)}`
  );
  console.log('File deleted:', response.data);
} catch (error) {
  console.error('Error deleting file:', error.response?.data || error.message);
}

// Promise 기반 함수로 만들기
const deleteSkillFile = async (skillName, filePath) => {
  try {
    const response = await axios.delete(
      `http://localhost:8765/skills/${encodeURIComponent(skillName)}/files/${encodeURIComponent(filePath)}`
    );
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || error.message);
  }
};

// 사용 예시
deleteSkillFile("My Custom Skill", "scripts/old_script.py")
  .then(data => {
    console.log('Success:', data.message);
    // 파일 삭제 성공 후 UI 업데이트 등
  })
  .catch(error => {
    console.error('Error:', error.message);
    // 에러 처리
  });

// React 컴포넌트에서 사용 예시
const handleDeleteFile = async (skillName, filePath) => {
  try {
    await deleteSkillFile(skillName, filePath);
    alert('파일이 삭제되었습니다.');
    // 파일 목록 새로고침
    refreshFileList();
  } catch (error) {
    alert(`삭제 실패: ${error.message}`);
  }
};
```

### 응답 예시
```json
{
  "skill_name": "My Custom Skill",
  "file_path": "scripts/old_script.py",
  "message": "File deleted successfully"
}
```

### 제한사항
- `SKILL.md` 파일은 삭제할 수 없습니다.
- 파일 삭제 후 스킬이 자동으로 재로드되고 인덱스가 업데이트됩니다.

### 에러 응답
- `400`: SKILL.md 삭제 시도 또는 잘못된 경로
- `404`: 스킬 또는 파일을 찾을 수 없음

---

## 10. 스킬 삭제

전체 스킬(디렉토리 및 모든 파일)을 삭제합니다.

### 엔드포인트
```
DELETE /skills/{skill_name}
```

### 파라미터
- `skill_name` (경로): 스킬 이름

### 사용 예시

**cURL:**
```bash
curl -X DELETE \
  "http://localhost:8765/skills/My%20Custom%20Skill"
```

**Python:**
```python
import requests
from urllib.parse import quote

skill_name = "My Custom Skill"

response = requests.delete(
    f"http://localhost:8765/skills/{quote(skill_name)}"
)
print(response.json())
```

**JavaScript (fetch):**
```javascript
const skillName = encodeURIComponent("My Custom Skill");

fetch(`http://localhost:8765/skills/${skillName}`, {
  method: 'DELETE'
})
.then(response => response.json())
.then(data => console.log(data));
```

**JavaScript (axios):**
```javascript
import axios from 'axios';

const skillName = "My Custom Skill";

// 기본 사용법
try {
  const response = await axios.delete(
    `http://localhost:8765/skills/${encodeURIComponent(skillName)}`
  );
  console.log('Skill deleted:', response.data);
} catch (error) {
  console.error('Error deleting skill:', error.response?.data || error.message);
}

// Promise 기반 함수로 만들기
const deleteSkill = async (skillName) => {
  try {
    const response = await axios.delete(
      `http://localhost:8765/skills/${encodeURIComponent(skillName)}`
    );
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || error.message);
  }
};

// 사용 예시
deleteSkill("My Custom Skill")
  .then(data => {
    console.log('Success:', data.message);
    // 스킬 삭제 성공 후 UI 업데이트 등
  })
  .catch(error => {
    console.error('Error:', error.message);
    // 에러 처리
  });

// React 컴포넌트에서 사용 예시
const handleDeleteSkill = async (skillName) => {
  if (!confirm(`정말로 스킬 '${skillName}'을(를) 삭제하시겠습니까?`)) {
    return;
  }
  
  try {
    await deleteSkill(skillName);
    alert('스킬이 삭제되었습니다.');
    // 스킬 목록 새로고침
    refreshSkillList();
  } catch (error) {
    alert(`삭제 실패: ${error.message}`);
  }
};
```

### 응답 예시
```json
{
  "skill_name": "My Custom Skill",
  "message": "Skill deleted successfully"
}
```

### 동작 방식
1. 스킬이 검색 엔진 인덱스에서 제거됩니다.
2. 스킬 디렉토리와 모든 파일이 삭제됩니다.
3. 검색 인덱스가 자동으로 재구성됩니다.

### 에러 응답
- `400`: 잘못된 스킬 경로 또는 경로 탐색 시도
- `404`: 스킬을 찾을 수 없음
- `500`: 스킬 삭제 실패 또는 로컬 스킬 스토리지 미설정

---

## 공통 에러 응답

모든 API는 다음과 같은 공통 에러 응답을 반환할 수 있습니다:

### 503 Service Unavailable
```json
{
  "detail": "Backend not fully initialized"
}
```
서버가 아직 초기화되지 않았습니다. 잠시 후 다시 시도하세요.

### 409 Conflict
```json
{
  "detail": "Skill loading in progress. Try again shortly."
}
```
스킬 로딩이 진행 중입니다. 완료 후 다시 시도하세요.

### 500 Internal Server Error
```json
{
  "detail": "No local skill source configured"
}
```
로컬 스킬 스토리지가 설정되지 않았습니다.

---

## URL 인코딩 참고

파일 경로에 특수 문자가 포함된 경우 URL 인코딩이 필요합니다:

| 문자 | 인코딩 |
|------|--------|
| `/` | `%2F` |
| ` ` (공백) | `%20` |
| `#` | `%23` |
| `?` | `%3F` |
| `&` | `%26` |

**예시:**
- 원본 경로: `scripts/example.py`
- 인코딩된 경로: `scripts%2Fexample.py`

---

## 전체 워크플로우 예시

스킬을 업로드하고 편집하는 전체 과정:

```python
import requests
from urllib.parse import quote

BASE_URL = "http://localhost:8765"

# 1. 스킬 업로드
with open("my-skill.zip", "rb") as f:
    files = {"file": ("my-skill.zip", f, "application/zip")}
    response = requests.post(f"{BASE_URL}/skills/upload", files=files)
    print("Upload:", response.json())

# 2. 업로드된 스킬 목록 확인
response = requests.get(f"{BASE_URL}/skills/list")
skills = response.json()["skills"]
skill_name = skills[0]["name"]
print(f"Uploaded skill: {skill_name}")

# 3. 스킬 파일 목록 조회
response = requests.get(
    f"{BASE_URL}/skills/{quote(skill_name)}/files"
)
files = response.json()["files"]
print(f"Files: {[f['path'] for f in files]}")

# 4. 파일 조회
file_path = files[1]["path"]  # 두 번째 파일
response = requests.get(
    f"{BASE_URL}/skills/{quote(skill_name)}/files/{quote(file_path)}"
)
file_data = response.json()
print(f"File content: {file_data['content'][:100]}...")

# 5. 파일 업데이트
new_content = file_data["content"] + "\n# Updated at 2024-01-01"
response = requests.put(
    f"{BASE_URL}/skills/{quote(skill_name)}/files/{quote(file_path)}",
    json={"content": new_content}
)
print("Update:", response.json())

# 6. 스킬 다운로드 (백업)
response = requests.get(
    f"{BASE_URL}/skills/download",
    params={"name": skill_name}
)
with open("backup.zip", "wb") as f:
    f.write(response.content)
print("Backup saved")
```

---

## 11. 멀티테넌트 및 권한 관리

### 스킬 Scope 시스템

스킬 엔진은 두 가지 scope를 지원합니다:

#### Global 스킬 (`scope="global"`)
- 기본 스킬 (GitHub에서 로드된 스킬)
- 모든 에이전트가 항상 조회 가능
- `tenant_id` 없이 업로드된 스킬도 global로 설정됨

#### Tenant 스킬 (`scope="tenant"`)
- 업로드 시 `tenant_id`를 제공한 스킬
- 다음 조건을 모두 만족해야 조회 가능:
  1. `skill.tenant_id == tenant_id` (동일한 테넌트)
  2. `skill.name in allowed_skill_names` (에이전트가 DB에 명시적으로 보유)

### 권한 관리 원칙

**중요**: 스킬 엔진은 DB를 직접 조회하지 않습니다. 권한 판단은 상위 API 서버의 책임입니다.

1. **API 서버 책임**:
   - `users` 테이블에서 에이전트 정보 조회
   - `tenant_id`와 `skills` 컬럼(콤마로 구분된 스킬 이름 목록) 추출
   - `allowed_skill_names` 리스트 생성

2. **스킬 엔진 책임**:
   - 제공된 `tenant_id`와 `allowed_skill_names`를 신뢰
   - Scope 기반 필터링 수행

### API 서버 통합 예시

```python
# API 서버에서 스킬 검색 호출 예시
import requests

# 1. DB에서 에이전트 정보 조회
agent = db.query(
    "SELECT tenant_id, skills FROM users WHERE id = ?",
    [agent_id]
)
tenant_id = agent.tenant_id
allowed_skill_names = agent.skills.split(",") if agent.skills else []

# 2. MCP 핸들러를 통해 스킬 검색
# (MCP 프로토콜 사용 시)
mcp_response = await mcp_client.call_tool(
    "find_helpful_skills",
    {
        "task_description": "analyze data",
        "tenant_id": tenant_id,
        "allowed_skill_names": allowed_skill_names,
        "top_k": 3
    }
)
```

### 필터링 규칙

검색 결과는 다음 규칙으로 필터링됩니다:

```
if skill.scope == "global":
    include  # 항상 포함 (모든 테넌트, 모든 에이전트에게 조회 가능)

elif skill.scope == "tenant":
    include only if (
        skill.tenant_id == tenant_id
        and skill.name in allowed_skill_names  # 명시적으로 포함되어야만 조회 가능
    )
```

**중요**: 업로드된 스킬(Tenant 스킬)은 `allowed_skill_names`에 **명시적으로** 포함되어야만 조회 가능합니다. 
기본 스킬(Global 스킬)처럼 모든 테넌트나 에이전트에게 자동으로 조회되지는 않습니다.

### 주의사항

- `allowed_skill_names`가 `None` 또는 빈 리스트일 경우:
  - **Tenant 스킬은 모두 제외됨** (명시적으로 허용된 스킬이 없으므로)
  - Global 스킬만 반환됨

- Tenant 스킬 접근 규칙:
  - ✅ `allowed_skill_names`에 스킬 이름이 **명시적으로** 포함되어야만 조회 가능
  - ❌ `allowed_skill_names`가 비어있으면 Tenant 스킬은 절대 조회되지 않음
  - ❌ 같은 `tenant_id`라도 `allowed_skill_names`에 없으면 조회 불가

- 스킬 엔진은 권한 판단을 하지 않습니다:
  - ❌ `users` 테이블 구조를 알지 않음
  - ❌ SQL/Supabase SDK를 호출하지 않음
  - ✅ 제공된 `tenant_id`와 `allowed_skill_names`만 신뢰

---

## 추가 참고사항

- 모든 API는 JSON 형식으로 응답을 반환합니다 (다운로드 API 제외).
- 파일 경로는 항상 스킬 디렉토리 기준 상대 경로입니다.
- 파일 업데이트/삭제 후 스킬이 자동으로 재로드되어 검색 인덱스가 업데이트됩니다.
- 바이너리 파일은 base64 인코딩을 사용합니다.
- 텍스트 파일은 UTF-8 인코딩을 사용합니다.
- 멀티테넌트 환경에서는 `tenant_id`를 제공하여 스킬을 업로드하면 해당 테넌트 전용 스킬이 됩니다.

