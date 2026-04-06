# project_singularity

# 1. 의존성 파일 구조

설계/로봇 작업의 의존성을 분리해서 관리:

```
requirements.txt          ← 공통 (python-dotenv)
requirements_design.txt   ← 설계용 (requests, cadquery)
requirements_robot.txt    ← 로봇 구동용 (lerobot, torch)
```

# 2. Groq API 키 설정 방법

## 개요
이 프로젝트는 Groq API를 사용합니다. 보안상 API 키는 GitHub에 업로드하지 않으므로, 각 개발 환경에서 로컬로 설정해야 합니다.

## 설정 단계

### 1. Groq API 키 발급받기
- [Groq Console](https://console.groq.com/keys)에 접속
- 계정 로그인 또는 회원가입
- API 키 생성
- 키 복사 (예: `gsk_TDimfSK37a250...`)

### 2. 로컬 환경에서 설정

#### Option A: `.bashrc.local` 파일 생성 (권장)

**Linux/Mac:**
```bash
# 1. .bashrc.local 파일 생성
cd ε1/Hylion
cp .bashrc.example .bashrc.local

# 2. 편집기에서 열기
nano .bashrc.local
# 또는
vim .bashrc.local

# 3. API 키 입력
# export GROQ_API_KEY="gsk_YOUR_API_KEY_HERE" 부분에 본인의 키 입력

# 4. 저장 후 추가 명령어 입력
source ~/.bashrc
```

**Windows (PowerShell):**
```powershell
# 1. .bashrc.local 파일 생성
cd ε1\Hylion
Copy-Item .bashrc.example .bashrc.local

# 2. 파일 편집 (메모장 또는 VS Code)
notepad .bashrc.local
# 또는
code .bashrc.local

# 3. API 키 입력 후 저장
# export GROQ_API_KEY="gsk_YOUR_API_KEY_HERE"
```

#### Option B: 환경 변수로 직접 설정

**Linux/Mac:**
```bash
export GROQ_API_KEY="gsk_YOUR_API_KEY_HERE"
```

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="gsk_YOUR_API_KEY_HERE"
```

**Windows (명령 프롬프트):**
```cmd
set GROQ_API_KEY=gsk_YOUR_API_KEY_HERE
```

### 3. 설정 확인

```bash
# 터미널에서 확인
echo $GROQ_API_KEY

# Python에서 확인
python -c "import os; print(os.getenv('GROQ_API_KEY'))"
```

## `.bashrc.local` 파일 구조

```bash
# .bashrc.local 예시
export GROQ_API_KEY="gsk_YOUR_API_KEY_HERE"

# 필요한 다른 환경 변수 추가 가능
# export OTHER_KEY="value"
```

## 주의사항

- ⚠️ **API 키를 절대 GitHub에 커밋하지 마세요!**
- `.bashrc.local` 파일은 `.gitignore`에 등록되어 있어 자동으로 추적되지 않습니다
- 각 개발자/컴퓨터마다 본인의 API 키를 설정해야 합니다
- API 키를 공개하면 누구나 사용할 수 있으므로 보안에 주의하세요

## 팀 협업 시

1. **프로젝트 클론:**
   ```bash
   git clone https://github.com/BaboGaeguri/project_singularity.git
   cd project_singularity
   ```

2. **`.bashrc.local` 설정:**
   ```bash
   cd ε1/Hylion
   cp .bashrc.example .bashrc.local
   # 본인의 API 키로 수정
   ```

3. **`.bashrc` 로드:**
   ```bash
   source ~/.bashrc
   ```

## 문제 해결

**문제: "GROQ_API_KEY not found" 에러**
- `.bashrc.local` 파일이 생성되었는지 확인
- API 키가 올바르게 입력되었는지 확인
- `.bashrc`를 다시 로드: `source ~/.bashrc`