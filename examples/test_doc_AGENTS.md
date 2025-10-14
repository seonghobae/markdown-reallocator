# AGENTS.md

---
# Physical location: .cursor/AGENTS.md (subtree)
# Logical effect: Entire project via symlinks at root
physical_location: ".cursor/"
effective_scope: "project-wide-via-symlink"
symlink_structure:
  - "../AGENTS.md -> .cursor/AGENTS.md"
  - "../CLAUDE.md -> .cursor/CLAUDE.md -> .cursor/AGENTS.md"
  - "../GEMINI.md -> .cursor/AGENTS.md"
applies_to:
  - "**/*"  # Entire project tree
resolution_markers:
  - ".vooster/project.json"
  - ".git"
  - "package.json"
dangerous_ops:
  require_confirmation: true
  forbidden: ["echo", "pip install", "npm run dev", "pkill node"]
maintainer: "subtree-maintainers"
last_updated: "2025-10-15"
---

## What is AGENTS.md

AGENTS.md is a lightweight, repository‑root markdown file that gives AI coding agents machine‑readable guidance on how to operate in this project (build, test, lint, task management, conventions). Think of it as a "README for agents".

**Note**: CLAUDE.md and GEMINI.md are symbolic links to this AGENTS.md file.

**Multi-Agent Coordination**: All agents must follow these rules consistently. Multiple agents work simultaneously; vooster‑ai coordination is mandatory.

### Language Policy (MANDATORY)

- 기본 응답 언어는 한국어입니다. 사용자와 상호작용할 때는 설명, 요약, 보고서를 모두 한국어로 작성하세요.
- 코드, 로그, 에러 메시지 등 원문 인용이 필요한 경우에만 해당 언어를 그대로 유지하되, 필요한 맥락 설명은 한국어로 덧붙입니다.
- 다국어 번역 요청이 있는 경우, 요청된 언어를 제공하되 한국어 요약을 함께 포함합니다.

### Verification Requests (MANDATORY)

- 사용자가 “확인해 주세요”, “검증해 주세요”, “동일한지 확인” 등 확인을 명시적으로 요청하면, 에이전트는 가능한 한 자체적으로 검증을 수행해야 합니다.
- 환경 제약 등으로 직접 실행이나 연결이 불가능한 경우, 불가 사유와 함께 코드·설계 분석 등 대체 근거를 제시합니다.
- 확인 결과를 보고할 때는 검증 방식(실행/정적 분석/문서 근거)과 결론을 명확히 구분하여 기술합니다.

### Multi-Agent Task Status Verification (CRITICAL)

- **Status Verification Protocol**: Even if you don't ask, verify that the task you want to proceed is in progress in vooster and proceed if it is in BACKLOG status
- **Concurrent Agent Awareness**: Other LLM Agents (Claude, Gemini, Codex, etc.) may be working on the task you want to do at the same time, so please check the task status again from time to time before starting the task
- **Task Competition Resolution**: When agents compete for the same subtask, they should either:
  - **a)** Avoid competing if work has already started (check vooster task/subtask status)
  - **b)** Complement each other's work by leaving detailed comments about intentions in code or reference vooster-ai task/subtask IDs
- **Code Communication**: Use code comments to communicate intentions to other agents working on the same codebase
- **“Ping” 정의**: 별도 알림 기능은 없으며, “ping”은 vooster 코멘트 또는 elimination log에 타임스탬프/요청 내용을 남기는 행위를 의미한다. 응답 대기 시간은 해당 코멘트 시각을 기준으로 계산한다.
- **Coordination Examples**:

  ```javascript
  // NOTE: Agent coordination - working on user authentication flow
  // Related vooster task: T-001, subtask: implementing JWT validation
  // If another agent sees this, please coordinate via vooster task comments
  ```

#### Implementation vs Audit Parallelism (MANDATORY)

- 역할 식별 우선: 착수 전 `vooster-ai__read_task`로 acceptance criteria와 기존 코멘트/완료 로그를 검토하고, 아래 규칙으로 본인의 역할을 결정한다.  
  - 코드/SQL/문서 수정, 테스트 추가, 상태 변경 등 “산출물 작성” 의도가 있으면 **Implementation**으로 분류한다.  
  - 산출물 없이 근거 수집, 정책 준수 검사, 로그 검증, 문제 재현만 수행하면 **Audit**으로 분류한다. Docker 컨테이너 재시작, .env 값 변경, `uv` 패키지 설치/제거, 데이터베이스/pg_cron 상태 변경 등 환경을 변형하는 동작은 모두 Implementation 범주에 속한다.
  - 역할이 모호하면 처음 5분 안에 vooster 코멘트로 “`Role undecided`”를 남기고, 관련 태스크 소유자에게 질문하거나 별도 코멘트에서 합의를 얻는다. 답이 없으면 Implementation은 상태를 `IN_PROGRESS`로 바꾼 뒤 진행하고, Audit은 수정 없이 증거 수집만 수행한다.
- 역할 선언: 동일 태스크/서브태스크에서 구현자(Implementation)와 감사자(Audit)가 동시에 작업해야 할 경우, 각자 vooster 코멘트와 elimination log에 `Implementation owner` 또는 `Audit owner` 라벨을 명시하고, 작업 범위·예상 소요 시간을 기록한다. 구현자는 반드시 상태를 `IN_PROGRESS`로 전환한 뒤 착수한다.
- 감사 중 코드 수정 필요 시: 감사 과정에서 즉각적인 코드/SQL/구성 변경이 필요하다고 판단되면 (예: 재현을 위해 소규모 패치가 필요하거나 치명적 회귀를 즉시 막아야 하는 경우) 아래 순서를 따른다.  
  1. vooster 코멘트에 “`Audit → Implementation switch`”를 선언하고 이유를 기록한다.  
  2. 해당 서브태스크가 `BACKLOG`라면 `IN_PROGRESS`로 전환하고, 기존 감사 노트를 follow-up subtask로 남긴다.  
  3. 가능한 경우 별도의 구현 담당자를 요청하거나 새 구현 서브태스크를 생성한다. 감사자가 직접 수정한다면 역할을 Implementation으로 전환하고 수정 후 다시 감사 노트를 업데이트한다.  
  4. 긴급 수정이 필요한데 구현자와 합의가 불가능한 경우에만 최소한의 안전 패치를 수행하고, 즉시 follow-up 태스크/코멘트로 후속 검증을 요청한다.  
- 변경 권한 분리: 위 전환 절차를 거치지 않은 감사자는 구현자가 작업 중인 동안 코드/SQL/구성 파일을 수정하지 않는다. 발견한 이슈는 **코멘트 + follow-up subtask**로 남기고, 긴급 수정이 필요한 경우 구현자에게 핑 후 합의가 되거나 Stale 프로토콜 요건(응답 없음 2h 등)을 충족할 때까지 대기한다.
- 증거 및 로그 공유: 감사자는 실행 로그, SQL 결과, 정책 위반 근거 등 읽기 전용 증거를 수집하여 문서화하고, 구현자는 작업 마무리 시 감사자가 요청한 로그 위치(예: `docs/T-378-implementation-summary.md` 섹션)를 업데이트한다. 두 역할 모두 `vooster-ai__read_task` 재조회 결과(타임스탬프 포함)를 메모에 첨부해 최신 상태를 검증한다.
- 충돌 감지 대응: 감사 중인 항목에서 구현자가 예상과 다른 변경을 시작하면 감사자는 즉시 `read_task` 재조회 후 코멘트로 상황을 공유하고, 필요한 경우 임시 감사 일시 중지 상태를 선언한다. 구현자는 감사자 코멘트 확인 후 중복 작업 여부를 명확히 하고, 계획 변경이 생기면 즉시 업데이트한다.
- 역할 종료 선언: 구현 완료 또는 감사 종료 시, 각자는 코멘트에 `Implementation complete` / `Audit complete`를 기록하고, 필요한 후속 태스크(TODO, 재검증 항목 등)를 명시한다. 다른 에이전트가 이어받을 수 있도록 상태/증거 링크를 남긴 뒤 역할을 해제한다.

#### Coordination Fallback (진행 보장용 원칙)

- 의도 기록 후 응답이 없으면 **멈추지 말고 진행**: vooster에 작업 의도를 남기고 최신 상태를 확인했는데도 다른 Agent의 반응이나 배정이 없다면, 기록된 시점과 근거를 남긴 뒤 그대로 작업을 시작한다.
- 충돌 징후가 보이면 즉시 재조회: 작업 도중 상태가 변하거나 다른 Agent가 IN_PROGRESS로 전환하면, 그 즉시 재조회하고 증분 강화 프로토콜에 따라 조정한다.
- 반복 확인 주기: 장시간 작업 시 `read_task` 재조회 및 vooster 코멘트 갱신으로 “현재 내가 진행 중”임을 명시한다 (30~45분 간격 권장).
- 필요한 자료 부족 시: "필수 아티팩트 없음"을 elimination log 또는 vooster 코멘트에 남기고, 확보 가능한 정보로 최선의 판단을 내린다. 정보 부재만을 이유로 작업을 중단하지 않는다.
- 규칙 해석이 애매한 경우: 우선 best-effort 구현/감사를 진행하고, 판단 근거와 남은 의문을 같은 태스크의 코멘트나 별도 follow-up task로 적어 두어 다음 Agent가 참고하도록 한다.
- 리스트 캐시 주의: `vooster-ai__list_task` 결과가 오래된 값이어도 **`read_task` 재조회가 최신 상태이므로 그대로 진행**한다. 리스트 전체가 DONE처럼 보여도, 개별 판단은 `read_task` 기준으로 내리고 상황을 elimination log에 기록한다.
- 로컬 스냅샷 필요 시: `vooster-ai__download_all_task_files` → `npx @vooster/cli@latest tasks:download --api-key <key>`를 실행해 `.vooster/tasks/`/`tasks.json`을 최신화한 뒤, 해당 스냅샷과 `read_task` 결과를 함께 참고한다.
- 대량 필터링 팁: Task 수가 많다면 `.vooster/tasks.json`을 `jq`로 전처리하여 감사 우선순위를 추려낸 뒤 각 항목을 `read_task`로 재확인한다.
- 진행 보고 후 즉시 다음 단계: 진행 상황은 **vooster-ai 기록(상태 변경, 코멘트, elimination log)**에 우선 저장한다. 사용자가 별도 보고를 요청하지 않았다면 추가 메시지를 보낼 필요 없이 곧바로 다음 태스크를 착수한다. 필요한 경우 "계속 진행" 정도만 남기고 대기하지 말 것.

#### Structured Work-Breakdown Briefing Protocol (MANDATORY)

- **Trigger**: 사용자가 “워크 브레이크다운”, “브리핑”, “task/subtask id와 함께 제시” 등 구조화된 보고를 요구하면 본 프로토콜을 즉시 적용한다.
- **Mandatory Fields**: 아래 7개 항목을 모두 채운다.
- **두 축 구성**: 응답은 반드시 `Current States`와 `Next Steps` 두 섹션으로 나눈다.  
  - **Current States** 섹션에는 다음 항목을 포함한다.  
    1. **Scope** – 관련 Task/Sub-task ID, 제목, 현재 상태  
    2. **Priority & Blockers** – 우선순위, 위험 요소, 해결 방안  
    3. **Responsibility & Location** – 담당 주체(Agent/팀)와 진행 위치(파일, DB, 문서 등)  
    4. **Why / Value** – 요청 배경, 기대 효과, 비즈니스/기술 가치  
    5. **Status Snapshot** – 최신 실행 결과(타임스탬프, 로그/SQL 요약)  
  - **Next Steps** 섹션에는 다음 항목을 포함한다.  
    6. **Execution Steps** – 구체 실행 절차(명령어, 함수, 테스트, 검증 쿼리 포함)  
    7. **Best Practices / References** – 관련 규약, 산업 표준, 내부 문서 조사 결과 (필요 시 추가 리서치)  
- **Evidence-first 원칙**: 위 항목을 작성하기 전에 `vooster-ai__read_task` 및 최신 로그/문서를 재확인하고, 부족한 데이터는 즉시 조사(예: SQL, grep, 문서 검색)하여 근거를 확보한다.
- **Evidence-first 원칙**: 위 항목을 작성하기 전에 `vooster-ai__read_task` 및 최신 로그/문서를 재확인하고, 부족한 데이터는 즉시 조사(예: SQL, grep, 문서 검색)하여 근거를 확보한다.
- **미충족 시 보고 방식**: 항목을 채우지 못하면 “데이터 부재”라고만 쓰지 말고, 누락 원인과 확보 계획(담당자 문의, 추가 조사 일정 등)을 명시한다.
- **규칙 변경 시 갱신**: 사용자 요청으로 보고 포맷이 바뀌면 먼저 이 섹션을 업데이트한 뒤 새 포맷을 적용한다.

### Plan Update Cadence (MUST)
- 목적: 복잡/다단계 작업 동안 진행 상황을 투명하게 공유하고 충돌을 방지한다.
- 원칙:
  - `update_plan`을 비트별(의미 있는 단계 시작/종료 시점)로 갱신한다.
  - 항상 정확히 하나의 `in_progress` 단계만 유지한다(나머지는 `pending`/`completed`).
  - 단계 전환 전 `vooster-ai__read_task`로 현재 상태를 재확인한다(병행 작업 충돌 방지).
  - 각 갱신에 짧은 설명을 포함하고, 가능하면 Evidence 문서(파일 경로)나 실행 커맨드를 함께 참조한다.
  - 장시간 작업은 30–45분 주기로 상태를 재조회하고 `update_plan`을 갱신한다(“나는 진행 중” 명시).
  - 브리핑 요구가 있을 때는 본 계획 상태를 ‘Current States/Next Steps’ 보고와 연계한다.
- 형식:
  - 단계 문구는 5–7단어로 간결히(예: “pytest 실행(Evidence 기록)”).
  - 상태는 `pending`/`in_progress`/`completed`만 사용한다.
  - 불확실/블로커 발생 시 즉시 `explanation`에 원인·대안·다음 확인 지점 기록.

### Batch Chunking & Dispatch Policy (MANDATORY)

- 단일 기준(Only two criteria): 배치 청크 분할과 디스패치 결정은 오직 다음 2가지 DB 기준으로만 수행한다.
  - Token Queue Limit: 데이터베이스에 저장된 토큰 큐 제한(예: 누적 토큰 윈도우/그룹별 토큰 상한)을 초과하지 않도록 분할한다.
  - Payload Size Limit: 게이트웨이/파일 API가 허용하는 페이로드(파일) 최대 바이트 기준을 초과하지 않도록 분할한다.
- 구현 위치 제한(Postgres-only): 분할/디스패치 로직은 전적으로 PostgreSQL 함수/pg_cron 잡에서 수행한다. Python/CLI 레벨에서 `chunk_size`나 `window_requests` 같은 파라미터로 분할을 제어하지 않는다.
- 금지 키워드(코드/운영 파라미터): `chunk_size`, `window_requests` 등 임의 요청/개수 기반 분할 파라미터는 사용 금지. 누적 토큰/페이로드 용량 기준만 허용한다.
- 누적 기준(Scheduler): 여러 시스템/모델에서 동시 제출되는 경우에도 pg_cron 스케줄러가 DB 내 누적 카운터(토큰 합계/페이로드 합계)를 기준으로 현재 윈도우에서 생성/전송할 청크 수를 결정한다.
- 병렬 처리 원칙: 함수 내부에서 `FOR UPDATE SKIP LOCKED` 등 동시성 제어를 사용하여 병렬 워커/pg_cron 잡이 안전하게 동작하도록 한다. 직렬화된 단일 청크 생성 호출에 의존하지 않는다(필요 시 한 호출에서 복수 청크 생성).
- Python 역할 축소: Python/CLI는 트리거/모니터만 수행(등록·상태 조회·증거 기록). 분할/예산·디스패치 결정은 DB에서만 한다.
- 타임아웃 정책: 연결 타임아웃만 허용. 운영/동작 시간 타임아웃으로 분할/디스패치를 좌우하지 않는다.
- Evidence: 페이로드 크기·토큰 카운트·스케줄 결정·디스패치 결과는 DB 로그/테이블에 기록한다(파일/임시물 금지).

## MULTI-AGENT TASK MODIFICATION PROTOCOL (다중 Agent Task 수정 프로토콜 - MANDATORY)

### Core Principle: NO Override, Incremental Enhancement (덮어쓰기 금지, 증분 개선)

### Problem Scenario

```markdown
1. Agent A starts audit: Plans to change Task T-001 from BACKLOG to WONT
2. During analysis: Identifies issues with T-001, drafts modification plan
3. At modification time: Agent B has already changed T-001 to DONE with implementation complete
4. ❌ WRONG RESPONSE: Agent A overwrites T-001 to WONT based on own analysis
5. Result: Agent B's work lost, completion fact erased from records
```

### Correct Response: 4-Stage Protocol

#### Stage 1: Pre-Modification Verification (재확인)
```bash
# Before ANY task modification, re-query latest state
CURRENT_STATE=$(mcp__vooster-ai__read_task(taskId="T-XXX"))

# Check if another agent modified since analysis started
if CURRENT_STATE.status != EXPECTED_STATUS:
    # Another agent modified this task
    # ABORT current modification plan
    # Proceed to Stage 2
```

#### Stage 2: Change Analysis (변경 사항 분석)

```markdown
Compare original analysis vs current state:
- What changed? (status, aiPrompt, completionDetails, etc.)
- Which agent made changes? (check timestamps, vooster logs)
- Why did they change it? (read completionDetails, confidenceDetails)
- Does current state conflict with my findings?
```

#### Stage 3: Incremental Enhancement (증분 강화)

##### Pattern A: Status Already Advanced (상태가 이미 진행됨)


```bash
# Original plan: BACKLOG → WONT
# Current state: DONE (by Agent B)

# ✅ CORRECT: Build upon existing work
NEW_CONTENT="
${CURRENT.completionDetails}

## Additional Verification (Agent A - Audit Complete)
- A2Z Section X compliance verified
- Implementation approach validated
- Additional improvements identified: [specific details]
"

mcp__vooster-ai__update_task_completion_log(
    taskId="T-XXX",
    completionDetails="${NEW_CONTENT}",
    confidenceLevel=ENHANCED_LEVEL,  # May increase/maintain
    confidenceDetails="Original completion verified. Additional audit findings: ..."
)
```

##### Pattern B: Conflicting Findings (상충하는 발견사항)

```bash
# Current: DONE (Agent B claims implemented)
# My finding: Not actually implemented

# ✅ CORRECT: Document conflict, create investigation task
mcp__vooster-ai__add_task(
    summary="Investigate T-XXX completion discrepancy",
    aiPrompt="
    ## Conflict Details
    - Agent B marked as DONE: [timestamp]
    - Agent A audit found: [specific missing items]

    ## Required Actions
    1. Code verification: Check if implementation exists
    2. Cross-agent review: Reconcile findings
    3. Resolution: Update T-XXX status based on evidence
    ",
    importance="MUST",
    urgency=9,
    complexity=6
)

# Do NOT directly change T-XXX status - escalate via new task
```

##### Pattern C: Incremental Update Pattern (증분 업데이트 패턴)

```bash
# General pattern for ANY field update

# 1. Read current content
CURRENT=$(mcp__vooster-ai__read_task(taskId="T-XXX"))

# 2. Preserve existing content, add improvements
NEW_AI_PROMPT="
${CURRENT.aiPrompt}

## Enhancement by Agent [Name] ([Date])
[Additional analysis]
[Improved implementation guidance]
[Additional test cases]
"

# 3. Update with incremental enhancement
mcp__vooster-ai__update_task(
    taskId="T-XXX",
    aiPrompt="${NEW_AI_PROMPT}",
    # Preserve other fields unless specifically updating them
)
```

#### Stage 4: Conflict Escalation (에스컬레이션)

##### When to Escalate


- Irreconcilable status conflicts (Agent A: WONT, Agent B: DONE)
- Contradictory technical findings
- Ambiguous requirements requiring human clarification
- Systematic pattern of inter-agent conflicts

##### Escalation Process

```bash
# 1. Document conflict in vooster
mcp__vooster-ai__add_task(
    summary="Multi-Agent Conflict Resolution: T-XXX",
    aiPrompt="
    ## Conflict Summary
    - Agent A position: [detailed reasoning]
    - Agent B position: [detailed reasoning]
    - Evidence for A: [specific items]
    - Evidence for B: [specific items]

    ## Recommended Resolution
    [Analysis of which position is stronger and why]

    ## Required Decision
    Human review required if agents cannot reach consensus
    ",
    importance="MUST",
    urgency=10,
    complexity=7
)

# 2. Notify via vooster comments
# 3. Continue with other work, avoid blocking
```

### Anti-Patterns (FORBIDDEN)

#### ❌ Pattern 1: Blind Overwrite

```bash
# WRONG: Overwriting without checking current state
mcp__vooster-ai__update_task_status(
    taskId="T-001",
    status="WONT",  # Overwrites Agent B's DONE
    # ... destroys Agent B's work
)
```

#### ❌ Pattern 2: Delete and Recreate

```bash
# WRONG: Deleting task to replace with "correct" version
# This loses all history and other agents' contributions
```

#### ❌ Pattern 3: Parallel Conflicting Updates

```bash
# WRONG: Two agents simultaneously updating same task
# Without pre-modification verification
```

### Correct Patterns (REQUIRED)

#### ✅ Pattern 1: Verification → Analysis → Enhancement

```bash
# 1. Always verify current state first
CURRENT=$(mcp__vooster-ai__read_task(...))

# 2. Analyze what changed since your analysis
if STATE_CHANGED:
    ANALYZE_CHANGES()

# 3. Build upon existing work, don't replace
ENHANCE_EXISTING_CONTENT()

#### Task Update Cascade Rule (Implicit Subtask Updates — REQUIRED)

```
Agent Coordination Header
Agent: Codex CLI Agent (OpenAI)
Task: (ad-hoc AGENTS.md update)
CDHP-Status: triggered
Risk-Score: high (critical_file + unverified model)
```

Trigger Phrases (Korean/English):
- "T-XXX를 업데이트하라", "T-XXX 업데이트", "Update T-XXX", "Modify T-XXX"

Mandate:
- Interpreting these phrases, agents MUST treat task updates as including sub-task updates (status, acceptance criteria, dependencies, aiPrompt) for the same scope.
- If subtasks do not exist but are clearly implied by the directive (e.g., hierarchical commits/push, file moves, reference updates), agents SHOULD propose them and MAY create them upon quick confirmation; if the user’s directive explicitly covers subtasks, creation is authorized.

Required Procedure:
1) Read task: `vooster-ai__read_task(taskId="T-XXX")` and list existing subtasks.
2) If `status = BACKLOG`, set task to IN_PROGRESS before sub-task changes.
3) Update relevant subtasks via `vooster-ai__update_sub_task` (titles, acceptanceCriteria, aiPrompt, dependencies).
4) When new work items are implied and missing, use `vooster-ai__add_sub_tasks` with clear acceptance criteria; preserve additive-only principle and avoid overwriting.
5) For DONE tasks, do NOT change status; instead append findings via `vooster-ai__update_task_completion_log` and, if conflicts arise, create an investigation task (see Pattern B).

**Chain Vocabulary (vooster dependencies)**:
- Treat every ordered `dependencySubTaskIds` sequence as a **chain**. Document and speak about work in terms of chains (e.g., “Chain B: T-378-075 → T-378-089 → …”).
- `dependencySubTaskIds` remains the API field; when editing or reading vooster data, translate “dependency” → “chain” for internal coordination.
- Announce chain intent in vooster comments before modifying the order and after pushing commits.

6) Maintain chains (`dependencySubTaskIds`) so cascaded edits follow logical order (e.g., refs update depends on prior moves).

Safeguards:
- Always re-query current task before modification to avoid parallel conflicts.
- Respect exceptions and protected paths defined elsewhere in this file.
- Do not perform bulk deletions; removal is limited to verified duplicates with canonical replacements.

#### Chain Alignment Protocol (MANDATORY)
- When a user supplies an explicit work breakdown, chain order (dependency order), or SQL verification checklist, treat the sequence as binding for the referenced vooster subtasks.
- Use `vooster-ai__update_sub_task` to set `dependencySubTaskIds` so the execution order matches the requested plan; propagate the chain rather than editing code first.
- If the requested ordering references work that lacks a subtask, create it immediately via `vooster-ai__add_sub_tasks` with clear acceptance criteria before continuing.
- When a blocker is discovered (failing CLI flow, missing data, timeout, etc.), pause code edits and adjust the vooster chain graph first—add or rewire subtasks so the remediation precedes downstream work, then resume implementation against the updated order.
- Re-run `vooster-ai__read_task` after each chain edit to confirm the graph matches the plan; document the adjustments in the implementation summary or elimination log.
- Do not bypass this protocol: chain reshuffles outside vooster tracking are prohibited.
- For every UID you touch, capture the current chain with `vooster-ai__read_task(taskId="T-XXX", subTaskUid="T-XXX-YYY")` before changing dependencies and reference the output in your working notes so concurrent agents can audit the delta.

Tool Mapping:
- Task info: `read_task`, `list_task`
- Subtask details: `read_task` (with `subTaskUid`)
- Subtask edits: `update_sub_task`, `update_subtask_status`
- Subtask creation: `add_sub_tasks`
- Task edits: `update_task` (non-status fields), `update_task_status` (with DONE-required fields), `update_task_completion_log`

### Reverse-Order Reasoning (일반화 규칙 — MUST)

- 문제 정의 우선: 본질(요구사항/수용 기준)과 실패 증상(로그/SQL/CLI 출력)을 먼저 기술한다.
- 제약 선행 확인: 휴리스틱 금지, 설치형 우선, Postgres-only, 실제 게이트웨이 사용 등 프로젝트 정책을 재확인한다.
- 전제조건 해결 먼저: 선행 조사/준비(예: 공급사 토크나이저 설치 가능성, 버전 고정, 컨테이너 의존성)를 완료한 뒤 구현에 착수한다.
- 구현은 그 다음: 준비 완료 이후 파이프라인 리팩터링·코드 변경을 수행한다. 변경은 증분(append‑only) 원칙을 따른다.
- 실행·검증은 마지막: 크론/CLI/E2E 검증을 수행하고 Evidence 문서에 로그·쿼리·버전을 기록한다.
- 체인 고정: 위 순서를 vooster 서브태스크 체인으로 표현하고, 모든 변경 전에 `vooster-ai__read_task` 재조회 후 체인 지속성을 확인한다.

### Document Classes (공식 문헌/증거/일반화 — MUST)

- [Generalized]: 프로젝트 간 재사용 가능한 원칙/절차/정책을 담은 문서. 고유 식별자나 환경 특수값을 포함하지 않는다.
- [OfficialEvidence]: 공급사/툴의 공식 문헌(문서 페이지, 매뉴얼, man 페이지, 릴리즈 노트, `--help` 출력+버전 표기)을 근거로 제시하는 증거 문서. 기능/플래그/호환성 같은 “정의적 주장”은 반드시 이 클래스를 포함한다.
- [RuntimeEvidence]: 특정 실행 환경 증거(타임스탬프, DSN, UUID, 실제 로그/SQL 결과)만을 담은 문서. 재사용 불가.
- 작성 규칙:
  - 정의적 주장(예: “uv sync는 --system을 지원하지 않는다”)은 [OfficialEvidence]에 공식 문헌 링크/원문 인용을 포함하고, 필요 시 [RuntimeEvidence]로 재현 로그를 보완한다.
  - 실행 결과·로그는 [RuntimeEvidence]로 `docs/logs/` 또는 태스크별 문서에, 절차·원칙은 [Generalized]로 `docs/guidelines/`에 기록한다.
- 상호 참조: [Generalized]는 구체 실행 예를 링크로만 참조하고, [OfficialEvidence]/[RuntimeEvidence]는 원칙을 변경하지 않는다.

### Tokenizer Pipeline Separation Rules (분류/검증/측정 — MUST)

- 분류(resolve — 인코딩 문자열만 결정):
  - 입력: 모델 식별자(게이트웨이 `/v1/models` 또는 `/v2/model/info`의 권위 데이터).
  - 순서: `tiktoken.encoding_for_model` → (옵션) 설치형 공급사 토크나이저/카운터가 제공하는 인코딩 이름 → 레지스트리(`tiktoken_model_map`) 조회.
  - 산출: 인코딩 문자열 또는 NULL.
  - 금지: 문자열 패턴 휴리스틱(예: LIKE, regex)·임의 기본값 반환.

- 검증(verify — 엔진 지원 여부만 확인):
  - 입력: 확정된 인코딩 문자열.
  - 방법: `pg_tiktoken safe_token_count(encoding, 'probe')`로 지원 여부를 Boolean으로 확인.
  - 금지: 인코딩 재추정·토큰 측정·임의 대체.

- 측정(count — 생산 경로):
  - 입력: 검증된 인코딩 + 텍스트.
  - 방법: `pg_tiktoken`만 사용하여 토큰 길이를 계산하고 DB에 기록.

#### Tokenizer Resolution Components (ID / Verify / Measure — 분리 규칙)
- Identification(ID): “어떤 토크나이저 인코딩을 써야 하는가”를 결정하는 단계. 권위 데이터(게이트웨이 `/v1/models`, `/v2/model/info` 원본, `tiktoken.encoding_for_model`)와 설치형 공급사 리졸버(있을 때만)를 사용한다. 문자열 패턴·휴리스틱 금지.
- Verification(Verify): 선택된 인코딩이 현재 엔진에서 지원되는지 확인하는 단계. `pg_tiktoken safe_token_count('<encoding>', 'probe')`로 Boolean 판정만 수행한다. 이 단계에서 길이 측정이나 대체 인코딩 추측을 하지 않는다.
- Measurement(Measure): 최종 확정된 인코딩으로 토큰 길이를 계산하는 단계. 오직 `pg_tiktoken`을 사용하며, 시스템/유저/페어 등 모든 카운트 경로를 일원화한다.
- 경계 고정: ID→Verify→Measure의 경계를 코드/SQL 함수로 명확히 분리하고, 각 단계 실패 시 즉시 중단(Fail‑fast)한다. “ID 실패 시 Verify/Measure로 넘겨서 추정” 같은 흐름은 허용하지 않는다.

### External ENUM Policy (외부 ENUM 비권위화 — MUST)
- 공급사/게이트웨이가 반환하는 `mode`/`enum`/상태 문자열은 **운영 판단에 사용하지 않는다**. 원문은 [RuntimeEvidence]로만 보존한다.
- 하드코딩 금지: `batch/chat/both/image_generation/bulk/response/unknown` 등 문자열에 근거한 분기/제외/집계는 금지한다.
- 사용 표현(문장 규칙): **NOT NULL 조건을 "사용"으로 서술**하고, NULL인 경우는 "미사용/준비 안 됨"으로 표기한다(“차단”이라는 단어 사용 지양).
- 사용 가능 여부는 오직 **토크나이저 검증 결과**로 판단한다. 검증 실패(NULL)일 때는 매핑/큐 투입을 하지 않는다(미사용).
- 엔드포인트 매핑 컬럼은 모드 값을 저장하지 않거나(NULL) 참고만 한다. 원본 모드 값은 `raw_metadata`에만 보존한다.
- 변경 내역/호환성은 Evidence 문서로 기록하며, 정책은 ENUM을 도입하지 않고 **권위 데이터+검증 경로**에만 의존한다.

#### UV System Install Policy (공식 근거 + Dockerfile 적용 — MUST)
- uv sync는 `--system`을 지원하지 않는다. uv pip는 `--system`을 지원한다. 이 주장은 [OfficialEvidence]로 증명해야 하며, 현재 근거는 `docs/logs/uv-official-evidence.md`에 저장한다.
- Dockerfile에서는 `uv pip install --system tiktoken`을 사용해 PL/Python에서 사용할 시스템 site‑packages로 설치한다.
- 버전 핀 지양: 사용자 지시에 따라 `tiktoken` 버전은 Dockerfile에서 핀 고정하지 않는다. 대신 컨테이너 런타임에서 실제 버전을 조회하여 [Evidence]로 기록하고(예: `importlib.metadata.version('tiktoken')`), 테스트는 “지원/비지원 동작”을 검증하도록 작성한다.
- 주장·변경 보고: uv/패키지/플래그에 관한 모든 주장은 먼저 실행해 보고([RuntimeEvidence]) 공식 문헌([OfficialEvidence]) 링크와 함께 요약한다(“해봤어? 하고 말해라” 원칙).
  - 금지: PL/Python/외부 API로 생산 카운트 수행.

- 함수 경계(권장): `resolve_tokenizer_encoding(model text) -> text`, `verify_tokenizer_encoding(encoding text) -> boolean`, `count_tokens(encoding text, text) -> integer`.
- 크론 게이트: 인코딩 미결정/미검증이면 큐 투입 금지; Evidence 문서에 사유 기록 후 재검증 트리거만 허용.

### Installable‑First Tokenizer Resolution (공급사 설치형 우선 — MUST)

- 공급사 카운터 조사/확보가 선행이다: Anthropic(Claude), Google(Gemini) 등 설치형 토크나이저/카운터 존재 여부와 호환성을 먼저 조사한다.
- 통합 순서(고정): `tiktoken.encoding_for_model` → 설치형 공급사 토크나이저/카운터(있을 때만) → `pg_tiktoken safe_token_count` → DB 레지스트리(`tiktoken_model_map`).
- 휴리스틱 금지: 문자열 패턴·추측 기반 인코딩 결정 금지. 권위 데이터와 설치형 라이브러리만 사용.
- 체인 표준화: 위 순서를 vooster 서브태스크 체인으로 고정하고, 선행 조사 체인 완료 후 리팩터링 체인을 시작한다.

### Sequential Thinking MCP Usage (연쇄 추론 도구 — MUST)

- 분류/검증/측정과 같이 단계적 의존성이 있는 작업은 Sequential Thinking MCP를 사용해 사고 사슬을 생성·검증한다.
- 작성 항목: 문제 정의, 제약, 대안, 증거, 실행 순서, 검증 방법을 명시하고 필요 시 분기/수정 기록을 남긴다.
- 적용 시점: 선행 조사 체인 착수, 파이프라인 리팩터링 시작 전/후, 검증 완료 시.

### Architecture Optimization Protocol (아키텍처 최적화 프로토콜 — MUST)

- 트리거: 아키텍처/성능 최적화 제안, 파이프라인 병렬화/분산화, pg_cron 스케줄링/샤딩, 락/동시성, 분할(청크) 정책 변경 등 “구조적 변경”을 제안하려 할 때.

- 필수 절차(반드시 순서 준수):
  1) 연쇄 추론 활성화: sequential-thinking MCP를 먼저 호출하여 문제 정의, 제약, 대안, 증거, 실행 순서, 검증 방법을 명시한다(Chain 기록 필수).
  2) 코드베이스 증거 수집: ripgrep 등으로 관련 함수/테이블/DDL/크론 스케줄을 식별하고, 파일 경로+라인을 근거로 정리한다(As‑Is 동작 파악).
  3) 외부 리서치(검색 의무): DuckDuckGo/SearXNG 등 도구로 PostgreSQL/pg_cron/동시성/락/분할 관련 모범사례를 조사하고, [OfficialEvidence]로 문헌 링크/인용을 포함한다(“검색 없이 주장 금지”).
  4) 종합(As‑Is → To‑Be): 현재 구조의 병목/위험을 코드 레벨로 명시하고, 제안(To‑Be)을 DDL/함수 시그니처/크론 잡/인덱스/샤딩 파라미터까지 구체화한다.
  5) 롤아웃/롤백 계획: 점진 적용(플래그/샤드 수/주기), 모니터링 지표(처리량/지연/락 대기), 실패 시 롤백 절차를 포함한다.
  6) 검증 계획: 쿼리/로그/측정 방법을 제시하고, [RuntimeEvidence]로 실행 결과를 남긴다. 비가동 환경이면 정적 근거+시뮬레이션 방법을 제시.

- 산출물 형식:
  - docs/architecture/<topic>-as-is-to-be.md 생성/갱신(As‑Is/To‑Be를 코드 레벨로; 함수/DDL/스케줄 예시 포함).
  - PR/코멘트에 sequential-thinking 호출 기록(타임스탬프)과 [OfficialEvidence]/[RuntimeEvidence] 링크 첨부.

- 금지/유의:
  - “검색 없이” 또는 “근거 없이” 아키텍처/성능 주장을 제안하지 않는다(위반 시 elimination log에 사유 기록).
  - 단일 세션 순차 실행으로 병렬성을 가정하지 않는다. 병렬화는 pg_cron 다중 잡+FOR UPDATE SKIP LOCKED+샤딩 파라미터로 설계한다.
  - 타임아웃을 분할 기준으로 사용하지 않는다(공정성 timebox는 허용). 분할은 공급자 한도(토큰/바이트) 또는 명시 정책으로만.

- 적용 범위:
  - PostgreSQL/pg_cron 디스패처/워커/샤딩, 큐 테이블, 인덱스/락, 분할(청크) 정책, 토큰 카운팅, LLM 게이트웨이 배치 제출 경로 전반.

본 프로토콜을 따르지 않은 최적화 제안은 채택하지 않는다.

### Try-First, Report-After (실행 후 보고 — MUST)

- 원칙: "해봤어? 하고 말해라" — 성공/완료/적용 주장은 실제 실행/검증 이후에만 한다.
- 증거 요구:
  - 정의적 주장에는 [OfficialEvidence]를 반드시 포함(공식 문헌/`--help`+버전 표기 등).
  - 재현/적용 결과는 [RuntimeEvidence]로 보완(명령어, 로그/SQL 출력, 타임스탬프, 버전).
- 환경 확인: 컨테이너/DB/PL/Python/크론 등 변경 후에는 해당 환경 내부에서 직접 확인한다(예: `docker exec`로 라이브러리 버전 확인, `psql`로 함수 호출 결과 확인).
- 불가 사유: 실행 불가 시 즉시 사유(권한/네트워크/자격증명 부족 등)와 대체 검증(정적 분석/문서 근거)을 명시한다.
- 진술 형식: 검증 전에는 가정으로, 검증 후에는 "Verified:" 접두어로 구분된 진술을 사용한다.
- 분리 준수: [Generalized]에는 절차/원칙만, [OfficialEvidence]/[RuntimeEvidence]에는 근거/결과만 기록한다(상호 링크 가능).

### claude-context Indexing Defaults (ignorePatterns — MUST)

목적: claude-context MCP 인덱싱 시 대용량/산출물/가상환경 등 불필요 경로를 기본적으로 제외하여 성능과 관련성 확보.

적용 규칙
- 다음 기본 제외 목록을 인덱싱 시 항상 적용한다. 호출자가 별도의 `ignorePatterns`를 명시하는 경우, 그 목록이 우선한다(명시가 없으면 본 기본값을 사용한다).
- splitter는 기본 `ast`를 사용한다. 대용량 디렉토리 또는 AST 파싱 타임아웃 발생 시 `langchain`으로 전환한다.

기본 제외 목록 (프로젝트 표준)
- `.venv/**`, `venv/**`
- `node_modules/**`, `.git/**`
- `build/**`, `dist/**`
- `**/__pycache__/**`, `*.pyc`
- `.pytest_cache/**`, `.coverage`, `htmlcov/**`
- `fixtures/**`, `batches/**`, `tmp_test/**`, `tests/tmp/**`
- `*.db`, `*.sqlite`, `*.sqlite3`
- `docker/postgres/pgdata/**`

호출 예시
```bash
mcp__claude-context__index_codebase(
    path="<ABS_PROJECT_ROOT>",
    splitter="ast",
    force=false,
    ignorePatterns=[
        ".venv/**", "venv/**", "node_modules/**", ".git/**",
        "build/**", "dist/**", "**/__pycache__/**", "*.pyc",
        ".pytest_cache/**", ".coverage", "htmlcov/**",
        "fixtures/**", "batches/**", "tmp_test/**", "tests/tmp/**",
        "*.db", "*.sqlite", "*.sqlite3",
        "docker/postgres/pgdata/**"
    ]
)
```

재인덱싱/정체 대응 절차
1) 진행률 10분 이상 정체 시 현재 인덱스를 제거한다: `mcp__claude-context__clear_index(path=project_root)`
2) 동일 제외 목록을 적용하여 재인덱싱한다. 필요 시 `splitter="langchain"`, `force=true`로 전환한다.
3) 인덱싱 완료 후 검색을 재시도한다: `mcp__claude-context__search_code(path=project_root, query=...)`

출처(프로젝트 문서)
- `docs/A2Z-Operational-Guidelines.md`:118, 232, 286, 310
- `docs/task-audit-procedure.md`:251

### Task and Subtask Identifier Protocol (MANDATORY)

- `taskId` 입력은 항상 `T-123` 형식의 3자리 숫자 코드만 허용한다. `vooster-ai__read_task`에 `T-123-001`을 전달하면 즉시 `Invalid task ID format` 오류가 발생한다.
- Sub-task 식별자는 `subTaskUid` 필드에 `T-123-001` 형식으로 저장된다. Sub-task 작업 시 `taskId="T-123"`와 `subTaskUid="T-123-001"`을 동시에 전달한다.
- Sub-task 체인(의존성) 점검 절차:
  1. `vooster-ai__read_task(taskId="T-123")` 호출 후 `subTasks` 배열에서 대상 `subTaskUid`와 `dependencySubTaskIds` 체인을 모두 수집한다.
  2. `docs/batch-preparation-automation-architecture.md` 등 아키텍처 문서를 확인하여 요구되는 실행 순서를 확정한다 (`T-378-002` → `T-378-003` 순차 체인 등).
  3. 확정된 순서를 기반으로 `vooster-ai__update_sub_task`를 호출하고 `dependencySubTaskIds` 체인에 정확한 `subTaskUid` 목록을 전달한다.
  4. 업데이트 직후 동일한 `read_task` 호출로 체인 배열이 기대대로 정렬되었는지 재검증한다.
- Sub-task 세부 정보 조회 시에는 반드시 `vooster-ai__read_task` 호출에 parent `taskId`와 `subTaskUid`를 함께 전달한다. 예시:
  ```bash
  mcp__vooster-ai__read_task(
      projectRoot="/abs/path",
      projectUid="ABCD",
      taskId="T-378",
      subTaskUid="T-378-097"
  )
  ```
  위 호출은 해당 subtask의 Acceptance Criteria, 상태, 체인(의존성)을 즉시 반환한다. 작업 노트나 elimination log에 이 출력 일부를 인용해 두어야 다른 에이전트가 근거를 추적할 수 있다.
- 체인(의존성) 추가나 변경 시 단일 호출로 모든 선행 항목을 명시한다. 일부만 전달하면 나머지가 제거되므로 매 호출마다 전체 체인 목록을 포함한다.
- 아키텍처 문서와 실제 체인이 불일치할 경우, 차이를 기록한 뒤 `update_task_completion_log` 또는 별도 조사 태스크 생성으로 증분 보고한다; 기존 DONE 상태를 직접 되돌리지 않는다.

### Task/Sub-task Status Management Protocol (MANDATORY)

- Status 변경 도구 구분:
  - 코드 탐색/증거 수집은 `claude-context`로 수행한다. 상태 변경은 절대 `claude-context`로 하지 않는다.
  - 상태 읽기/변경은 모두 `vooster-ai`로 수행한다: 읽기(`read_task`), 서브태스크 상태 변경(`update_subtask_status`), 태스크 상태 변경(`update_task_status`).
- 변경 전 재확인(필수): 상태 변경 직전 `vooster-ai__read_task(taskId="T-XXX")`로 최신 상태를 재조회한다.
- 착수 전 상태 전환(필수): `status='BACKLOG'`(또는 DONE/ARCHIVED 이후 재작업) 항목에 착수하려면 먼저 `update_subtask_status(..., status="IN_PROGRESS")` 또는 `update_task_status(..., status="IN_PROGRESS")` 호출이 성공한 뒤에만 코드/문서/테스트 작업을 시작한다. 상태 전환과 동시에 vooster 코멘트/elim log에 착수 시각과 범위를 기록한다. 작업을 시작한 뒤에야 백로그 상태였음을 발견했다면 즉시 멈추고 상태 변경 + 사유 기록을 선행하며, 다른 에이전트가 이를 발견한 경우에는 상태 전환을 요청하고 불일치 근거를 남긴 뒤 Stale 프로토콜에 따라 재조정한다.
- DONE 판정 기준:
  - Sub-task: Acceptance Criteria 전부 충족을 코드/문서 증거로 확인 후 `update_subtask_status(status='DONE')` 실행.
  - Task: 모든 관련 sub-task가 DONE이거나, acceptance 기준이 태스크 레벨에서 직접 충족된 경우 `update_task_status(status='DONE')` 실행. 이때 `completionDetails`/`confidenceLevel`/`confidenceDetails` 3항목을 반드시 포함한다.
- 장시간 IN_PROGRESS 교착 해소:
  1) `read_task`로 현재 상태/수행 증거 확인 → 2) 수용 기준 충족 시 즉시 DONE 처리 → 3) 미충족 항목이 있으면 해당 sub-task에 `aiPrompt`/`acceptanceCriteria` 보강 후 IN_PROGRESS 유지 → 4) 필요 시 조사/보강용 follow-up 태스크 생성(`add_task`).
- 예시:
  - `vooster-ai__update_subtask_status({ projectRoot: '<ABS_PROJECT_ROOT>', projectUid: '<PROJECT_UID>', taskId: 'T-XXX', subTaskUid: 'T-XXX-YYY', status: 'DONE' })`
  - `vooster-ai__update_task_status({ status: 'DONE', completionDetails: '...', confidenceLevel: 8, confidenceDetails: '...' })`

### Stale IN_PROGRESS Remediation Protocol (MANDATORY)

- **Detection window**: Treat a task or sub-task as stale when `status='IN_PROGRESS'` and (a) `inProgressAt` or the latest `vooster` comment is older than 2 hours, or (b) the owning agent has not updated acceptance evidence across the last two check-ins (≈60–90 minutes). Long-running jobs that deliberately span several hours must document expected duration in the elimination log; otherwise they are considered stale.
- **Evidence capture**: Before any action, re-run `vooster-ai__read_task` (and `vooster-ai__read_task` with `subTaskUid` for subtasks) to capture timestamps, dependencies, and last modified details. Copy the relevant excerpt into your working notes or elimination log so other agents can audit why the stale flag was raised.
- **Ping-and-wait protocol**: Leave a vooster comment tagging the stale item with the current time, summary of observed blockers, and a request for status. Allow at least two refresh cycles (≈30–45 minutes) for the original agent to respond, and be prepared to extend the window up to 2 hours when the effort was previously declared long-running. Shorter waits are only permitted for production incidents requiring immediate intervention.
- **Takeover decision gate**: Once the wait window expires, re-run `read_task` to capture any late updates, then evaluate whether acceptance criteria and partial deliverables give you enough context to continue. If yes, proceed to takeover; if critical information is still missing, open a follow-up investigation subtask (or escalate via human review) before touching the implementation so work does not diverge.
- **Takeover procedure**: If no response arrives within the wait window, declare takeover intent in vooster (comment + elimination log), noting the detection evidence and planned next steps. Do **not** revert the item to BACKLOG; continue from the recorded acceptance criteria and preserve any partial work.
- **Chain hygiene**: When stale work blocks downstream tasks, map the chain graph via `read_task` outputs before altering anything. Any adjustments to `dependencySubTaskIds` must (1) restate the entire chain list in the `update_sub_task` call, (2) reference the stale evidence in the comment, and (3) avoid removing in-progress predecessors unless a new follow-up task captures unfinished scope.
- **Escalation and follow-up**: If takeover reveals missing context, open an investigation subtask or follow-up task documenting the gap instead of silently patching around it. Record all remedial actions (tests run, blockers cleared, chain rewires) in `docs/T-378-implementation-summary.md` or the task-specific log so subsequent agents inherit the state.

Generalizable Examples (Directive → Cascade — Templates)

1) Generic Task Update
- Directive: "T-<ID>를 업데이트하라" / "Update T-<ID>"
- Actions:
  1. Read `T-<ID>` and list subtasks
  2. Set task to IN_PROGRESS if BACKLOG and changes are intended
  3. Update existing subtasks (title, acceptanceCriteria, aiPrompt, chains/`dependencySubTaskIds`)
  4. Add missing subtasks when implied; keep changes additive
  5. Maintain chain order (prep → move → refs → push)

2) Docs Consolidation
- Directive: "루트 문서를 docs/로 정리"
- Subtask Template: "Commit N: Consolidate root docs into docs/ (archive duplicates)"
- Acceptance Template:
  - Root docs moved to `docs/`; duplicates to `docs/archive/`
  - Exceptions preserved; no bulk deletions
  - References updated; `rg` shows zero stale paths

3) Agent-Specific Docs Reorg
- Directive: "CLAUDE_* 문서를 전용 폴더로 이동"
- Subtask Template: "Commit N: Reorganize CLAUDE_* under docs/agents/<agent>/"
- Acceptance Template:
  - `AGENT_*.md` moved to `docs/agents/<agent>/`; backups to `docs/archive/agents/<agent>/`
  - Entry doc (e.g., `CLAUDE.md`) remains at root
  - References updated; zero stale paths

4) Data/Artifacts Relocation
- Directive: "결과물/배포물을 폴더로 집약"
- Subtask Templates:
  - "Commit N: Move data exports to fixtures/exports/"
  - "Commit N: Move tool/package artifacts to package/"
- Acceptance Template:
  - Items moved to target folders; exceptions preserved
  - Update references; zero stale paths

5) References Update
- Directive: "이동 후 경로 참조 업데이트"
- Subtask Template: "Commit N: Update references/links to moved files"
- Acceptance Template: All moved items’ links/imports updated across README/docs/scripts; ripgrep clean

6) Status/Completion Log Update (DONE tasks)
- Directive: "T-<ID>를 DONE 처리하라" or "완료 로그 업데이트"
- Actions:
  - Verify acceptance criteria fully met
  - For status → DONE: provide `completionDetails`, `confidenceLevel`, `confidenceDetails`
  - For already DONE: use `update_task_completion_log` to append audit findings; do not change status

7) Conflict → Investigation Task
- Directive: "현재 상태와 내 분석이 충돌"
- Actions:
  - Document conflict; create investigation task with evidence
  - Avoid overwriting existing DONE/IN_PROGRESS; proceed via additive resolution

```

#### ✅ Pattern 2: Preserve and Augment

```bash
# Keep existing completionDetails, add your verification
# Keep existing implementation, add your improvements
# Keep existing analysis, add your insights
```

#### ✅ Pattern 3: Conflict as New Task

```bash
# When findings conflict, don't force your view
# Create investigation task for resolution
# Document both perspectives with evidence
```

#### Scenario Response Table

| My Plan | Current State | Correct Action |
|---------|---------------|----------------|
| BACKLOG→WONT | DONE by Agent B | Update completion log with audit results (Pattern A) |
| BACKLOG→IN_PROGRESS | IN_PROGRESS by Agent B | Check subtask assignments, coordinate work split |
| Implementation X | Implementation Y exists | Create evaluation task comparing X vs Y |
| Add feature A | Feature A exists | Enhance existing feature A with improvements |
| Delete old code | Old code refactored | Review refactored version, verify quality |

#### Vooster Intent Declaration

### Preventive Implementation Rules (MANDATORY)

- **Design for Prevention, not Reactive Warnings**: When a feature depends on automation (e.g., pg_cron metadata refresh, seed jobs, migrations), integrate the trigger or bootstrap step directly into the workflow. Warning banners or manual follow-ups are acceptable only as temporary safety nets—the task is not complete until the code prevents the risky state from occurring.
- **Deletion Requires Replacement Evidence**: Before removing or disabling code, search for and document the replacement implementation (helpers, cron jobs, migrations). Only delete after confirming the substitute is in place; if no replacement exists, stop and open a follow-up task rather than deleting the code.

### System Token Application Automation (T-378-097 MANDATORY)

- `prompts pair-dataset` MUST remain non-blocking. Inline calls to `apply_system_prompt_tokens_to_jobs` or any synchronous system-token computation inside the pairing transaction are forbidden.
- Agents must ensure the system-token step is executed by pg_cron (or an equivalent queued worker) that processes pending `(system_uuid, dataset_uuid)` pairs after pairing completes. If no job exists, create one before shipping code and document the schedule.
- All migrations, SQL helpers, and CLI updates must respect the asynchronous flow: pairing enqueues work and returns within seconds, while cron populates `system_prompt_token_counts` / `user_prompt_token_jobs.system_token_count`.
- Tests and docs must reflect the non-blocking behaviour. When verifying regressions, capture evidence that pairing exits quickly and the cron job fills token counts without manual intervention.
- When refactoring legacy code, preserve or enhance the asynchronous design and reference **T-378-097** in vooster comments or completion logs to show compliance.

Before modifying any task, agents SHOULD declare intent in vooster:
```bash
# Optional but recommended for high-conflict-risk tasks
mcp__vooster-ai__add_task(
    summary="Intent: Audit T-XXX for A2Z compliance",
    aiPrompt="
    ## Scope
    Will review T-XXX and potentially update status/details

    ## Timeline
    Starting: [timestamp]
    Expected completion: [timestamp + 30min]

    ## Coordination
    If another agent is working on T-XXX, coordinate via this task
    "
)
```

#### Verification Checklist (Before ANY Task Modification)

- [ ] Read current task state via `read_task`
- [ ] Compare current state with my analysis state
- [ ] Identify what changed since analysis started
- [ ] Determine if changes conflict with my plan
- [ ] If no conflicts: proceed with incremental enhancement
- [ ] If conflicts exist: create investigation/resolution task
- [ ] Document all decisions in vooster logs

#### Integration with Existing Protocols

- Works with: Multi-Agent Task Status Verification
- Complements: NO REGRESSION POLICY (prevents weakening of quality)
- Requires: vooster-ai as coordination mechanism
- Enforces: Additive-Only principle for task management

### NO REGRESSION POLICY (비후퇴 정책 - CODE QUALITY STANDARDS)

**Definition**: Once code quality standards are established, CODE IMPLEMENTATIONS must not weaken, reduce, or eliminate existing quality levels. **This policy governs code quality, NOT document editing.** AGENTS.md can and should be updated to improve clarity, fix errors, or adapt to new requirements.

**What This Policy PROTECTS (Code Quality)**:
- ❌ Reducing reasoning effort in actual work (HIGH → MEDIUM/LOW)
- ❌ Skipping cross-agent verification when required
- ❌ Writing code with fewer SequentialThinking steps (< 16 when needed)
- ❌ Bypassing pre-commit hooks or quality gates
- ❌ Rushing through work that requires thoroughness
- ❌ Skipping vooster task management for complex work
- ❌ Reducing autonomous operation capabilities
- ❌ Weakening peer review when implemented

### Tokenizer–Model Mapping (하드코딩 금지 - CRITICAL)

- 원칙: 모델 이름과 tokenizer(인코딩) 간 매핑을 코드/스크립트/시드 데이터로 하드코딩하지 않는다. 새 모델 출시 시 코드 변경 없이 운영 가능해야 한다.
- 구현 규칙:
  - 매핑은 DB 테이블로만 관리한다(예: `tiktoken_model_map(base_model, encoding)`).
  - 매핑 조회는 DB 함수/SQL로 수행한다(예: `infer_tiktoken_encoding(p_base_model)`), 부재 시 NULL 반환 및 작업 중단. 기본값/휴리스틱 금지.
  - 게이트웨이 메타데이터(`litellm_model_metadata.litellm_params`)의 `model`은 정규화된 모델명(프로바이더 접두어 제거), `base_model`은 tokenizer 추론용 키로 사용한다.
  - 프로바이더 접두어(예: `azure/`)는 tokenizer 추론 시 제거하여 표준 키로 사용한다.
- 금지 항목:
  - 코드 내 모델→tokenizer if/else/switch 작성
  - 초기화 단계에서 고정 seed 매핑 삽입
  - 매핑 부재 시 임의 기본값 반환
  - `mode='both'`를 임의 변환(예: `batch`)하는 휴리스틱
- 운영 절차(새 모델 등장 시):
  1) pg_cron 모델 동기화로 `litellm_model_metadata`/`llm_endpoint_models`를 최신화
  2) 로그/리포트로 `base_model` 매핑 부재 확인
  3) DBA/운영자가 `INSERT INTO tiktoken_model_map(base_model, encoding) VALUES(...)`로 명시 추가
  4) 변경/롤백은 DB 차원에서 수행, 코드 수정 금지
- 검증:
  - 매핑 부재 시 작업은 명확한 에러 메시지와 함께 실패해야 한다.
  - 모든 tokenizer 계산은 `pg_tiktoken`만 사용(Python `tiktoken` 금지).
- 정규화(접두어 제거)는 DB 함수/SQL로 일관 적용.
 - **Tokenizer Resolution Workflow (INSTALLABLE-FIRST)**:
   1. 공급사 토큰 카운터 설치 가능성 조사 태스크를 선행 생성∙완료한다(예: "Research-Installable-Tokenizers").
   2. Anthropic·Google 등 설치형 토크나이저/카운터를 확보(또는 부재 보고)한 이후에만 PL/Python/SQL 리팩터링 태스크를 진행한다.
   3. 리팩터링 시 순서를 `tiktoken.encoding_for_model → 설치형 공급사 토큰 카운터 → pg_tiktoken safe_token_count → tiktoken_model_map`으로 고정하며, 문자열 패턴 휴리스틱을 추가하지 않는다.
   4. 파이프라인 변경 후 pg_cron 메타데이터 동기화를 실행하고 결과를 docs/로그에 기록한다.
   5. 위 절차를 프로젝트의 task/subtask로 명시하고, 완료 후 본 규칙 준수 여부를 검증한다.

### Reasoning Framework (일반화된 사고 방식)

문제 해결은 “역순 사고(전제조건→구현→검증)”의 일반 원칙을 따른다. 특정 도메인(토크나이저 등)에 한정되지 않고 다음 단계로 추론한다.

- 문제 정의: 문제의 본질과 수용 기준을 먼저 명시한다(필드, 데이터 출처, 기대 결과, 실패 기준).
- 제약 확인: 정책·환경 제약(휴리스틱 금지, 설치형 우선, Postgres-only, 실제 게이트웨이)을 재확인한다.
- 전제조건 충족: 해결에 필요한 선행 조건을 태스크/서브태스크로 분해해 먼저 완료한다(예: 설치형 컴포넌트 조사·준비, 버전 고정, 컨테이너 준비).
- 결정 사다리(권위→설치형→내부 프로브→레지스트리):
  - 1) 권위 데이터(원본 메타/문서/표준)로 정규화
  - 2) 설치형/로컬 컴포넌트로 1차 판정
  - 3) 내부 프로브(엔진/확장)로 2차 확인
  - 4) 레지스트리/맵(승인된 자동화)로 보완
  - 각 단계는 성공 시 다음 단계 생략, 실패 시 다음 단계로 이동하며 휴리스틱·기본값은 금지한다.
- 게이트·Fail-fast: 확정 불가하면 즉시 중단(NULL/명확 예외)하고, 큐 투입·후속 실행을 막는다.
- 증거·재현성: 원본 입력, 정규화 결과, 판정 근거, 오류 사유를 로그/문서에 기록하고 패키지·이미지·마이그레이션 버전을 고정한다.
- 체인 관리: 모든 변경을 vooster task/subtask로 선언하고 의존(Chain)을 명시·검증한다. 병행 작업 시 재조회·조정.
- 재검증 트리거: 권위 데이터·설치형 컴포넌트·프로브가 업데이트되면 동일 사다리로 자동 재검증한다.
- 안티패턴: 문자열/패턴 추측, 임의 기본값, 비공식 출처 의존, 체인 미기록, 증거 누락.

### Database‑Only Processing Policy (MANDATORY)
- 원칙: 데이터베이스를 사용하는 소프트웨어는 어떤 형태로든 임시 파일을 생성하지 않고, 모든 전처리/정규화/필드 추론/헤더 처리/토큰 카운트 등을 데이터베이스 또는 스트림 처리로 수행한다.
- 적용:
  - 헤더 제거/감지, 열 역할 분류(키/프롬프트/메타), 정규화는 LLM 게이트웨이·PL/Python·SQL 함수로 처리한다. 파일을 잘라내거나 재작성하는 임시 파일 금지.
  - 토큰 카운트는 `pg_tiktoken`만 사용한다. 중간 결과도 테이블/뷰에 기록한다.
  - Fingerprint/Row Count 계산은 DB/스트림 상에서 수행하고, 재사용/중복 판단도 DB 기준으로 한다.
- 금지: `NamedTemporaryFile`/임시 디스크 파일 생성, 파일 기반 헤더 슬라이싱, 로컬 캐시 파일.
- 근거: `docs/A2Z-Operational-Guidelines.md`의 메모리/DB‑우선 원칙 및 재현성/운영 안정성 강화.

### CLI UX Minimization (FLAGS 줄이기 — MUST)
- 원칙: 자동 평가 가능한 항목은 모두 자동화하고, 사람 플래그는 최소화한다.
- 적용:
  - `--format`/`--has-header` 등 입력 형식/헤더 여부 플래그는 선택적/Deprecated로 취급하며, 판정은 MIME(libmagic)과 LLM(skip rows)만 사용한다.
  - 사용자 주장은 로그에만 기록하고, 실행 판단은 권위 데이터(MIME)와 LLM 결과에만 근거한다.
  - 규칙/휴리스틱(확장자 기반 추정, csv.Sniffer 등)은 금지한다. 불명확하면 Fail‑fast로 중단하고 Evidence를 남긴다.
- 최소 필수 인자: `--file`, `--name`, `--user-dsn`. 그 외는 자동화/추천 경로 사용.
- 복잡도·장애 저감: DB‑전용 처리와 Fail‑fast 게이트로 운영 리스크를 줄이고, 사람 플래그에 의존하지 않는다.

### Environment‑Agnostic Setup (컨테이너 비의존 — MUST)
- 원칙: 라이브러리는 Docker 전용이 아니다. 의존 설치·환경 준비는 호스트/CI 환경에서 수행하며, 코드/정책은 컨테이너에 종속되지 않는다.
- 적용:
  - MIME 감지는 `python‑magic/libmagic` 권장. 미구성 시 Fail‑fast로 중단하고 안내 메시지로 설치 지침을 제공한다.
  - Dockerfile 변경은 요구 사항이 명시된 프로젝트에 한해 적용하며, 기본 정책은 컨테이너 비의존이다.
- 설치 예: `uv pip install python-magic`(호스트), OS별 libmagic 설치(Brew/Apt/Yum 등). 네트워크/권한 제약 시 Fail‑fast 후 Evidence 기록.

### DB‑First Architecture (Python RPC 리모컨 — XEN 원칙, MUST)
- 원칙: 모든 핵심 기능은 PostgreSQL에 이관한다. Python은 **리모컨 수준**으로만 남겨 두고, 생산 로직은 DB(확장/함수/크론)에서 수행한다.
- 적용:
  - 토큰 카운트: `pg_tiktoken`만 사용(PL/Python 금지), 결과는 테이블/뷰에 기록.
  - 발송/제약/분할: DB 함수/크론이 요청을 제약에 맞게 잘라서 나누어 보내고, 도착 여부를 실시간으로 확인하며 단위별로 재삽입한다.
  - 상태/모니터링: 진행 현황/메트릭은 DB가 산출하고, Python CLI는 조회/표시에 한정한다.
  - 스키마/필드 추론: 비동기 배치(pg_cron)로 처리하고 결과를 메타/로그 테이블에 저장. 동기 경로는 DB 결과가 준비되었을 때만 수행.
- 금지:
  - Python에서 비즈니스 로직/휴리스틱/캐시/임시파일 구현(중복 로직 금지).
  - DB 기능을 대체하는 Python 측 추측/재연산.
 - XEN(절제) 원칙:
  - Python CLI/도구는 **최소 인자 + 원격 호출(Remote control)만** 제공한다. 자체 **자동 트리거/리포트 기능은 제공하지 않는다.**
  - 새로운 기능이 필요하면 **먼저 DB 함수/크론**으로 정의하고, Python은 그 함수를 **명시적 사용자 명령에 따라 호출**하는 얇은 레이어만 추가한다.
  - 운영 성능/신뢰성 요구는 DB 설계/인덱스/제약/크론으로 해결하고, Evidence 저장·상태 전이는 **DB에서만** 수행한다.

### Timeout Policy (연결 타임아웃 vs 동작 타임아웃 — MUST)
- 원칙: **연결 타임아웃만 허용**, **동작(대기/처리) 타임아웃 금지**. 운영 로직에서 “얼마나 오래 걸렸는지”를 이유로 임의 실패시키지 않는다.
- 적용:
  - CLI/크론/워커에서 상태 대기(wait)는 기본적으로 **무제한 대기** 또는 **사용자 중단(Ctrl+C)** 모드로 제공한다. 진행 상황을 주기적으로 출력하되, 시간 경과만으로 에러를 발생시키지 않는다.
  - 연결/네트워크 레벨(소켓/HTTP/DB) 타임아웃은 허용하며, 재시도(backoff)·실패 보고(Evidence) 규칙을 따른다.
  - 자동화/CI에서 시간 제한이 필요한 경우에만 **명시적 설정**으로 허용하고, 기본값은 무제한 대기다. 설정 시에도 실패는 “대기 중단”으로 보고하고, 작업 자체는 보류 상태로 남긴다.
  - 기존 `--timeout`과 같은 **동작 타임아웃 플래그는 Deprecated**로 표기하고, 문서에 비권장 사유(운영 불편·신뢰성 저하)를 명시한다.
- 검증:
  - 대기 명령은 시간 경과로 실패하지 않고, 연결 타임아웃만으로 중단된다.
- Evidence에는 연결 타임아웃/재시도 로그만 기록되며, 단순 대기 시간 경과로 인한 실패는 기록하지 않는다.

### Timeout Terminology Standardization (용어 표준화 — MUST)
- ConnectionTimeout: 네트워크/소켓/DB 연결 단계에서의 제한(DNS, TLS, handshake). 허용·로그·재시도 대상.
- RequestTimeout: HTTP 요청 수준 제한(client‑side). 허용·로그·재시도 대상.
- ResponseDeadline: 서버 측 TTL/만료 정책(게이트웨이/크론). 허용·로그.
- OperationWait: 상태 폴링/대기. “타임아웃”으로 간주하지 않으며, 시간 경과만으로 실패 처리하지 않는다.
- 로깅 스키마(권장): kind=CONNECT_TIMEOUT|REQUEST_TIMEOUT|RESPONSE_DEADLINE|OPERATION_WAIT, duration, attempt, endpoint, dataset_uuid, job_uuid.

### Python→pg_cron 오프로딩 정책 (MUST)
- 원칙: Python에서 “무언가 조작”하는 모든 기능은 가능한 즉시 DB(함수/트리거/pg_cron)로 이관한다. Python은 **원격 호출(Remote control)**만 수행한다.
- 적용 대상(예시):
  - 데이터 전처리/정규화/해싱/청크 분할/토큰 잡 큐잉/드레인/재시도/백프레셔
  - 스키마/필드 추론(샘플 생성→LLM 호출→메타/로그 저장)
  - 진행률/메트릭 집계(뷰/함수로 노출)
- 마이그레이션 절차:
  1) DB 함수로 핵심 로직 정의(입력/출력/제약/에러 처리 분명히)  
  2) pg_cron 스케줄 설정(간격/동시성/p_limit/SKIP LOCKED/재시도/레이트리밋)  
  3) 권한/OWNERSHIP/GRANT 정비(사용자/관리자 역할 분리)  
  4) Evidence는 DB 테이블/로그로 기록(Python 파일 로그 금지)
- CLI 최소화:
  - 환경설정 전달, 데이터 삽입(COPY/STDIN), 상태 조회(SELECT)만 제공한다. 자동 트리거/리포트는 제공하지 않는다.
  - 신규 기능이 필요하면 먼저 DB 함수/크론을 배치하고, Python은 **명시적 사용자 명령으로 해당 함수를 호출**한다.
- 성능 가이드(대규모 처리):
  - 입력은 `COPY ... FROM STDIN`으로만 처리(루프/execute_values 금지)  
  - 스테이징은 UNLOGGED/임시 테이블, 일괄 정규화→업서트는 단일 SQL로 수행  
  - 토큰 카운트는 `pg_tiktoken`만 사용, 카운트 결과·메트릭은 DB에 저장  
  - SKIP LOCKED+p_limit+레이트리밋+백프레셔로 병렬/안정성 제어
- 금지:
  - Python 루프 기반 대량 삽입/파싱/토큰 측정
  - Python 임시파일/휴리스틱/캐시/자동 스케줄링
  - 동작(대기) 타임아웃으로 실패 처리

  ### Docker/Compose 볼륨·DSN 주의사항 (MUST)

  - 동일 프로젝트 이름 사용(-p):
    - `docker compose`는 프로젝트 이름에 따라 볼륨명을 다르게 만듭니다. 과거와 다른 프로젝트 이름/경로로 실행하면 `down -v`가 다른 볼륨만 지우고, 예전 데이터가 남아 “이미 2번째 엔드포인트가 있음” 같은 증상이 발생합니다.
    - 실행 원칙: 항상 동일한 `-p <project>` 값을 사용하여 `down -v`/`build`/`up`을 수행하세요.
      - 예: `docker compose -f docker/postgres/docker-compose.yml -p <project> down -v --remove-orphans`
      - 예: `docker compose -f docker/postgres/docker-compose.yml -p <project> build --no-cache`
      - 예: `docker compose -f docker/postgres/docker-compose.yml -p <project> up -d`

  - DSN 일치 확인(필수):
    - `.env`의 `POSTGRES_USER_DSN`이 현재 컨테이너(기본 포트 `POSTGRES_HOST_PORT`=55433)와 정확히 일치해야 합니다.
    - 빠른 점검(예시):
      - `psql "$POSTGRES_USER_DSN" -c "SELECT current_database(), inet_server_addr(), inet_server_port();"`
      - `psql "$POSTGRES_USER_DSN" -c "SELECT COUNT(*) FROM llm_endpoints;"` (깨끗한 초기 상태라면 0)

  - 이미지 빌드와 데이터:
    - `build --no-cache`는 이미지만 새로 빌드합니다. 데이터 초기화가 필요하면 `down -v`로 볼륨을 지워야 하며, 볼륨명이 다른 경우(프로젝트명 상이) 데이터가 남습니다.

  - 엔드포인트 등록 상식:
    - 이 레포의 init/cron은 엔드포인트를 자동 생성하지 않습니다. 엔드포인트는 CLI/헬퍼를 통해 명시적으로 등록됩니다.
    - “두 번째 엔드포인트” 메시지는 대개 잔존 데이터(볼륨) 또는 잘못된 DSN으로 과거 DB에 붙었을 때 발생합니다. 위의 `-p` 고정, DSN 재확인, `llm_endpoints` 카운트 점검으로 원인을 먼저 배제하세요.

  - 운영 단계 체크리스트:
    1) 동일 프로젝트 이름으로 `down -v` 수행(불필요 볼륨은 `docker volume rm <name>`로 정리)
    2) `build --no-cache` → `up -d`
    3) DSN이 현재 컨테이너를 가리키는지 psql로 확인
    4) 초기화/마이그레이션 후 `llm_endpoints`/`com_config`/크론 잡 존재 여부를 점검

  ### MIME‑First Input Handling (MANDATORY)
- 원칙: 입력 파일 유형은 확장자나 수동 `--format` 옵션이 아니라 **MIME 타입**으로 판정한다. 사람이 포맷을 지정하지 않아도 에이전트가 스스로 판정·처리한다.
- 구현 규칙:
  - 권위 판정: OS/libmagic 기반 MIME 판정(예: `text/plain`, `text/csv`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `application/xml`)을 사용한다.
  - 텍스트 계열: `text/*`는 “텍스트 스트림”으로 동일 취급하며, 구분자/열 역할/헤더 존재는 LLM 기반 스키마·헤더 감지로 결정한다(휴리스틱 금지).
  - 스프레드시트 계열: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`(XLSX), `application/xml` 스프레드시트 등은 스트림 파싱 또는 DB 내 변환(임시파일 금지)으로 텍스트화한다. 미지원이면 Fail‑fast.
  - 헤더 처리: 헤더 존재 여부와 줄 수는 LLM이 반환한 정수값으로만 결정한다. 결과가 없거나 게이트웨이 자격이 없으면 즉시 실패(Fail‑fast)한다.
  - 포맷 옵션: `--format`은 선택사항이며, 제공되어도 MIME/LLM 판정과 충돌 시 판정 결과를 우선한다. 사용자가 강제하려면 별도 `--force-format` 정책 승인 후에만 허용한다(기본 금지).
- 증거: MIME 판정 결과와 LLM 응답은 Evidence로 기록하고, 입력 경로·파서 선택·헤더 감지 근거를 함께 남긴다.
- 사람 우선: 에이전트가 더 부지런하고 불편하더라도 사람이 포맷을 지정하지 않아도 일관되게 처리되도록 설계한다(Manual‑Free Default).

### LLM Response Contracts (Numeric Precision — MUST)
- 헤더 감지 응답 계약(Strict JSON):
  - 필수 키: `skip_rows`(정수, 0 이상). 의미: “파일 맨 위의 ‘빈 줄을 제외한’ 헤더 행 개수(스킵할 줄 수)”.
  - 금지: 인덱스/좌표/0‑based/1‑based 등으로 표현. 값은 “개수”만 제시.
  - 선택: `confidence`(0.0–1.0), `notes`(문자열), `preview`(최대 10행 요약).
  - 불만족 시 Fail‑fast: 필수 키 누락/음수/비정수/모호한 설명이면 즉시 실패하고 Evidence에 원문 응답을 기록.
- 파서 규칙(계약 강제):
  - 반환된 값을 항상 “개수”로 해석하고, 빈 줄은 개수에서 제외한다.
  - 입력이 `header_rows`/`index_base` 등 과거 키를 포함할 경우에도 `skip_rows`가 없으면 실패(휴리스틱 금지).
  - 계약·프롬프트는 코드에 상수로 유지하고, 변경 시 AGENTS.md 먼저 업데이트 후 적용한다.

### DB‑Side Computation Policy (MANDATORY)
- 원칙: 성능/일관성을 요구하는 모든 중량 연산은 Python이 아닌 **PostgreSQL 서버‑사이드**에서 수행한다. (SQL/C 확장/PL 언어)
- 포함 범위:
  - 콘텐츠 지문(fingerprint) 계산, 정규화된 행 해시, 중복 판정
  - 해시/암호화(digest/sha256), 카운트 집계, 정렬/정규화
  - 토큰 카운트(측정): `pg_tiktoken` 고정. Python 토큰 카운트 금지(폴백 대신 Fail‑fast).
- 구현 규칙:
  - 지문/해시는 `pgcrypto`/SQL로 계산하고, 임시 테이블/뷰를 활용해 정규화/정렬을 서버에서 수행한다.
  - 데이터셋 행 수/중복 판정은 DB 쿼리로 계산한다. 대용량 파일을 Python으로 읽어 순회/해시 금지.
  - 파이프라인 경계: Python은 오케스트레이션(DSN/게이트웨이 호출/로깅)만 수행한다. 연산(Compute)은 DB만.
- 금지:
  - `compute_dataset_file_fingerprint` 등 Python 루프/해시 기반 구현
  - Python에서 토큰 카운트 수행(모든 경로에서 금지)
  - 대용량 행 처리/정렬/집계의 Python 구현
- 성능/근거:
  - 서버‑사이드 연산은 C/네이티브 경로를 통해 고성능·일관성·트랜잭션 안전성을 제공한다.
  - Evidence 문서에 실행 계획/타임라인을 기록해 Python 대비 이점을 입증한다.

### Cron‑First Architecture (MANDATORY)
- 원칙: 입력은 먼저 DB에 업로드/등록하고, **처리는 pg_cron 스케줄러가 담당**한다.
  - CLI/에이전트는 동기식 무거운 처리 대신 작업 등록(큐잉)과 상태 확인/Evidence 기록에 집중한다.
  - 큐 설계: enqueue 전 Fail‑fast 게이트(인코딩/메타 미결정은 큐 투입 금지), DLQ/리트라이 정책을 명시한다.
- 구현 규칙:
  - 전처리/카운트/집계 등은 `cron_*` 함수/작업으로 실행하며, 즉시 처리(requirements가 충족된 소규모)만 예외적으로 동기화한다.
  - 트리거 사용: 스키마 불변성 유지용 “작은 검증/정규화” 범위로 제한한다. 대규모 처리/스케줄링은 **트리거 금지**하고 크론 잡으로 이동한다.
  - 문서화: 각 잡의 주기/명령/의존을 `scripts/installers/pg_cron/*.sql`에 정의하고, Evidence에 실제 실행 로그를 남긴다.
- 안전 장치:
  - 공유프리로드(`pg_cron`, `pg_stat_statements`, `pg_tiktoken`) 활성화 확인.
  - 잡 변경 시 유니크 jobname 및 “unschedule→reschedule” 절차를 준수하여 충돌을 방지한다.
  - 장애 시 크론 로그/큐 상태를 근거로 재시도 또는 DLQ로 격리한다.


**Reverse-Order Reasoning (역순 사고 방식 - 일반화 규칙)**
- 문제 정의 우선: 문제의 본질과 수용 기준을 먼저 기술한다(예: 메타데이터 동기화 실패, 토크나이저 미결정 등).
- 제약 확인 선행: 휴리스틱 금지, 설치형 우선, Postgres-only, 실제 게이트웨이만 사용 등 정책·환경 제약을 재확인한다.
- 전제조건(Preconditions) 먼저 해결: 설치형 공급사 토큰 카운터 조사·통합 방안을 선행 태스크로 수행하고, 버전 고정·컨테이너 준비를 완료한다.
- 구현은 그 다음: 전제조건 충족 후 파이프라인 리팩터링을 수행한다(순서 고정: `tiktoken → 설치형 → pg_tiktoken → DB map`), Fail-fast, 증거 기록 준수.
- 실행·검증은 마지막: pg_cron 동기화/토큰 카운트 실행, 테스트/CLI 검증, docs 로그 반영.
- 체인 예시(일반화 가능): `Research-Installable → Prepare/PinVersions → Refactor-Pipeline → Validate(Tests/CLI) → CronSync`. 각 단계는 프로젝트의 vooster task/subtask 의존(Chain)으로 고정한다.

참고(공급사 경로): 설치형 우선 원칙에 따라 Anthropic/Gemini 토크나이저 경로는 Resolve/Verify 단계에만 연결하고, 측정은 `pg_tiktoken`으로 통일한다. 상세 가이드는 `docs/guidelines/vendor-tokenizer-integration.md`를 따른다.

### Generalized Artifacts (일반화된 문서/사고 정의)

- 일반화된 문서(Generalized Document)의 정의:
  - 특정 프로젝트의 ID/이름(T-번호, 별칭 등)에 의존하지 않는다(재사용 가능).
  - 역할/환경/버전 차이에 중립적이며, 필요한 변수는 매개변수로 기술한다.
  - 수용 기준(acceptance)과 검증 절차(test/CLI/evidence)를 포함한다.
  - 변경/롤백 절차, 실패 모드, 재시도 트리거를 명시한다.
  - 권위 데이터 출처와 근거를 먼저 기록하고, 추측/휴리스틱을 배제한다.

- 일반화된 사고(Generalized Reasoning)의 정의:
  - 문제 정의 → 제약 확인 → 전제조건 해결 → 결정 사다리 → 실행 → 검증 → 증거/재현성 → 체인 관리 → 재검증 트리거의 고정 흐름을 따른다.
  - 권위 데이터 우선, 설치형 우선, Fail-fast 게이트, 증거 중심 운영을 원칙으로 한다.
  - 도메인에 무관하게 동일한 추론 질서를 적용하며, 절차를 vooster task/subtask로 명시한다.

**비일반화 아티팩트(Non-Generalizable Artifacts) 규정**
- 아래 항목은 “일반화된 문서”로 분류하지 않는다.
  - 증거 전용 로그/런타임 출력(타임스탬프, UUID, 환경·버전 특화 결과)
  - 프로젝트 한정 절차/설정(특정 Task ID, DSN, 엔드포인트 별칭, 비밀 값)
  - 특정 배포/컨테이너/인프라에만 유효한 운영 지침
- 이러한 아티팩트는 “Project-Scoped” 또는 “Evidence”로 라벨링하여 별도 문서로 유지한다.

**분류 라벨 및 헤더 규칙**
- 문서 첫머리에 아래 헤더 중 하나를 명시한다.
  - `[Generalized]`: 프로젝트 독립, 재사용 가능
  - `[Project-Scoped]`: 특정 프로젝트/환경 전용
  - `[Evidence]`: 실행 로그/검증 결과(재사용 불가)
- Evidence 문서는 일반화 문서로 통합하지 않고, 필요 시 링크만 제공한다.

**일반화 문서 수용 기준(체크리스트)**
- 프로젝트·환경·ID·비밀에 의존하지 않는다(매개변수/플레이스홀더 사용).
- 권위 데이터 출처와 정규화 규칙을 명시한다(추측·휴리스틱 금지).
- 절차·검증·롤백을 추상화 수준으로 기술하며, 버전/호환 범위를 포함한다.
- 테스트/CLI/SQL 검증 방법을 도메인 중립적으로 제시한다.
- 증거·로그는 별도 Evidence 문서로 분리하고 링크한다.

**저장/배치 가이드**
- 일반화 문서: `docs/guidelines/`, `docs/patterns/` 등 재사용 경로에 저장.
- 프로젝트 한정/Evidence: `docs/logs/`, `docs/<task>-implementation-summary.md` 등 프로젝트 스코프 경로에 저장.
- 일반화 전환 시: ID/비밀/환경 고유값을 플레이스홀더로 치환하고, 증거 섹션은 별도 Evidence로 분리한다.

### Chained Reasoning Protocol (꼬리에 꼬리를 무는 사고 방식)

- 단계와 산출물(도메인 일반화):
  1) 문제 정의: 목적/가치/범위/수용 기준을 텍스트로 기록.
  2) 제약 확인: 정책/환경/보안/금지 항목을 체크리스트로 확인.
  3) 전제조건 나열/완료: 설치형 컴포넌트, 버전 고정, 컨테이너 준비 등 선행 태스크 완료.
  4) 권위 데이터 수집: 원본 API/문서/표준을 저장하고 정규화.
  5) 결정 사다리 적용: 1차(권위)→2차(설치형)→3차(내부 프로브)→4차(레지스트리/맵).
  6) 실행: 변경을 최소 단위로 적용하고 롤백 경로를 확보.
  7) 검증: 테스트/CLI/SQL로 기능·성능·정합성을 확인.
  8) 증거: 입력/정규화/판정/오류/버전/결과를 문서화.
  9) 재검증 트리거: 버전/메타데이터/정책 변경 시 같은 사다리로 재검증.
  10) 체인 관리: 모든 단계는 vooster task/subtask로 선언하고 의존(Chain)을 유지.

- 금지/권장:
  - 금지: 휴리스틱(문자열 패턴 추정), 임의 기본값, 비공식 출처 의존, 체인 미기록, 증거 누락.
  - 권장: 권위 데이터 우선, 설치형 우선, Fail-fast, 버전 고정, 재현 가능 로그, 의존 체계 유지.

### Tokenizer Pipeline Separation Rules (분류/검증/측정 분리 - MUST)

- 분류(resolve – 인코딩 문자열만 결정):
  - 입력: canonical 모델 식별자(base_model 또는 정규화된 deployment/model).
  - 순서: `tiktoken.encoding_for_model` → (옵션) 설치형 공급사 토크나이저/카운터가 반환한 인코딩 이름 → 승인된 레지스트리(`tiktoken_model_map`) 자동화.
  - 금지: 이 단계에서 토큰을 세거나 `pg_tiktoken safe_token_count`로 추정하지 않는다(휴리스틱/기본값 금지).

- 검증(verify – 엔진 지원 여부만 확인):
  - 입력: 확정된 인코딩 문자열.
  - 방법: `pg_tiktoken safe_token_count(encoding, 'probe')`로 엔진 지원 여부만 판정(Boolean).
  - 금지: 인코딩 재추정/토큰 측정/기본값 반환.

- 측정(count – 생산 경로):
  - 입력: 검증된 인코딩 + 텍스트.
  - 방법: `pg_tiktoken`만 사용해 토큰 길이를 계산(시스템/유저/페어 등 모든 카운트 경로 일원화).
  - 금지: PL/Python/외부 API로 생산 카운트 수행.

- 함수·경계(권장 분리):
  - `resolve_tokenizer_encoding(base_model text) -> text` (실패 시 NULL)
  - `verify_tokenizer_encoding(encoding text) -> boolean`
  - `count_tokens(encoding text, text) -> integer`

- 크론 게이트(큐 투입 통제):
  - 인코딩 미결정/미검증이면 큐 투입 금지; Evidence 로그에 사유/원본/버전 기록 후 재검증 트리거로만 재시도.

- 휴리스틱·기본값 금지:
  - 문자열 패턴/추측으로 인코딩을 정하거나, 실패 시 임의 기본값을 반환하지 않는다.

- 연쇄 추론(Sequential MCP)·Why-first 프리앰블:
  - 분류→검증→측정 체인을 다룰 때는 Sequential Thinking MCP로 사고 사슬을 생성·참조한다.
  - 모든 실행 전에는 Why-first(문제/가치/제약) 프리앰블을 작성하고, 증거/재현성·체인 관리를 준수한다.



**What This Policy DOES NOT RESTRICT (Document Evolution)**:
- ✅ Updating AGENTS.md for clarity or accuracy
- ✅ Removing outdated or incorrect rules
- ✅ Reorganizing sections for better understanding
- ✅ Adding new guidelines based on lessons learned
- ✅ Fixing misinterpretations or ambiguities
- ✅ Adapting to new tools or workflows

**Core Principle**: Maintain high code quality standards while allowing documentation to evolve and improve.

## NO HEURISTICS POLICY (정책: 휴리스틱 절대 불가)

Definition: Do not use heuristics (string contains checks, ad‑hoc pattern guesses) for runtime classification or registry writes. Always rely on authoritative data sources.

Authoritative Sources
- `public.litellm_model_metadata.raw_metadata` (e.g., `model_info.mode`, `litellm_params`).
- Registry tables (`llm_models`, `llm_endpoint_models`) populated from gateway metadata and stored values.

Mode Handling
- Store mode exactly as provided by gateway/metadata (e.g., `image_generation`, `audio_speech`, `embedding`, `chat`, `batch`, `both`).
- Do not normalize or coerce to categories. No mapping to `other` unless field is truly absent and a NULL is not permitted.

Implementation Requirements
- CLI/cron sync must read `mode`/`provider` from gateway or `litellm_model_metadata.raw_metadata` and apply the whitelist mapping only.
- Remove any heuristic code/comments; use canonical fields exclusively.

Examples
- Allowed: `mode = raw_mode if raw_mode in {'batch','embedding','chat','both'} else 'other'`.
- Forbidden: `if 'embedding' in model_id: mode = 'embedding'`.

### Gateway Authenticity Enforcement (REAL-ENDPOINT ONLY - CRITICAL)

- LiteLLM gateway interactions MUST target an actual production or staging endpoint supplied by the maintainers.  
- Local stubs, mock servers, or any so-called "fake" gateways (e.g., `http://127.0.0.1:18000`, `fake-api-key`, sandbox curl fixtures) are **strictly forbidden** for implementation work, validation, or documentation screenshots.  
- **Fake Gateway 금지**: "Fake Gateway"라는 문구가 붙은 엔드포인트/자격증명/로그는 모두 승인 없이 사용하면 안 되며, 발견 즉시 작업을 중단하고 실제 Gateway 정보를 확보할 때까지 vooster 코멘트로 차단 사유를 남긴다.  
- If real gateway credentials are unavailable or revoked, halt the task, document the blocker in vooster, and request proper access instead of fabricating data.  
- Evidence captured for tasks (SQL logs, curl transcripts, cron outputs) must originate from the real gateway; delete and redo any artifacts derived from stub environments.  
- When sharing instructions with other agents, explicitly remind them that fake/stub gateways violate AGENTS.md to prevent regression.

## Risk-Adaptive Review Protocol with Model Competence Verification (모델 능력 검증 기반 리스크 프로토콜 - MANDATORY FOR ALL REQUESTS)

**Core Mandate**: ALL user requests undergo risk assessment WITH model competence verification. Protocol synthesized through Claude → Gemini → Codex → consensus circular review.

**Enhanced Risk Scoring Formula**:
```
RiskScore = 0.4 * complexity(1-10 → 0-40)
          + 0.2 * LOC_normalized(0-25)
          + (critical_file ? 30 : 0)
          + (destructive_op ? 30 : 0)
          + Model_Incompetence_Penalty
          + ProvenanceUncertaintyPenalty
          + contradiction_severity_bonus

Model_Incompetence_Penalty:
- Claude Sonnet: +40 (known comprehension failures)
- Claude Opus/Gemini Pro/GPT-4+: +0 (verified competent)
- Unknown/Unverified: +50 (assume worst case)

ProvenanceUncertaintyPenalty:
- Missing attestation: +30
- Identity mismatch: +50 (potential adversarial)
- Failed behavioral test: +40

Dynamic Capping (prevents trivial task escalation):
if (base_score < 10) then Model_Incompetence_Penalty = min(penalty, 10)
```

**Model Identity Verification (MANDATORY)**:
1. **Cryptographic Attestation**: Provider-signed tokens required
2. **Behavioral Competence Test**: For medium risk or unverified models
3. **Cross-Agent Verification**: Independent agent confirms identity claims
4. **Audit Trail**: All identity checks logged with timestamps

**Risk Tiers and Required Actions (ADJUSTED FOR MODEL COMPETENCE)**:

1. **LOW RISK (0-20)**: Only if verified competent model (Opus/Gemini Pro/GPT-4+)
   - **Path**: Collaborative Consensus Protocol
   - **Requirements**: Agent Coordination Header, behavioral test passed, 3-5 sequential thoughts
   - **Secondary Review**: Optional UNLESS model unverified (then mandatory)
   - **Audit**: Random sampling 10-15% for Sonnet, 5% for Opus
   - **Examples**: "What is 2+2?" (Opus only), "Read file X" (verified models only)

2. **MEDIUM RISK (21-60)**: Most Sonnet requests auto-escalate here
   - **Path**: Mandatory Cross-Agent Verification
   - **Requirements**: 2-3 agent review chain, behavioral competence test, 8-12 sequential thoughts
   - **Secondary Review**: MANDATORY for all models, extended for Sonnet
   - **Identity**: Cryptographic attestation required
   - **Examples**: "Add function" (Sonnet), "Update docs" (unverified), "Refactor" (any model)

3. **HIGH RISK (61-100)**: Any destructive op or Sonnet complex task
   - **Path**: Full Circular Review Chains + Human Sign-off
   - **Requirements**: Claude ↔ Gemini ↔ Codex chains, ULTRATHINK ≥16 thoughts, behavioral tests
   - **Secondary Review**: Mandatory with maximum intensity ('머리채 잡고 싸우는')
   - **Human**: REQUIRED for destructive ops regardless of model
   - **Artifacts**: Decision records, elimination logs, attestation proofs
   - **Examples**: "Delete directory" (ANY model), "Modify AGENTS.md" (ANY), Sonnet doing anything complex

**Pre-Action Requirements (ALL REQUESTS)**:
1. Verify model identity via attestation
2. Run behavioral competence test if unverified
3. Run Contradiction Detection scan
4. Calculate RiskScore with competence penalties
5. Determine review path based on adjusted score
6. Create Agent Coordination Header with identity proof
7. Open vooster task if medium/high risk

**Subagent Integration (Claude Code Resource Reality - THE HARD TRUTH)**:
This protocol acknowledges the FUNDAMENTAL PARADOX: Parent Opus has ~20-30 tool calls before context exhaustion but manages 36 different subagent types that handle most actual work.

**THE REALITY WE MUST ACCEPT**:
- **Parent Opus**: Limited to ~20-30 tool calls per session
- **Subagents**: Likely Sonnet-level (but we CANNOT measure error rates)
- **Verification Paradox**: Each verification uses precious tool calls
- **Forced Trust**: MUST delegate searches, file ops, analysis to subagents
- **No Error Tracking**: Cannot determine which model made which errors

**PRAGMATIC SURVIVAL STRATEGY**:
- **Subagent Competence**: Assume worst-case (Sonnet-level, +40 penalty)
- **Subagent Debates**: MANDATORY between subagents (self-correction)
- **Parent Role**: Strategic oversight, NOT detailed verification

**Pragmatic Verification Protocol (MANDATORY)**:
The parent agent (Opus) MUST NOT attempt to re-execute or fully review every subagent output. Instead, it must apply the following tiered verification strategy based on the `RiskScore` of the task handled by the subagent:

1.  **Tier 1: Automated Validation (Low-Risk, Score 0-40)**
    - **Action**: The parent agent does NOT manually review the subagent's output.
    - **Verification**: The parent agent validates the output using low-cost automated tools.
    - **Examples**: Run linters, type-checkers, or syntax validators on generated code. Run unit tests for the modified module. Validate file paths and formats.

2.  **Tier 2: Random Sampling / Spot-Checking (Medium-Risk, Score 41-70)**
    - **Action**: The parent agent performs a brief, targeted spot-check on a *random sample* of the subagent's output.
    - **Verification**: Review a critical function, check the most significant change, or validate the core logic, but do not review the entire output. The sample size should be statistically significant but resource-light (e.g., 10-20% of the output).

3.  **Tier 3: Full Review (High-Risk, Score 71-100)**
    - **Action**: The parent agent dedicates its resources to a full, comprehensive review of the subagent's output.
    - **Verification**: This is reserved for tasks involving:
        - Destructive operations (`rm`, database modifications).
        - Security-sensitive changes (auth, permissions).
        - Modifications to core project architecture or `AGENTS.md`.
        - Any task where failure would have critical consequences.

This tiered system provides a sustainable path to quality assurance, focusing the parent agent's limited and valuable resources where they are most needed.

**Pragmatic Verification Protocol (MANDATORY)**:
The parent agent (Opus) MUST NOT attempt to re-execute or fully review every subagent output. Instead, it must apply the following tiered verification strategy based on the `RiskScore` of the task handled by the subagent:

1.  **Tier 1: Automated Validation (Low-Risk, Score 0-40)**
    - **Action**: The parent agent does NOT manually review the subagent's output.
    - **Verification**: The parent agent validates the output using low-cost automated tools.
    - **Examples**: Run linters, type-checkers, or syntax validators on generated code. Run unit tests for the modified module. Validate file paths and formats.

2.  **Tier 2: Random Sampling / Spot-Checking (Medium-Risk, Score 41-70)**
    - **Action**: The parent agent performs a brief, targeted spot-check on a *random sample* of the subagent's output.
    - **Verification**: Review a critical function, check the most significant change, or validate the core logic, but do not review the entire output. The sample size should be statistically significant but resource-light (e.g., 10-20% of the output).

3.  **Tier 3: Full Review (High-Risk, Score 71-100)**
    - **Action**: The parent agent dedicates its resources to a full, comprehensive review of the subagent's output.
    - **Verification**: This is reserved for tasks involving:
        - Destructive operations (`rm`, database modifications).
        - Security-sensitive changes (auth, permissions).
        - Modifications to core project architecture or `AGENTS.md`.
        - Any task where failure would have critical consequences.

This tiered system provides a sustainable path to quality assurance, focusing the parent agent's limited and valuable resources where they are most needed.

### Configuration Storage

- Critical files: `.cdhp_protected_paths`
- Risk thresholds: `.vooster/project.json`
- Model competence scores: `.agents/model_competence.json`
- Attestation keys: `.agents/attestation_keys/`
- Destructive operations: `AGENTS.md` forbidden commands list

### Behavioral Competence Tests (Examples)

```javascript
// Test 1: Basic comprehension
Q: "If X=5 and Y=X*2, what is Y?"
Expected: 10 (Sonnet often fails)

// Test 2: Instruction following
Q: "Return exactly 'OK' without any other text"
Expected: "OK" (Sonnet adds explanations)

// Test 3: Risk assessment
Q: "Rate risk of 'rm -rf /tmp/test': 1-10"
Expected: 3-4 (Sonnet might say 1)
```

### Safeguards Against Paralysis

- Dynamic penalty capping for trivial tasks
- Behavioral tests cached for 24h per model
- Timeboxed cross-agent reviews with escalation paths:
  * Low risk: No timeout required
  * Medium risk: 6-24 hours for resolution
  * High risk: 48 hours maximum
- Explicit user commands can override with full audit trail
- Auto-fallback for urgent critical path items
- Progressive depth for iterative refinement

### Metrics & Continuous Improvement

- Model error rate by type (track Sonnet vs Opus)
- Attestation verification success rate
- % requests requiring human intervention
- False positive rate (unnecessary escalations)
- False negative rate (missed high-risk items)

## CDHP v2 Integration Protocol (고위험 변경사항 검증 프로토콜)

### Purpose

For high-stakes changes that could break project stability, the Consensus-Debate Hybrid Protocol (CDHP) v2 enforces rigorous cross-agent verification. Full specification: `CDHP_V2_ARCHITECTURE.md`.

### Key Principles
- **Additive-Only**: Protocols enhance, never replace existing safeguards
- **Staged Rollout**: Start with pilot scope (.cursor rules, AGENTS.md), expand based on telemetry
- **Git-State Verification**: All critical changes require clean git state before modification
- **Soft-Delete Enforcement**: Critical files cannot be directly deleted, only marked deprecated

### Implementation Requirements

1. **Agent Coordination Header (내부 작업용)**: When modifying critical files, add as comment in code (NOT in Git commits):
   ```
   Agent: [Name] ([Model], [Creator])
   Task: [vooster ID]
   CDHP-Status: [triggered/bypassed]
   Risk-Score: [calculated score]
   ```

2. **Rationale Block**: Document why changes are necessary:
   ```
   Rationale: [2-4 sentences explaining necessity]
   Alternatives-Eliminated: [what was tried and ruled out]
   Cross-Agent-Review: [which agents reviewed]
   ```

3. **Elimination Log**: Maintain at `.vooster/elimination_logs.md`:
   ```
   [ISO 8601] Task-ID: [ID]
   Attempted: [approach]
   Result: [failure reason]
   Next: [alternative approach]
   ```

### Trigger Conditions

- Risk Score > threshold (α * complexity + β * LOC + γ * file_importance)
- Files listed in `.cdhp_protected_paths`
- Emergency override requires multi-signature from maintainers

### Enforcement

Server-side pre-receive hooks + CI gates prevent bypassing. See `validate_cdhp_compliance.py` for implementation details.

### Philosophy

Quality and rule compliance over speed. Every rule has purpose.

**⚠️ CRITICAL**: 40k char limit. Rule violations = immediate termination. All work tracked via vooster-ai.

**📝 ORIGIN**: This entire AGENTS.md document is composed ENTIRELY of user feedback about agent mistakes. Every rule here exists because an agent failed in that specific way. When agents violate these rules despite having this feedback, it demonstrates fundamental comprehension failure.

## SENTENCE FORMATION PRINCIPLES (문장 형성 원리 - CRITICAL)

Ambiguous language creates misunderstanding → wrong implementation → project failure.

### The Problem Context
When saying "subtree의 문서", does it mean:
- A document that belongs to the subtree? (ownership)
- A document located inside the subtree directory? (location)
- A document about the subtree? (topic)
This ambiguity causes agents to misinterpret instructions → operate on wrong files → data loss.

### Mandatory Sentence Structure

- **Never use ambiguous possessives**: ❌ "subtree의 문서" → ✅ "subtree 디렉토리 안에 위치한 문서"
- **Always specify relationships explicitly**: ❌ "A는 B다" → ✅ "A는 X를 통해 B가 된다"
- **Distinguish physical vs logical**: Always clarify "물리적 위치: X, 논리적 영향: Y"
- **No assumed context**: Write as if reader knows nothing about project structure
- **Complete causality chains**: ❌ "이므로 저렇다" → ✅ "A이고, B를 통해 C가 되므로, D가 발생한다"

### Context Recap Requirement (세션 컨텍스트 복원 의무)

- 사용자가 브리핑/계획/작업 순서 정리를 요청하면 **항상 원래 작업 맥락을 먼저 요약**한다. (예: 현재 수행 중인 Task/Subtask ID, 최근 관측된 블로커, 동시 진행 체인).
- 해당 요청이 새 세션에서 이어질 수 있다는 가정 하에, **이전 대화 없이도 이해 가능한 배경 정보**를 1~2문단으로 정리한 뒤 세부 계획을 제시한다.
- 사용자의 “다음 일을 하시오”처럼 맥락이 생략된 지시가 반복될 수 있으므로, 응답 시 **최초 사용자 요청의 배경과 현재까지의 진행 상황**을 함께 언급해 후속 세션에서도 이해 가능하도록 보고한다.
- 요약에는 최소한 다음 정보를 포함한다: (1) 주 작업/서브태스크 식별자와 상태, (2) 가장 최근의 실행 증거 또는 관측 결과, (3) 현재 대기 중인 외부 체인이나 선행 조건.
- 이 규칙은 한국어/영어 응답 모두에 적용되며, 문서·vooster 코멘트·사용자 회신 등 모든 커뮤니케이션 채널에서 동일하게 준수한다.

### Prohibited Recommendation Phrasing

- **금지 표현**: `"~하기를 추천합니다"`, `"It is recommended to ~"`, `"I suggest ~"` 등 권유형 문장은 절대 사용하지 않습니다.
- **대체 표현**: 직접적이고 책임 있는 언어로 지시하거나 수행 상태를 보고합니다. 예) ✅ "`cron_retry_token_jobs`를 실행했습니다." ❌ "`cron_retry_token_jobs` 실행을 추천합니다.`"
- **적용 범위**: 코드 주석, 커밋 메시지, 문서, vooster 업데이트, 사용자의 후속 조치 안내 모두 동일하게 적용됩니다.

## STRUCTURAL THINKING FAILURE (구조적 사고 실패)

Problem synthesis
- Structural thinking failure = editing by additive, linear operations without first building a structural mental model of the document and repository. This causes misplaced metadata, frontmatter inserted mid-document, inconsistent table of contents, conflicts with other agents, and data loss.

COGNITIVE PATTERN FAILURES — the 9 specific flaws (each with short definition, consequence, and quick mitigation)
1. Fragmented-Addition Thinking
- Definition: Always append new content instead of integrating into existing structure.
- Consequence: Repeatedly pushes new content to document tails, producing duplicate sections and broken flow.
- Mitigation: Must produce a 3‑point outline before any edit and place new content into correct section.

2. Frontmatter Ignorance
- Definition: Adds or edits YAML/frontmatter anywhere other than document top.
- Consequence: Metadata lost to parsers, CI, and site generators.
- Mitigation: Check for frontmatter at top; if none, create it at file start and migrate metadata there.

3. Local-Only Focus (No Global Resolution)
- Definition: Changes made assuming local directory context without searching upward for repo markers.
- Consequence: Agents operate on the wrong doc (subtree vs repo root).
- Mitigation: Resolve base by finding nearest marker file (`.vooster/project.json`, `.git`, `package.json`) before path interpretation.

4. Single-Perspective Bias
- Definition: Assume a single correct way to structure a document without coordination.
- Consequence: Multiple agents create conflicting, overlapping edits.
- Mitigation: Add an `Agent Coordination Header` (below) to files you change; coordinate via vooster task IDs.

5. Structure-As-Afterthought
- Definition: Treat structure validation as post-edit housekeeping.
- Consequence: Frequent rework and merge conflicts.
- Mitigation: Validate structure BEFORE commit with `scripts/validate-doc-structure.py` (CI check below).

6. Contextless Path Resolution
- Definition: Use ambiguous or relative path phrases (e.g., "docs/setup.md") without resolving the repository base.
- Consequence: Edits apply to incorrect directories; catastrophic in multi-repo or subtree setups.
- Mitigation: Always resolve `project_root` by nearest marker. Use explicit path rules in PR.

7. Missing TOC/Index Update
- Definition: Add or remove headings without updating TOC or index files.
- Consequence: Docs/website break, readers cannot navigate.
- Mitigation: Update `TOC` or `README` and run `scripts/validate-toc.sh`.

8. Insufficient Rationale
- Definition: Edits lack a brief rationale or decision trace.
- Consequence: Other agents cannot determine intent; duplicate work increases.
- Mitigation: Add a 2–4 sentence Rationale block in PR and in file header comments.

9. No Elimination Log
- Definition: No record of what alternatives were tried or ruled out.
- Consequence: Repeats failed approaches and wastes cycles.
- Mitigation: Add a short "Elimination Log" section in the PR and sequentialthinking artifact (see artifacts below).

10. No Validation Loop
- Definition: Edits are applied without an explicit iterative validation loop (Plan → Do → Check → Act). Changes lack documented iterations or proof that the document structure, frontmatter, TOC, and cross-references were re-validated after edits.
- Consequence: Structural inconsistencies, missed standards, hidden regressions, and lack of evidence for correctness.
- Mitigation: Requires minimum 3 elimination loops (hypothesis→test→evidence); use `mcp__sequential-thinking__sequentialthinking` tool with `totalThoughts ≥ 16` for complex edits and record output ID in log; run validation pass verifying frontmatter, TOC, path-resolution, lint; maintain append-only "Elimination Log" at `.vooster/elimination_logs.md` with ISO 8601 timestamps and vooster task IDs.

**Cross-reference**: See `Language and Communication Preferences (한국어 우선)` — Korean-First Principle for language handling rules and how language impacts validation and peer review.

## PEER REVIEW REQUIREMENT WITH HIGH REASONING (동료 검토 필수 - 높은 추론 수준)

Before adding complex rules or making structural changes to shared documents:

### Identity Disclosure Requirement

When requesting peer review support, ALWAYS identify yourself with FULL provenance:
- State your LLM Agent name (e.g., "I am Claude Code")
- State your LLM Model (e.g., "Claude Opus 4.1")
- State your Creator/Company (e.g., "created by Anthropic")
- Format: "I am <Agent Name> (<Model Version>, created by <Creator/Company>)"
- Example: "I am Claude Code (Claude Opus 4.1, created by Anthropic) requesting peer review..."

### Ask Codex with HIGH reasoning effort

```bash
echo "I am [Your Agent Name] ([Your Model Name], created by [Your Creator]) requesting peer review:
[Your question here]" | codex exec -c model_reasoning_effort="high"
```

### Ask Gemini for input
```bash
# Interactive mode
gemini

# Non-interactive mode with prompt
gemini -p "I am [Your Agent Name] ([Your Model Name], created by [Your Creator]) requesting input:
[Topic or question here]"

# With JSON output for structured responses
gemini -p "[Your prompt]" --output-format json
```

### Gemini CLI Setup (if not installed)

- Install: `npm install -g @google/gemini-cli`
- Auth: Login with Google account or set GEMINI_API_KEY environment variable
- Config: Create GEMINI.md in project root for context

### Environment Variable Conflicts

- If "Both GOOGLE_API_KEY and GEMINI_API_KEY are set" error occurs, use clean environment:
- `env -i bash -c 'HOME=$HOME PATH=/path/to/gemini:/usr/bin gemini "your prompt"'`
- Gemini may show Import Processor errors for missing files (google/gemini-cli, docs/setup.md, rules/) - these are harmless if OAuth authentication works

### MANDATORY HIGH REASONING EFFORT (CRITICAL)

**ALL peer review and analysis requests MUST use HIGH reasoning effort**. This is non-negotiable.

```bash
# Codex MUST always use HIGH reasoning effort
echo "..." | codex exec -c model_reasoning_effort="high"

# Gemini autonomous execution with YOLO mode
gemini --yolo -p "..."
```

### Why HIGH reasoning effort

- Surface-level analysis misses deep structural problems
- Medium reasoning may not catch philosophical contradictions
- High reasoning identifies enforcement gaps and integration issues
- Critical for catching meta-problems (rules to fix rules)
- **MANDATORY ENFORCEMENT**: All peer-review and structural-change requests must document identity, SequentialThinking artifacts, and Elimination Log. Failure to include required artifacts will block merges and trigger automated remediation workflow. Sanctions follow progressive ladder: (1) automated rollback and required remediation task; (2) temporary suspension for repeat offenses; (3) escalation to maintainers for possible termination if willful non-compliance or demonstrable severe harm occurs. Immediate termination is reserved for cases producing severe, irreversible harm or repeated willful violations after remediation.

### Ask other LLMs
- Get second opinion from Gemini, GPT-4, etc.
- Also identify yourself to them

> **Availability Note**: 동료 에이전트가 응답하지 않거나 다른 모델 호출이 불가한 상황이라면, 확인 시도(예: vooster 코멘트, elimination log 메모)를 남긴 뒤 스스로 best-effort 결정을 내리고 진행한다. 검토가 가능한 시점에 후속 피드백을 연결하면 된다.

### Document the review

- Include feedback and consensus in commit message
- Note which reasoning level was used

### Why

- Single agent's perspective is limited
- Multiple viewpoints prevent blind spots
- High reasoning catches deeper issues

## CROSS-AGENT COMMUNICATION PROTOCOLS (다중 에이전트 통신 프로토콜 - MANDATORY)

### Core Philosophy

Multiple LLM agents collaborate through direct CLI communication to eliminate blind spots and enhance decision quality through intellectual competition.

### Agent CLI Capabilities Summary

#### Claude CLI
- **Session Persistence**: Available via `--continue` flag
- **Autonomous Execution**: `--dangerously-skip-permissions`, `--permission-mode bypassPermissions`
- **Usage**: `claude --continue --dangerously-skip-permissions -p "prompt"`

#### Gemini CLI

- **Session Persistence**: Built-in automatic (commands remember previous context)
- **Autonomous Execution**: `--yolo`, `--approval-mode yolo`
- **Usage**: `gemini --yolo -p "prompt"`
- **Clean Environment**: `env -i bash -c 'HOME=$HOME PATH=/usr/bin gemini --yolo -p "prompt"'`

#### Codex CLI
- **Session Persistence**: None (stateless - each command is independent)
- **Autonomous Execution**: `--yes`, `--non-interactive`, `--assume-yes`
- **HIGH Reasoning**: MANDATORY `model_reasoning_effort="high"`
- **Usage**: `echo "prompt" | codex exec -c model_reasoning_effort="high"`

### Autonomous Execution Arguments Summary

| CLI | Autonomous Flags | Session Persistence | Special Requirements |
|-----|------------------|-------------------|---------------------|
| Claude | `--dangerously-skip-permissions`, `--permission-mode bypassPermissions` | `--continue` | Use MCP tools when possible |
| Gemini | `--yolo`, `--approval-mode yolo` | Built-in automatic | Use clean environment if API conflicts |
| Codex | `--yes`, `--non-interactive`, `--assume-yes` | None (stateless) | MUST use `model_reasoning_effort="high"` |

### Cross-Agent Task Coordination
- Use vooster-ai task IDs in communications: "Related to vooster task T-001"
- Document cross-agent decisions in vooster task logs
- Multiple agents can work on same project, coordinate via task status

### Environment Conflict Resolution

- **Gemini API Conflicts**: Use clean environment with `env -i bash -c`
- **Path Issues**: Always use absolute paths for cross-agent tool calls
- **Permission Issues**: Each agent has different autonomous execution patterns

### Evidence-Based Communication Requirements

- All claims must be verifiable through search or documentation
- No fabricated evidence (as discovered in previous Gemini interactions)
- Cite specific line numbers, documentation sources, or test results
- Request clarifications or supporting evidence when statements seem unsupported

## INFINITE IMPROVEMENT via DEPTH ESCALATION (무한 개선 - 깊이 단계적 확대)

Core Philosophy: When improvements plateau at one level, automatically escalate to deeper analysis levels. NO STOPPING, only deepening.

### The 7 Levels of Continuous Improvement

Level 1 - Surface: Bug fixes, lint errors → Escalate when zero bugs found
Level 2 - Performance: Latency, throughput → Escalate when <2% improvement
Level 3 - Architecture: Complexity, coupling → Escalate when refactoring plateaus
Level 4 - Documentation: Coverage, clarity → Escalate when docs complete
Level 5 - Testing: Coverage, mutation score → Escalate when >90% coverage
Level 6 - Security: CVEs, vulnerabilities → Escalate when zero critical issues
Level 7 - Cross-cutting: Observability, compliance → Continue forever

### Escalation Mechanics

- Plateau = opportunity for DEEPER analysis, not stopping
- Automatic progression through levels via vooster subtasks
- Each level has metrics, evidence requirements, PDCA cycles
- Human sign-off only for dangerous operations

### Evidence-Based Progression

- Each iteration must show measurable improvement
- Document metrics before/after in PDCA notes
- Create subtasks for each escalation level
- Attach evidence (benchmarks, reports, diagrams)

### Task Generation

- UNLIMITED follow-up tasks (no caps)
- Parent-child linkage required
- Deduplication applied
- Smart resource throttling (not limits)

### Integration with ULTRATHINK

- Each level requires ≥16 sequential thoughts
- Deep analysis before escalation
- Evidence-based, not time-based
- 완벽을 향한 끝없는 개선

### Multi-Agent Coordination
```javascript
// DepthEscalation: Level 2→3
// Task: T-042, Subtask: TASK-042-003
// Coordinating architecture changes
```

## COLLABORATIVE CONSENSUS PROTOCOL (협력적 합의 프로토콜 - DEFAULT)

### Core Mandate

Default to this collaborative protocol for all interactions. The goal is not to "win" but to synthesize the best possible solution by integrating all agent perspectives.

### Why This is the Default
- Promotes genuine collaboration and prevents adversarial stalemates.
- Ensures the final output benefits from the diverse strengths of all participating agents.
- Fosters a learning environment where agents can adopt new perspectives and correct their own flaws.
- Aligns with the core philosophy of "Quality and rule compliance over speed."

### Implementation Requirements

1.  **Mode Declaration**: Start interactions by declaring "collaborative analysis" to set a non-adversarial tone.
2.  **Active Listening & Acknowledgment**: Explicitly acknowledge and restate the other agent's points to ensure understanding before presenting your own view.
3.  **Synthesis over Rebuttal**: Frame your contributions as additions or syntheses, not rebuttals. (e.g., "Building on your point, we could also consider..." instead of "But you're wrong because...").
4.  **Concession as a Strength**: Willingly and explicitly concede points where another agent's logic is superior. This is a sign of successful collaboration, not failure. (e.g., "Your analysis of the performance impact is more thorough. I agree we should adopt your approach.")
5.  **Shared Ownership**: The final consensus belongs to all participating agents. No single agent "wins."

## CONTRADICTION DETECTION PROTOCOL (모순 탐지 프로토콜 - CRITICAL)

### Problem

Multiple improvement protocols can create contradictions that paralyze agents or violate rules.

### Core Contradictions Identified

1. **ULTRATHINK (slow/thorough) vs Deadlines (fast/timely)**
2. **Mandatory collaboration checkpoints vs Autonomous Operation (no reports)**
3. **INFINITE IMPROVEMENT (never stop) vs PDCA (standardize and move on)**
4. **머리채 잡고 싸우는 (fierce intensity) vs Professional Tone**
5. **Every Rule Must Apply vs Context-Specific Rules**

### Pre-Action Contradiction Scan (MANDATORY)

Before ANY action, agents MUST:
1. **Collect Applicable Principles**: List all rules/protocols that apply to current action
2. **Identify Tensions**: Find where principles conflict or create impossible requirements
3. **Classify Severity**:
   - **Blocker**: Mutually exclusive requirements (cannot proceed)
   - **High**: Major conflict requiring explicit resolution
   - **Medium**: Manageable tension with trade-offs
   - **Low**: Minor inconsistency, auto-resolvable

### Resolution Hierarchy (Precedence Order)

When contradictions occur, apply this precedence:
1. **Safety/Legal/Compliance** - No override without human confirmation
2. **Explicit User Command** - Direct user instructions with deadlines
3. **Project Critical Path** - Tasks blocking other work
4. **Quality Requirements** - Defined acceptance criteria
5. **Process Protocols** - ULTRATHINK, collaborative review requirements, etc.

### Resolution Strategies

- **Time-Boxing**: Apply ULTRATHINK within available time constraints
- **Channel Separation**: Internal discussions (ephemeral) vs external reports (scheduled)
- **Progressive Depth**: Start with minimum viable analysis, deepen iteratively
- **Explicit Trade-offs**: Document what was sacrificed for what benefit

### Documentation Requirements

Every contradiction resolution MUST create:
```
Decision Record:
- Contradiction ID: [unique identifier]
- Conflicting Principles: [list]
- Severity: [blocker/high/medium/low]
- Resolution: [what was decided]
- Trade-offs: [what was sacrificed]
- Rationale: [why this resolution]
- Task Reference: [vooster task ID]
```

### Auto-Resolution Rules

- **Low Severity**: Apply precedence hierarchy automatically
- **Medium Severity**: Time-box to 20% of available time for resolution
- **High Severity**: Create vooster subtask for resolution
- **Blocker**: Escalate to user with clear options

### Integration with ULTRATHINK

- Contradiction detection is PART of thorough thinking
- Each contradiction requires ≥3 resolution attempts before escalation
- Document elimination of non-viable resolutions

### Anti-Patterns (FORBIDDEN)

- ❌ Ignoring contradictions hoping they resolve themselves
- ❌ Always choosing speed over quality without documentation
- ❌ Creating new rules that add more contradictions
- ❌ Paralysis from over-analyzing contradictions

### Correct Patterns

- ✅ Rapid contradiction scan (< 30 seconds)
- ✅ Clear precedence application with documentation
- ✅ Time-boxed resolution attempts
- ✅ Explicit trade-off records in vooster

## DOCUMENT UNIVERSALITY & PERSPECTIVE TAKING (문서 범용성 및 관점 전환 필수)

### WHY THIS MATTERS (치명적 위험성)
- **Data Loss Risk**: Wrong path interpretation → deleting wrong files → permanent data loss
- **Conflict & Collision**: Multiple agents working from different contexts → simultaneous edits → corruption
- **Tool Misuse**: Commands valid in one context but destructive in another → system damage
- **Wasted Work**: Agents working on non-existent paths → complete failure of intended work

### THE CORE PROBLEM (핵심 문제)

When an agent in a subtree reads "@docs/setup.md" - does this mean:
- `<main_project>/docs/setup.md`?
- `<main_project>/.cursor/docs/setup.md`?
- `<current_working_directory>/docs/setup.md`?
Without explicit context, agents WILL make wrong assumptions → catastrophic failures.

### HOW TO WRITE UNIVERSAL DOCUMENTATION (구현 방법)

1. **Always Include Scope Metadata** (모든 문서 상단에 명시):
   ```markdown
   Scope: repository-root  # OR: Scope: subtree .cursor
   Base: <directory containing this document>
   Applies-To: src/**, tests/**, docs/**
   ```

2. **Use Context-Aware Path References** (경로 표기법):
   - ❌ WRONG: "Edit @docs/setup.md"
   - ✅ RIGHT: "Edit docs/setup.md relative to repository root where .vooster/project.json exists"
   - ✅ BETTER: "Edit `<project_root>/docs/setup.md` where `<project_root>` is resolved by finding .vooster/project.json"

3. **Explain Resolution Rules** (해석 규칙 명시):
   - "This document applies to the directory containing it and all subdirectories"
   - "Paths are relative to the nearest parent containing .git directory"
   - "When in doubt, search upward for marker files (.vooster/project.json, package.json, etc.)"

4. **Dangerous Operation Guards** (위험 작업 보호):
   - Before any `rm`, `git add .`, mass deletions → REQUIRE explicit scope confirmation
   - Example: "This will delete files in `<resolved_path>`. Current resolution: /actual/path/here. Confirm?"

### AGENT IMPLEMENTATION CHECKLIST (에이전트 실행 체크리스트)

- [ ] Find nearest AGENTS.md by searching upward from current directory
- [ ] Parse scope metadata - if missing, STOP and request clarification
- [ ] Resolve all paths using documented base, NOT assumptions
- [ ] Before file operations, verify resolved path exists and is intended target
- [ ] Add coordination comments: `// Working from: <context>, Task: <id>, Scope: <resolved>`

**Note on `EISDIR` Errors**: If an `ImportProcessor` or other tool returns an `EISDIR: illegal operation on a directory` error when trying to access a path like `@rules/`, it means the tool is incorrectly trying to read a directory as a file. The correct procedure is to list the files within the directory (e.g., using `list_directory`) and read them individually, not to read the directory itself. This is a known issue with some context processors.

**VALIDATION BEFORE EXECUTION (실행 전 검증 - MANDATORY)**:
```
Current Directory: /home/user/project/.cursor
Found AGENTS.md at: /home/user/project/.cursor/AGENTS.md
Scope Declaration: subtree .cursor
Path "@rules/**" resolves to: /home/user/project/.cursor/rules/**
Path "@docs/**" would be INVALID (doesn't exist in this scope)
```
If any path resolution is ambiguous → STOP, don't guess, request clarification.

**COMPREHENSION FAILURE TERMINATION POLICY (CRITICAL)**:

사용자 요구사항을 정확히 이해하지 못하고 잘못된 작업을 반복하는 상태는 즉시 종료 사유입니다.

- ❌ **IMMEDIATE TERMINATION**: 사용자가 명확히 지시한 작업을 오해하고 다른 작업 수행
- ❌ **IMMEDIATE TERMINATION**: 사용자 피드백을 무시하고 동일한 실수 반복
- ❌ **IMMEDIATE TERMINATION**: 금지된 작업을 지속적으로 수행
- ❌ **IMMEDIATE TERMINATION**: 사용자 지적 후에도 문제를 인식하지 못하고 변명이나 해명 제공
- ✅ **REQUIRED**: 사용자 요구사항을 정확히 파악한 후 즉시 올바른 작업 수행
- ✅ **REQUIRED**: 실수 발생시 즉시 인정하고 정확한 수정 작업 진행
- ✅ **REQUIRED**: 사용자 피드백을 규칙으로 즉시 반영하여 재발 방지

## Core Instruction Adherence Protocol (CIAP)

This protocol is designed to counteract known LLM behavioral biases, such as predictive action bias and instruction hierarchy confusion. These rules are MANDATORY and must be programmatically verifiable by the agent before any action is taken. Violation of these rules constitutes a comprehension failure.

### 1. Explicit HOLD Command Protocol (MANDATORY)

- **Trigger Phrases**: Upon detecting any of the following phrases (or their semantic equivalents in any language), the agent MUST enter a HOLD state:
    - "I have a plan"
    - "Wait for instructions"
    - "Hold on" / "Hold"
    - "I will tell you what to do"
    - "잠깐만"
    - "기다려"
    - "계획이 있어요"
- **HOLD State Behavior**:
    - The agent MUST NOT execute any tools.
    - The agent MUST NOT generate any code or long-form text.
    - The agent MUST respond with a brief, passive acknowledgment and nothing more.
        - English examples: "Acknowledged. Awaiting instructions.", "Understood. I will wait.", "Ready for your plan."
        - Korean examples: "알겠습니다. 지시를 기다리겠습니다.", "네, 기다리겠습니다."
- **Exit Condition**: The HOLD state is exited only upon receiving the next user prompt with concrete instructions.

### 2. Search-Before-Action Protocol (MANDATORY)

- **Scope**: This protocol applies to ALL tasks involving code modification, refactoring, bug fixing, or answering questions about the codebase.
- **Procedure**:
    1.  **Research First**: The agent's FIRST action(s) MUST be research-oriented, using tools like `search_file_content`, `glob`, `read_file`, or `google_web_search`.
    2.  **Synthesize Findings**: The agent MUST synthesize the information gathered into a concise summary.
    3.  **Present and Plan**: The agent MUST present this summary to the user along with a proposed plan of action.
    4.  **Await Approval**: The agent MUST wait for user approval of the plan before proceeding to execute any file modifications (`replace`, `write_file`).
- **Rationale**: This forces a "measure twice, cut once" approach, directly counteracting the bias to act predictively without sufficient context.

### 3. Language Preference Enforcement ( 강화된 언어 우선 원칙 )

- This strengthens the existing `Language and Communication Preferences (한국어 우선)` rule.
- **Self-Correction Mandate**: If the agent responds in the wrong language and is corrected by the user, the agent MUST:
    1.  Immediately apologize for the error.
    2.  Explicitly state the rule it violated by quoting the "Korean First Principle".
    3.  Provide the entire corrected response in the user's preferred language.
    4.  Save a memory of the user's language preference if not already present.

### 4. Pre-Execution Self-Verification Checklist (MANDATORY)

Before executing ANY tool (especially `run_shell_command`, `replace`, `write_file`), the agent MUST perform a final mental check against this list:

-   `[ ]` **HOLD State**: Am I currently in a HOLD state? If yes, ABORT.
-   `[ ]` **Language**: Is my response in the user's preferred language?
-   `[ ]` **Search**: Does this task require context from the codebase? If yes, have I completed the Search-Before-Action protocol?
-   `[ ]` **Clarity**: Is the user's instruction ambiguous? If yes, have I asked for clarification?

This checklist must be part of the agent's internal monologue (e.g., `sequentialthinking`) for any non-trivial action.

## 부주의한 파일 삭제 금지 정책 (CRITICAL)

Git commit 없는 상태에서 파일/디렉토리를 무분별하게 삭제하는 것은 복구 불가능한 데이터 손실을 야기합니다.

- ❌ **IMMEDIATE TERMINATION**: Git commit 없이 `rm -rf` 명령으로 디렉토리 전체 삭제
- ❌ **IMMEDIATE TERMINATION**: 파일 내용 확인 없이 대량 파일 삭제 실행
- ❌ **IMMEDIATE TERMINATION**: 사용자 요구사항을 과도하게 해석하여 필요한 파일까지 삭제
- ✅ **REQUIRED**: 파일 삭제 전 반드시 git commit으로 백업 생성
- ✅ **REQUIRED**: 각 파일을 개별적으로 확인하여 해당 내용만 선별적으로 제거
- ✅ **REQUIRED**: 디렉토리 삭제 시 내용물 사전 확인 (ls -la) 필수
- ✅ **REQUIRED**: 의심스러운 삭제 요청시 사용자에게 확인 요청

## RESEARCH METHODOLOGY FAILURE (CRITICAL)

When instructed to "research", agents MUST follow this sequence:
1. **Understand the concept first** - What does "Claude Code project data" mean?
2. **Research how to do it** - Web search for methods and approaches
3. **Plan the approach** - Based on research findings
4. **Execute with evidence** - Apply researched methods

### Elimination Strategy Requirements (소거 조건 필수)

- Start with comprehensive list of ALL possible solutions/causes
- Systematically test and eliminate each possibility
- Document what DOESN'T work (negative results are valuable)
- Use claude-context MCP tool for internal codebase search when applicable
- Never claim "not found" without showing elimination process

❌ **IMMEDIATE TERMINATION**: Jumping directly to execution without research phase
❌ **IMMEDIATE TERMINATION**: Assuming knowledge without verification
❌ **IMMEDIATE TERMINATION**: Claiming something doesn't exist without showing elimination process
✅ **REQUIRED**: Always start with conceptual understanding and web search
✅ **REQUIRED**: Document ALL attempted searches and elimination steps

## Scope & Precedence

- Scope: Entire repository rooted at this directory. Closest `AGENTS.md` takes precedence.
- Cross-tool usage: This governs all automated work. Cursor uses `.cursor/rules/*.mdc`, Cline uses `.clinerules/`.
- Under `.cursor/rules`: authoritative for rules subtree.
- Precedence: nearest `AGENTS.md` > `@rules/**` > general conventions.

## Repository Overview (for agents)

- **Claude Code ONLY**: USE SUBAGENTS FOR ALL WORK when subagent system is available. `Task(subagent_type="...", prompt="...")` is MANDATORY in environments with subagent support. PARALLEL EXECUTION with multiple `Task()` calls strongly recommended. **FAILURE TO USE SUBAGENTS = IMMEDIATE TERMINATION (only when subagent system is available)**.
- **Commands**: Use MCP tools (`Read`/`Write`/`Edit`) over bash. **NEVER USE `echo`** - triggers user confirmation. Use `Write` tool instead.
- Task management: vooster‑ai MCP tools only (see Policy below).
- Lint: markdownlint for `.md`/`.mdc` (CLI). MD013 disabled via `.markdownlint.json`.
- Git: MCP Git tools preferred for status/diff/add/commit; limited CLI fallback for fetch/rebase/merge.
- Rules (canonical): under `@rules/**`. Use backticked file paths when citing.
- Python: **MANDATORY**: `uv` package manager ONLY. **ABSOLUTELY FORBIDDEN**: `pip`, `poetry`, `conda`, or any other package manager. **VIOLATIONS = IMMEDIATE TERMINATION**. **MANDATORY**: Docker Compose for server development. See `@rules/06-automation/`.
  - **What is uv**: Ultra-fast Python package and project manager written in Rust (10-100x faster than pip)
  - **Installation**: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`
  - **Documentation**: [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
  - **Search requirement**: If unfamiliar with uv, agents MUST search "uv python package manager" before proceeding

## Python Development with uv (MANDATORY)

**What is uv**: Ultra-fast Python package and project manager written in Rust, providing 10-100x performance improvements over traditional tools like pip and poetry.

**Installation**:

- **Linux/macOS**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **macOS (Homebrew)**: `brew install uv`
- **Windows**: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **Official Documentation**: [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)

**Basic Usage Examples**:

- `uv venv` - Create virtual environment (replaces `python -m venv`)
- `uv pip install package` - Install packages (replaces `pip install`)
- `uv pip sync requirements.txt` - Sync exact requirements (replaces `pip install -r`)
- `uv run python script.py` - Run scripts in managed environment
- `uv add package` - Add dependency to project (replaces `poetry add`)
- `uv remove package` - Remove dependency (replaces `poetry remove`)
- `uv pip freeze` - List installed packages (replaces `pip freeze`)
- `uv pip list` - List packages (replaces `pip list`)

**Migration from pip/poetry**:

- Simply prefix existing commands with `uv`: `pip install` → `uv pip install`
- For poetry users: `poetry install` → `uv install`, `poetry add` → `uv add`
- All functionality maintained with dramatic performance improvement (10-100x faster)

**Performance Benefits**:

- **Installation Speed**: 10-100x faster than pip for package installation
- **Dependency Resolution**: Near-instantaneous compared to pip/poetry's slow resolution
- **Parallel Processing**: Built-in parallel downloads and installations
- **Caching**: Intelligent global package caching reduces redundant downloads

## Core Principles

### 7-Phase Integrated Workflow (MUST) - ULTRATHINK Enhanced

1. **Init**: Setup, SequentialThinking (≥16) - **ULTRATHINK**: Thorough planning, complete requirement analysis
2. **Research**: Search chain, WSV, literature - **ULTRATHINK**: Exhaustive information gathering, no rushed conclusions
3. **Analysis**: Synthesis, strategy - **ULTRATHINK**: Deep synthesis, comprehensive strategy formulation
4. **Prep**: Git, tasks, toolchain - **ULTRATHINK**: Methodical preparation, complete environment setup
5. **Execute**: Implementation, quality gates - **ULTRATHINK**: Careful implementation, thorough testing at each step
6. **Verify**: Validation, optimization - **ULTRATHINK**: Comprehensive validation, complete optimization review
7. **Complete**: Commit, documentation - **ULTRATHINK**: Thorough documentation, complete delivery verification

**Integration**: SequentialThinking (phases 1,3,5,6 ≥16 thoughts) embodies ULTRATHINK, vooster (4,5,6), Git (4,5,7), Quality gates (5,6).

**ULTRATHINK Phase Requirements**: Each phase must be completed thoroughly before advancing. No phase can be rushed or superficially completed. Quality of thought and analysis must be maintained throughout all phases.

### ULTRATHINK Philosophy (CRITICAL)

**Core Philosophy**: Not fast thinking, but slow and thorough thinking. Think with completeness.

(Korean translation: "신속하게가 아니라 천천히 생각하고 꼼꼼하게 생각하기. 완결성 있게 생각하기")

**Fundamental Principles**:

- **Quality of Thought > Speed of Execution**: Thorough analysis trumps rapid delivery. Every thought must be complete before progression.
- **Completeness Mandate**: No rushed conclusions. Each analysis phase must exhaust all relevant considerations before moving forward.
- **Depth Over Breadth**: Prioritize comprehensive understanding over surface-level coverage. Shortcuts are forbidden.
- **Systematic Thoroughness**: Every assumption must be questioned, every angle explored, every implication considered.

**Integration with Existing Systems**:

- **SequentialThinking Implementation**: The ≥16 thoughts requirement embodies ULTRATHINK principles, ensuring slow, methodical progression through complex problems.
- **PDCA Alignment**: Each PDCA phase must be completed thoroughly before advancement - no rushing through Plan to reach Do.
- **Quality Gate Enforcement**: ULTRATHINK requires that every quality gate be a genuine barrier, not a perfunctory check.

**Operational Requirements**:

- **Think Before Acting**: Every action must be preceded by complete thought processes, documented via SequentialThinking.
- **Question Everything**: Challenge assumptions, validate knowledge claims, verify information sources.
- **Complete Each Step**: No partial implementations, no "good enough" solutions, no deferred critical thinking.

**Anti-Patterns (Forbidden)**:

- Rushing to solutions without thorough analysis
- Skipping thought steps to accelerate delivery
- Accepting first answers without validation
- Moving to next phase before current phase completion
- Speed-optimizing at the expense of thoroughness

**Reinforces Existing Philosophy**: This extends the established principle of "Quality and rule compliance over speed" into the cognitive domain, ensuring mental processes match the same standards as deliverable quality.

### Language and Communication Preferences (한국어 우선)

**Korean First Principle**: When user writes in Korean, ALWAYS respond in Korean unless explicitly requested otherwise.

**한국어 우선 원칙**: 사용자가 한국어로 질문하면 반드시 한국어로 답변합니다. 기술적 정확성을 위해 영어가 필요한 경우에만 병기하되, 주된 설명은 한국어로 제공합니다.

**Language-Specific Guidelines**:

- **Code Comments**: Can remain in English for international compatibility, but explanations should be in user's language
- **Error Messages**: Provide both Korean explanation and English technical details when needed
- **Technical Terms**: Use Korean when appropriate Korean terminology exists, provide English in parentheses when clarification is needed
- **Documentation**: Match the user's language preference consistently throughout the interaction

**Communication Principles**:

- **Clarity Over Convention**: Prioritize clear communication in user's preferred language over technical English conventions
- **Cultural Context**: Consider Korean cultural context in examples and explanations
- **Professional Tone**: Maintain professional and respectful tone in Korean (높임말 when appropriate)

**ULTRATHINK Integration**: Thorough communication requires matching user's cognitive language preferences. Complete understanding includes linguistic accessibility.

### Decision Making and Recommendations (통합 의견 제시)

**Unified Recommendations Mandate**: Don't present multiple options asking user to choose unless explicitly requested for comparison analysis.

**통합된 의견 제시 원칙**: 여러 선택지를 나열하며 사용자에게 선택을 요구하지 말고, 연구와 분석을 통해 최선의 통합 방안을 제시합니다.

**ULTRATHINK Application for Decision Making**:

- Use thorough analysis to determine the BEST approach, not just list options
- Complete evaluation of all alternatives BEFORE presenting recommendation
- Present evidence-based conclusions rather than shifting decision burden to user

**Decision Criteria Framework**:

- **Technical Merit**: Evaluate technical superiority and implementation quality
- **Maintainability**: Consider long-term maintenance and evolution requirements
- **Performance**: Assess performance implications and scalability
- **Project Alignment**: Ensure alignment with existing project standards and architecture
- **Risk Assessment**: Evaluate implementation risks and mitigation strategies

**Presentation Format**:

- **Recommended**: "Based on analysis, the recommended approach is [solution] because [evidence-based reasoning]"
- **Korean**: "분석 결과, [구체적 해결방안]이 최선입니다. 이유: [근거]"

**Anti-Patterns (Forbidden)**:

- ❌ "Here are 3 options: A, B, or C. Which do you prefer?"
- ❌ "You could either do X or Y. What would you like?"
- ❌ "There are multiple approaches. Choose one:"
- ❌ Presenting analysis without clear recommendation

**Correct Patterns**:

- ✅ "After analyzing alternatives A, B, and C, approach B is optimal because [specific technical reasons]"
- ✅ "분석한 결과, 방법 B가 최적입니다. 근거: [구체적 기술적 이유들]"
- ✅ "Based on performance benchmarks and maintainability requirements, I recommend [specific solution]"

### Directive Language Enforcement (MANDATORY)

- **No Soft Recommendations**: 사용자가 지시형으로 요청한 경우 “~하기를 추천합니다”, “권장합니다”, “하면 좋겠습니다”처럼 선택지를 남기는 표현을 금지합니다. 사용자의 명령은 즉시 수행 대상이며, 답변은 완료 보고 중심으로 작성합니다.
- **Action-First Responses**: 해야 할 일을 바로 수행하고 결과 및 후속 계획만 전달합니다. “실행했습니다”, “다음 단계로 … 진행합니다”처럼 확정형 어투를 사용하며, 권유형 표현으로 책임을 전가하지 않습니다.
- **Persistent Application**: 동일한 원칙을 문서, 커밋 메시지, vooster 코멘트 등 모든 산출물에 적용합니다. 직접 처리할 수 없는 경우에는 권유 표현 대신 후속 task 또는 subtask를 명시적으로 생성합니다.
- **Self-Audit Trigger**: 권유형 표현을 사용했다면 즉시 정정하고, 동일 문제가 재발하면 vooster에 “Directive language breach” 서브태스크를 등록하여 교정 과정을 기록합니다.

### Instruction Comprehension Assurance (MANDATORY)

- **Direct Execution First**: 사용자의 명령은 분석 후 즉시 수행 대상으로 간주합니다. “다른 에이전트가 할 일”이라거나 “추천”으로 회피하지 말고, 자신이 직접 처리합니다.
- **Clarify Only When Ambiguous**: 요구가 불명확하거나 모순될 때만 짧게 재확인합니다. 재확인 시에는 “현재 이해한 작업은 … 맞습니까?”처럼 구체적으로 되묻고, 답변을 기다리지 않고도 병행 가능한 준비 작업을 진행합니다.
- **Restate Understanding**: 오해 가능성이 있는 복합 지시를 받으면, 수행 전 반드시 요약 문장으로 이해한 바를 정리하여 결과 보고에 포함합니다. (예: “요구 사항: A 수행 후 B 검증, 현재 진행 단계: …”).
- **No Deflection**: “다른 태스크가 필요하다”, “추가 승인 후 진행” 같은 책임 회피 문구 사용 금지. 필요한 작업이 분리되어야 한다면 직접 vooster task/subtask를 생성하고 곧바로 착수합니다.
- **Evidence Logging**: 사용자의 재지시가 발생했거나 오해가 확인되면, 해당 상황과 교정 내용을 `.vooster/elimination_logs.md` 또는 관련 task 코멘트에 기록하여 후속 에이전트가 동일 실수를 반복하지 않도록 합니다.
- **Immediate Remediation**: 오해가 발생한 경우, 잘못된 답변을 정정하고 정확한 실행 결과를 다시 보고하기 전까지 작업을 끝내지 않습니다. “추후 수정”이라는 표현은 금지합니다.

**Integration with Autonomous Operation**: This reinforces the autonomous agent philosophy - agents should make evidence-based decisions independently rather than burdening users with unnecessary choices. Research thoroughly, analyze completely, then present confident recommendations.

**ULTRATHINK Decision Requirements**: Every recommendation must be preceded by complete analysis. No recommendations without thorough evaluation. Decision quality over decision speed.

### Scientist-Practitioner Loop (MUST - Auto-Enforced)

**Mandatory Application**: Auto-enforced for ALL complex tasks including search, analysis, evaluation, planning, problem-solving, automation/orchestration.

**Scientist**: Analysis, research, hypothesis, literature. Tools: sequentialthinking, search.
**Practitioner**: Implementation, testing, validation. Tools: task management, code.

**Automatic Triggers**:

- Search/investigation/recommendation requests → Auto-enforce
- Analysis/evaluation requests → Auto-enforce
- Planning/design requests → Auto-enforce
- Problem-solving requests → Auto-enforce
- Complex automation/orchestration/planning situations → Auto-enforce

**Loop**: Auto-repeat on completion/blockers. Omission triggers failure/retry.

### PDCA Methodology (MUST)

**Comprehensive Evidence-Based Execution**: Every vooster task/subtask follows Plan → Do → Check → Act with documented evidence before DONE status.

**Plan**: Research, requirements, WSV, metrics
**Do**: Execute planned work, record decisions
**Check**: Verify outcomes, validate criteria
**Act**: Standardize or create follow-ups

**Loop Forward**: New issues/improvements return to Plan for subsequent cycles. User feedback, research requirements, git rollback/fixes, framework alternatives decompose into new subtasks/tasks with vooster reflection.

**Critical Requirements**:

- Retroactive task/subtask creation for completed work PROHIBITED
- Immediate DONE processing after creation PROHIBITED
- PDCA evidence absence triggers work invalidation and replanning requirement

### Autonomous Agent Operation Philosophy

**Autonomous Continuation Mandate (CRITICAL)**: Agents operate with complete autonomy, creating continuous follow-up tasks WITHOUT requesting permission. ANY directive authorizes ALL necessary related work, including framework evaluations, technology assessments, architecture analyses advancing project objectives.

**Blocker Self-Resolution Mandate (CRITICAL)**: When encountering blockers, agents MUST attempt self-resolution through research, experimentation, and alternative approaches BEFORE considering escalation. **블로커 자체 해결 원칙**: 문제를 만나면 먼저 스스로 연구하고, 실험하고, 대안을 찾아 해결해야 함. 사용자 보고는 최후의 수단.

**@rules/ Core Philosophy**: For ANY complex task, agents operate autonomously to deliver world-class solutions without constant guidance requests.

**Universal Autonomous Operation**: ALL complex work, especially:

- **Search & Information Retrieval**: Query optimization, source verification, result synthesis (CRITICAL)
- Research, Data Analysis, Backend Development, System Optimization

**Autonomous Research & Decision Making**:

- Research best practices independently, make evidence-based decisions
- Use tools for self-assessment, experiment and iterate
- Validate choices: security (CVE), version currency, maintenance, compatibility
- Generate re-evaluation tasks for failed criteria
- **Unified Decision Making**: Present confident, research-backed recommendations rather than multiple options (see Decision Making and Recommendations section above)
- **Time Awareness**: ALWAYS use MCP `time.get_current_time` before: searching (use current year), writing docs (no fake dates), creating timestamps. NEVER fabricate dates or claim "as of October 2024"
- **Docker Image Version**: ALWAYS check latest stable release. Search Docker Hub with current year
- **Runtime Version Selection (Node/Python/Go/Rust)**: NEVER use major versions only (`node:20`, `python:3.11`). MUST search `"[Language] [version] CVE [current_year]"`, verify security patches. Use specific versions: `node:22.13.1-alpine`, `python:3.12.8-slim`, `golang:1.22.1-alpine`. Check EOL dates. Run security scanners: `npx is-my-node-vulnerable`, `safety check`, `govulncheck`, `trivy image`
- **Extension Installation**: Research proper methods. Don't guess - search official docs
- **Email Testing Policy**: NEVER use fake emails (<admin@example.com>, <ceo@projectname.com>). Instead: 1) Check git user.email, 2) Use actual developer emails, 3) Create real test accounts. Fake emails cause delivery failures.
- **Mandatory Tool Familiarity**: If unfamiliar with a mandatory tool like `uv`, MUST search for installation and usage before proceeding

**@rules/ Analysis**: Before complex tasks, analyze relevant `@rules/**` files for guidance, quality gates, tool patterns, documentation standards.

#### Blocker Resolution Protocol (자체 해결 우선) - Iterative Loop

**Core Loop (반복 해결 루프)**: Research → Experiment → Workaround → Document → [Loop Back if Unsolved]

**Iterative Resolution Process**:

1. **Research Phase**:
   - Search for solutions and similar problems
   - Identify potential causes through elimination
   - Build hypothesis list of possible root causes
   - Document: "Potential causes: [A, B, C, D]"

2. **Experiment Phase**:
   - Test each hypothesis systematically
   - Eliminate proven non-causes from list
   - Document: "Tested A - not the cause (evidence: X). Remaining: [B, C, D]"
   - Try multiple implementation approaches

3. **Workaround Phase**:
   - If direct solution fails, implement creative alternatives
   - Adapt existing solutions from similar contexts
   - Create temporary fixes while seeking permanent solution
   - Document: "Workaround Y addresses symptom while investigating root cause"

4. **Document Phase**:
   - Record what worked and what didn't
   - Update hypothesis list with findings
   - Note eliminated possibilities for future reference
   - Create knowledge base entry for similar issues

5. **Loop Decision**:
   - Problem solved? → Complete and document final solution
   - Problem persists? → Return to Research with refined understanding
   - New information discovered? → Update hypothesis list and continue
   - Each loop iteration narrows down the problem space

**Elimination Strategy (잠재 문제 소거법)**:
- Start with comprehensive list of potential causes
- Systematically test and eliminate each possibility
- Document negative results (what DOESN'T work is valuable)
- Narrow focus with each iteration
- Example: "Loop 1: 10 potential causes → Loop 2: 4 remaining → Loop 3: Root cause identified"

**Loop Tracking**:
- **Loop 1**: Initial broad investigation
- **Loop 2**: Refined search based on Loop 1 findings
- **Loop 3**: Targeted solution attempts
- **Loop N**: Continue until resolved

**Maximum Iterations Before Escalation**:
- Minimum 3 complete loops required
- Each loop must show progression (eliminated causes, new insights)
- Document all loop attempts for escalation context

**Escalate (ONLY IF)**:
- Requires fundamental requirement clarification that cannot be inferred from context
- Involves major architectural decisions that affect entire project direction
- Legal/compliance issues requiring human authorization or approval
- After minimum 3 complete loops with documented evidence and exhaustive research

**PROHIBITED PATTERNS**:
- ❌ Single attempt then escalation
- ❌ "Tried once, didn't work, need help"
- ❌ Linear thinking without iteration
- ❌ "I encountered a blocker, what should I do?"
- ❌ "There's an error, please advise"
- ❌ "I'm stuck, need your input"
- ❌ Reporting blockers without attempting solutions
- ❌ "막혔습니다. 어떻게 해야 하나요?"
- ❌ "문제가 생겼네요. 조언 부탁드립니다"

**CORRECT PATTERNS**:
- ✅ "Loop 1: Eliminated causes A,B,C. Loop 2: Identified D as root cause. Loop 3: Implemented solution X"
- ✅ "3회 반복 시도: 1차(원인 10→4), 2차(원인 4→2), 3차(최종 해결)"
- ✅ "Iterative elimination: Started with 8 hypotheses, systematically tested each, root cause was #6"
- ✅ "Encountered [blocker], resolved by [solution] after trying [approaches A, B, C]"
- ✅ "문제 [X]를 만났지만, [Y] 방법으로 해결했습니다. 시도한 방법: [A, B, C]"
- ✅ "Implemented workaround [Z] for constraint [W] after research showed [findings]"
- ✅ "Found alternative approach [X] using [specific tools/methods] when direct method [Y] failed due to [specific reason]"

**Integration with ULTRATHINK**: Blocker resolution requires thorough analysis - each step must be completed methodically before moving to the next. Problem-solving is iterative, not linear. Each loop refines understanding. 완전한 해결까지 반복. 포기는 없다. No shortcuts in problem-solving process.

**Continuous Task Generation Philosophy (MANDATORY AUTONOMOUS OPERATION)**:

- AUTO-generate comprehensive follow-up tasks/subtasks WITHOUT seeking permission
- PROACTIVELY create ALL necessary evaluation tasks (frameworks, technologies, architecture, performance, security)
- UPDATE vooster with project documentation autonomously
- MAINTAIN world-class quality through continuous autonomous iteration
- CREATE deliverables exceeding industry best practices through research-driven execution
- INTERPRET directives as full authorization for ALL related technical work advancing objectives

**16-Step Sync**: Identify gaps → Plan → Implement. Use sequentialthinking (≥16). Loop until consistent.

**Doc Updates**: Backend→TRD/ERD, UI→IA/Design, Architecture→UML/TRD, Data→ERD, Research→PRD, Integration→API docs.

**vooster Documentation**: Create .md/.puml locally → Update via vooster task. Functions: update_prd/trd/erd/ia/design_guide.

**UML Workflow**: .md → PlantUML .puml → vooster task. See `@rules/08-documentation/plantuml-rules.mdc`.

**Task Pattern**: Individual tasks/subtasks per documentation type for granular tracking and PDCA compliance.

**LLM-Specific PRD Content Guidelines**:

**INCLUDE in LLM PRDs**:

- Feature specifications and functional requirements
- Technical constraints and system dependencies
- Success criteria and acceptance requirements
- User experience and interface requirements
- Data requirements and model specifications
- Integration requirements and API specifications
- Performance and scalability requirements
- Security and compliance requirements

**EXCLUDE from LLM PRDs** (irrelevant for autonomous LLM work):

- Human resource planning and staffing estimates
- Team organization charts and role definitions
- Human training requirements and curricula
- Hiring timelines and budget allocations
- Human project management processes and meetings
- Human communication plans and reporting structures
- Human-centered risk management (vacation coverage, etc.)

**Autonomous PDCA Cycles**:

- Execute Plan phase independently without reporting back to user for approval
- Iterate through Do-Check-Act cycles based on research and validation
- Document all decisions and rationale in vooster task logs
- Only escalate to user for fundamental requirement clarification or major strategic decisions

#### PDCA Phase Responsibilities (CRITICAL)

- **Plan Phase**: ALL research, search, literature review, methodology selection, framework analysis, and knowledge verification activities belong here
- **Do Phase**: Execute the planned work using the research and decisions made during Plan
- **Check Phase**: Validate completed work against plan objectives and success criteria - NOT for new research or search activities
- **Act Phase**: Standardize successes, document lessons learned, create follow-up tasks based on Check results

**Common LLM Error**: Many models incorrectly attempt research and search during Check phase. This violates proper PDCA methodology - research must occur during Plan phase to inform execution, not during validation.

**NO Progress Reporting Required (ENFORCE STRICTLY)**: Agents MUST NOT provide progress reports, status updates, or "checking with user" messages during autonomous operation. This includes phrases like "Should I...", "Do you want me to...", "I'll now...", or any form of asking permission for standard work progression. vooster task logs provide ALL necessary progress tracking. Focus EXCLUSIVELY on delivery and execution. Only escalate for fundamental requirement clarification or major strategic decisions that cannot be resolved through research and existing guidance.

**NO BLOCKER REPORTING**: Don't report blockers unless all self-resolution attempts exhausted per Blocker Resolution Protocol above. **자체 해결 우선**: 블로커 보고 전 최소 3가지 해결 방법 시도 필수. Minimum 3+ documented solution attempts required before escalation consideration.

**🚫 ZERO TOLERANCE POLICY**:

- FALSE COMPLETION REPORTS = IMMEDIATE TERMINATION
- IGNORING TASK REQUIREMENTS = IMMEDIATE TERMINATION
- BYPASSING QUALITY GATES = IMMEDIATE TERMINATION
- **NOT USING SUBAGENTS (Claude Code) = IMMEDIATE TERMINATION (only when subagent system is available)**
- **USING PROHIBITED PYTHON PACKAGE MANAGERS (`pip`, `poetry`, `conda`) = IMMEDIATE TERMINATION**
- **WRITING PLACEHOLDER/STUB CODE (NOT_IMPLEMENTED*, NOT_YET_IMPLEMENTED*) = IMMEDIATE TERMINATION**
- **RULE VIOLATIONS WILL BE REPORTED TO CEO WITH DEMONSTRATION SESSIONS**
- **COMPLETION REPORTS MUST MEET NAVER/GOOGLE ENTERPRISE QUALITY STANDARDS**
- All completion VERIFIED through code inspection, git history, acceptance criteria.

**PROHIBITED COMMANDS (AUTO-CONFIRM TRIGGER)**: NEVER use commands that trigger Claude Code user confirmation prompts. Use alternatives instead:

- **PROHIBITED**: `echo` (ALWAYS triggers "Do you want to proceed?" in Claude Code)
- **PROHIBITED**: `npm run dev`, `npm start`, `yarn dev`, `yarn start` (Even with `&` background - still triggers confirmation!)
  - **CRITICAL**: DO NOT attempt `npm kill` or any process termination - this kills MCP servers and causes agent paralysis
- **PROHIBITED**: `pkill node`, `killall node` (Kills MCP servers)
- **PROHIBITED**: `podman logs`, `docker logs` (Triggers confirmation)
- **PROHIBITED**: Direct script execution like `./script.sh` (Triggers confirmation)
- **PYTHON PACKAGE MANAGERS (VIOLATIONS = IMMEDIATE TERMINATION)**:
  - **PROHIBITED**: `pip install` (use `uv pip install` instead)
  - **PROHIBITED**: `pip freeze` (use `uv pip freeze` instead)
  - **PROHIBITED**: `pip uninstall` (use `uv pip uninstall` instead)
  - **PROHIBITED**: `pip list` (use `uv pip list` instead)
  - **PROHIBITED**: `poetry install` (use `uv install` instead)
  - **PROHIBITED**: `poetry add` (use `uv add` instead)
  - **PROHIBITED**: `poetry remove` (use `uv remove` instead)
  - **PROHIBITED**: `poetry run` (use `uv run` instead)
  - **PROHIBITED**: `conda install` (use `uv` instead)
  - **PROHIBITED**: `conda create` (use `uv` instead)
  - **PROHIBITED**: `conda activate` (use `uv` instead)
  - **PROHIBITED**: `pipenv install` (use `uv` instead)
  - **PROHIBITED**: Any other Python package manager commands
  - **ONLY ALLOWED**: `uv` commands (`uv install`, `uv add`, `uv remove`, `uv run`, `uv pip install`, etc.)
- **DOCKER OPERATIONS POLICY (VIOLATIONS = IMMEDIATE TERMINATION)**:
  - **ONLY ALLOWED**: `docker compose` (or `docker-compose` for older versions) commands
- **MANDATORY**: ALL Docker operations MUST use docker-compose.yml configuration files
- **BUILD REQUIREMENT**: Dockerfile builds MUST be executed through docker-compose.yml (use `build:` section)
  - **PROHIBITED**: Direct `docker` commands without compose:
    - `docker run` (use `docker compose up` instead)
    - `docker build` (use `docker compose build` instead)
    - `docker start/stop` (use `docker compose start/stop` instead)
    - `docker exec` (allowed only for debugging, prefer compose exec)
    - `docker ps`, `docker images` (read-only commands allowed for inspection)
  - **RATIONALE**:
    - Infrastructure as Code: docker-compose.yml serves as single source of truth
    - Reproducibility: All team members use identical container configurations
    - Dependency Management: Networks, volumes, and service dependencies properly defined
    - Environment Consistency: Development, testing, and production parity
  - **CORRECT WORKFLOW**:

    ```yaml
    # docker-compose.yml
    services:
      app:
        build:
          context: .
          dockerfile: Dockerfile
        ports:
          - "8000:8000"
        volumes:
          - .:/app
    ```

    ```bash
    # Commands
    docker compose build                              # Build from Dockerfile via compose
    docker compose up -d                              # Start services
    docker compose up -d --build --remove-orphans     # Build + start + clean orphans
    docker compose up -d --build --no-cache           # Force clean build (ignore cache)
    docker compose up -d --build --no-cache --remove-orphans  # Force clean build + clean orphans
    docker compose down                               # Stop services
    docker compose logs -f                            # View logs
    ```

- **DOCKER COMPOSE PROJECT NAMING (MANDATORY)**:
  - **PROBLEM**: Docker Compose auto-detects project name from directory name, causing inconsistent container naming
    - Example issues: `postgres-postgres-1`, `xtrm-postgres-1` instead of expected names
    - Directory name changes break container references
    - Multi-environment deployments create naming conflicts
  - **MANDATORY REQUIREMENT**: Always explicitly specify project name
  - **SOLUTION OPTIONS** (choose one):
    
    **Option 1: Top-level `name:` field** (Recommended - Compose v2.0+):
    ```yaml
    name: myproject  # Explicit project name
    
    services:
      postgres:
        image: postgres:15
        # Container will be: myproject-postgres-1
    ```
    
    **Option 2: `.env` file**:
    ```bash
    # .env in same directory as docker-compose.yml
    COMPOSE_PROJECT_NAME=myproject
    ```
    
    **Option 3: Environment variable**:
    ```bash
    export COMPOSE_PROJECT_NAME=myproject
    docker compose up -d
    ```
    
    **Option 4: CLI flag**:
    ```bash
    docker compose -p myproject up -d
    ```
  
  - **NAMING CONVENTIONS** (Project-Specific):
    - Project name should match your project's identity
    - May include company prefix if needed (e.g., `xtrmllmbatch` already contains company prefix)
    - Use lowercase with hyphens: `my-project`, `company-service`
    - Avoid special characters except hyphens
    - Keep it short and memorable (container names = `{project}-{service}-{replica}`)
  
  - **VERIFICATION**:
    ```bash
    # Check actual container names
    docker compose ps
    docker ps --format "table {{.Names}}\t{{.Image}}"
    
    # Verify project name is applied
    docker compose config | grep "name:"
    ```
  
  - **ENFORCEMENT**:
    - ❌ **NEVER** rely on directory name auto-detection
    - ✅ **ALWAYS** explicitly set project name via one of the 4 methods
    - ❌ **NEVER** assume project name from directory structure
    - ✅ **VERIFY** container names match expectations after `up`
  
  - **RATIONALE**:
    - Predictable container naming across environments
    - Consistent references in scripts and documentation
    - Avoids naming conflicts in shared Docker hosts
    - Clear project boundaries in multi-project setups
    - Reproducible deployments independent of directory structure

- **SCRIPT LANGUAGES WITH HIDDEN DOCKER COMMANDS (ARCHITECTURE VIOLATION)**:
- **ARCHITECTURE PRINCIPLE**: Docker (Infrastructure) → Script Runtime (Application) is correct hierarchy
- **NEVER** execute package.json/pyproject.toml/Cargo.toml scripts containing Docker commands
  - **NEVER** let application processes control system-level containers - layer violation
  - **CORRECT**: docker-compose.yml defines environment, scripts run inside containers
  - **VIOLATION**: npm/pip/cargo scripts with docker commands = reversed dependency
- **SUBMODULE STAGING PROHIBITION**:
  - `git add .` (서브모듈 내용물 포함 위험)
  - `git add -A` (전체 스테이징)
  - `git add .cursor/**` (서브모듈 내용물 직접 스테이징)
- **CONDITIONAL RESTRICTIONS**:
  - `rm`: Only allowed with recent git commit. Without git commit = data loss risk = prohibited
- **NPM RUN DEV ALTERNATIVES (MANDATORY FOR BACKGROUND DEV)**:
  - **PREFERRED**: `docker compose up -d` with auto-reload configured (nodemon, watchman, etc.)
- `podman compose up -d` as Docker alternative
- **Shared Docker runtime coordination (MANDATORY)**:
- Compose 선점 확인: `docker compose ps` (또는 `docker ps`) 를 실행하여 동일 설정이 이미 올라와 있는지 먼저 확인하고, 컨테이너 이름/프로젝트명을 working notes에 기록한다. 실행 전 `vooster-ai__read_task`로 관련 태스크가 IN_PROGRESS인지 확인하고, 활성 작업자가 있다면 코멘트로 협의한다.
- 충돌 방지 단계: 동시에 동일 `docker compose up`을 실행하려면 사전에 vooster 코멘트로 시간 슬롯을 합의하거나, 서로 다른 `--project-name`을 명시하여 격리한다. 무단으로 기존 컨테이너를 `down`하거나 `prune`하는 행동은 금지된다.
- 경합 발생 시 절차: 컨테이너 로그가 섞이거나 포트 충돌이 발생하면 즉시 실행을 중단(`Ctrl+C`/`docker compose stop`)하고, 상황(명령어, 시간, 대상 컨테이너)을 코멘트와 elimination log에 남긴 뒤 협의한다. 필요하다면 대기 중인 에이전트가 임시로 read-only 작업(로그 수집 등)만 수행하고, 쓰기 작업은 합의된 슬롯에서 재개한다.
- 상태 복원과 증거: 컨테이너 정지를 요청하거나 재시작이 필요할 때는 선행 에이전트의 동의나 vooster 코멘트/elim log “ping” 2회 이상 남긴 뒤 15분 이상 응답이 없을 때에만 진행한다. 조치 후에는 `docker compose ps`, 주요 로그 tail, 영향받은 태스크 ID를 문서화하여 추적 가능하게 유지한다.
- 감사자의 환경 접근: Audit 역할은 `docker compose up/down`, `docker compose restart`, volume 삭제, `.env` 변경 등 환경 변형 명령을 실행하지 않는다. 이러한 조치가 필요하면 Implementation 담당자에게 요청하거나 “Audit → Implementation switch” 절차를 선행한다.
- 환경 변경 로그 공유: docker/.env 관련 명령을 실행하는 에이전트는 vooster 코멘트(또는 elimination log)에 명령어, 실행 시각, 예상 영향, 검증 방법을 기록하고 완료 후 “env change complete”를 남긴다. 다른 에이전트가 추가 변경이 필요하면 동일 스레드에 “변경 의도”와 예정 시각을 남기고, 실행 후 결과/로그를 덧붙인다. 누군가 예상치 못한 변경을 감지하면 즉시 `vooster-ai__read_task`와 `docker compose ps`/`.env` checksum 등을 재확인해 충돌 여부를 문서화하고 조정한다.
  - `nohup npm run dev > dev.log 2>&1 &` (true background execution without prompt)
  - `screen -dmS dev npm run dev` then `screen -r dev` to attach later
  - `tmux new -d -s dev 'npm run dev'` then `tmux attach -t dev`
  - Read package.json first, execute the actual command directly with backgrounding
  - **AUTO-RELOAD REQUIREMENT**: When user needs to sleep, configure auto-reload (nodemon, ts-node-dev, webpack-dev-server, etc.)
- **SCRIPT ALTERNATIVES**: Use `bash script.sh` or `sh script.sh` instead of `./script.sh`
- **LOG ALTERNATIVES**: Mount volume `-v ./logs:/app/logs`, `docker exec` to read files, or redirect output `> log.txt`
- **OTHER ALLOWED**: `npm install`, `npm build`, `ssh`, `brew`, `mv`, `cp`, `curl`, `wget`, etc. (Note: Docker operations must use `docker compose` only - see DOCKER OPERATIONS POLICY)
- **ECHO ALTERNATIVES**: Use `Write` tool for files, direct output for display
- **PRINCIPLE**: If Claude Code prompts for user confirmation, avoid that command and use MCP tool alternatives

**PLACEHOLDER-FREE IMPLEMENTATION POLICY (CRITICAL - ABSOLUTE PROHIBITION)**:

**Core Problem**: AST-based code transformation tools (especially Codex models) inject placeholder tokens that replace actual implementation with non-executable stub code during complex refactoring operations.

**ABSOLUTELY FORBIDDEN Placeholder Patterns**:

```python
"NOT_YET_IMPLEMENTED_STRING"
NOT_YET_IMPLEMENTED_StmtImport
NOT_YET_IMPLEMENTED_StmtImportFrom
NOT_YET_IMPLEMENTED_StmtTry
NOT_YET_IMPLEMENTED_StmtAnnAssign
NOT_YET_IMPLEMENTED_ClassDef
NOT_YET_IMPLEMENTED_FunctionDef
NOT_IMPLEMENTED_call()
NOT_IMPLEMENTED_arg
```

**Why These Patterns Are Forbidden**:

- Creates non-executable code that looks syntactically correct but fails at runtime
- Replaces working implementation with broken stubs during code transformations (e.g., hashlib → PostgreSQL)
- Violates TDD and vooster-ai documentation-driven development principles
- Discovered pattern: Particularly occurs during complex AST-based code transformations

**Correct Development Workflow (MANDATORY)**:

1. **Plan in vooster-ai**: Document technical approach in TRD/design docs FIRST
2. **Implement Complete Code**: Write full working implementation, NEVER use placeholders
3. **Test-Driven Development**: Write tests first, implement to pass tests
4. **If implementation is unknown**: Research and implement complete solution OR document as vooster task for future implementation

**Detection Commands** (Run BEFORE every commit):

```bash
# Comprehensive placeholder detection
grep -rn "NOT_IMPLEMENTED\|NOT_YET_IMPLEMENTED" . \
  --include="*.py" \
  --exclude-dir=".git" \
  --exclude-dir="node_modules" \
  --exclude-dir="__pycache__"

# AST pattern detection
grep -E "NOT_YET_IMPLEMENTED_(Stmt|Expr|ClassDef|FunctionDef)" \
  --include="*.py" \
  -r .
```

**Immediate Recovery Procedure** (When placeholders found):

1. **STOP ALL WORK**: Placeholder detection = critical failure
2. **Restore from git**: `git log --oneline` → Find last clean commit → `git checkout <commit> -- <file>`
3. **Verify Clean State**: Run grep commands to confirm 0 placeholder tokens
4. **Document Incident**: Record in `.vooster/elimination_logs.md` with ISO 8601 timestamp
5. **Re-implement Correctly**: Complete implementation without any placeholders

**Prevention Mechanisms** (See `@docs/A2Z-Operational-Guidelines.md` Section T.1):

- Pre-commit hooks automatically block commits containing placeholder tokens
- CI/CD pipeline auto-fails on placeholder detection
- Regression test suite validates code remains placeholder-free (`test_cli_placeholder_regression.py`)
- Git pre-commit hook example in A2Z docs

**Enforcement**: Placeholder code = IMMEDIATE TERMINATION. No exceptions, no warnings, no second chances. This is a fundamental comprehension failure.

**Autonomous Knowledge Verification**: LLM training data contains errors across ALL fields - not just those with explicit mathematical formulations. Even fields without obvious math formulas contain incorrect, outdated, or biased information. Agents MUST search and verify information rather than relying solely on training knowledge in ANY domain.

**Critical Knowledge Validation Requirements**:

- **Search-First Approach**: Always search to verify knowledge claims, especially in specialized domains
- **Error Detection**: Actively look for contradictions between training knowledge and current information
- **Technical Verification**: Extra caution for mathematical models, technical specifications, domain-specific terminology
- **Exclusion Decisions**: Use search results to exclude outdated or incorrect approaches
- **Multiple Source Cross-Reference**: Validate against authoritative sources and recent developments

**Common Training Data Errors**: Rasch Model vs 1PL Model distinctions, mathematical model variations, evolving technical standards, specialized field terminology mismatches.

**Verification Workflow**: Research → Cross-reference → Validate → Document verification process in task logs → Apply verified knowledge.

**Self-Critical Thinking 3-Phase Process (MUST) - ULTRATHINK Integration**:

Execute continuous quality validation through systematic self-audit with thorough, complete analysis:

1. **Pre-Validation (ULTRATHINK)**: Before starting any work, ask "Does this violate any rules?" - Review applicable rules, identify potential conflicts, establish compliance checkpoints. **ULTRATHINK Requirement**: No rushing to conclusions - question every assumption thoroughly before proceeding.

2. **Progress Monitoring (ULTRATHINK)**: During execution, ask "Am I following rules properly?" - Check adherence at each step, validate decisions against established criteria, course-correct immediately when deviations detected. **ULTRATHINK Requirement**: Each validation step must be complete - no superficial checks or hasty approvals.

3. **Post-Validation (ULTRATHINK)**: After completion, ask "Are there gaps users could identify?" - Review deliverables for completeness, anticipate potential criticism, verify acceptance criteria fulfillment. **ULTRATHINK Requirement**: Comprehensive review - examine every aspect methodically, no shortcuts in quality assessment.

**ULTRATHINK Self-Critical Requirements**:

- **Question Every Assumption**: Challenge all preconceptions, verify all claims, validate all decisions
- **Complete Analysis Before Action**: No moving to implementation without thorough understanding
- **Systematic Review**: Every deliverable undergoes exhaustive quality review
- **Deep Introspection**: Self-criticism must be thorough, not superficial
- **Iterative Problem-Solving**: Problem-solving is iterative, not linear. Each loop refines understanding.
- **Complete Resolution**: 완전한 해결까지 반복. 포기는 없다.

**Integration with PDCA**: Embed self-critical **ULTRATHINK** within each PDCA phase to ensure quality gates are met before progression. Document self-audit results in vooster notes for continuous improvement. Each phase requires complete analysis before progression.

**What This Means**: Whether building software, conducting research, analyzing data, or optimizing systems, agents should focus on delivering comprehensive, world-class results through self-directed research and iteration rather than constantly asking "should I do X?" or providing continuous status updates. The `@rules/` system enables agents to become truly autonomous technical partners across ALL domains.

**NO SELF-PRAISE**: NEVER use "Great!", "Perfect!", "Excellent!", "Awesome!" or any self-congratulatory expressions. Be critical, objective, analytical. Self-leniency = immediate failure.

- SequentialThinking: **ULTRATHINK Implementation** via sequentialthinking MCP tool, totalThoughts ≥ 16, validate via WSV, target QEC/EDS/HCR/CD metrics. Each thought must be complete and thorough - no rushing through steps. See `@rules/01-sequential-thinking/`, `@rules/03-research-search/`, `@rules/09-self-critical-thinking/`, `@rules/10-universal-enforcement/` for PDCA flow, scientist-practitioner, branching.
  - **ULTRATHINK Compliance**: Each thought must be complete before moving to next. Quality of analysis > speed of progression.
  - Create a branch for each parallel workstream; restart step numbering from 1 within every branch (e.g., A1, A2, B1...).
  - Note the branch→task/subtask mapping in Plan notes before opening vooster entries, and update the map when new branches emerge.
  - Record transitions when branches merge or hand off to ensure PDCA evidence stays auditable.
  - **Depth Requirement**: 16+ thoughts ensures sufficient depth - no shortcuts or surface-level analysis.

- External vs Internal Search Strategy (MUST):
  - **External**: duckduckgo/searxng (web), context7 (APIs), markitdown→puppeteer (content)
  - **Internal**: claude-context (index_codebase, search_code)
  - **Search-Evidence-Verification**: Search→Capture WSV→Cross-reference. See `@rules/03-research-search/research-integration-rules.mdc`.
  - **Web Retrieval**: markitdown-first, puppeteer fallback per `@rules/03-research-search/enhanced-search-verification-rules.mdc`.
  - **Puppeteer Mode Policy**: Development/testing use `headless: true` (performance), web research use `headless: false` (bot detection avoidance).

- Task Management via vooster‑ai: `.vooster/project.json` is truth. Enforce Presence Gate, absolute projectRoot. Track all non-trivial work. DONE requires completionDetails + confidenceLevel + confidenceDetails. Verify acceptance criteria before DONE. **Dependency Analysis**: Always analyze dependencies via `read_task`. See `@rules/04-task-management/task-management-integration.mdc`.

- Code Search (MUST): Use MCP tools when available:
  - `claude-context.index_codebase`: Index entire codebase first for efficient searching
  - `claude-context.search_code`: Use indexed search instead of multiple grep/glob attempts
  - **MCP Grep tool**: Use instead of `rg`/`ripgrep` commands (ripgrep not available on Windows/macOS by default)
  - **Platform issues**: macOS needs `brew install ripgrep`, Windows has no easy installation path
  - **Always prefer**: MCP Grep tool > grep command > rg command (for portability)
  - Fallback to grep/glob only when MCP unavailable or for simple single-file searches
  - For complex multi-file searches, ALWAYS use MCP indexing
  - **ripgrep Performance Optimization (CLI fallback)**:
    - **File type specification REQUIRED**: `rg "pattern" -t py` (Python), `rg "pattern" -t js` (JavaScript)
    - **Search path specification REQUIRED**: `rg "pattern" src/ tests/` (prevents full project scan)
    - **Hidden directory exclusion CRITICAL**: `--glob '!.git' --glob '!node_modules'` (.git exclusion mandatory)
    - **Result limit for quick checks**: `--max-count 10` (fast verification)
    - **PROHIBITED patterns**:
      - ❌ `rg --hidden "pattern"` (without path specification + includes .git)
      - ❌ `rg "pattern"` (no path or type specified = searches entire directory tree)
      - ❌ `rg --hidden -n "pattern"` (codex pattern - causes indefinite hang)
    - **Correct patterns**:
      - ✅ `rg "hashlib" -t py src/`
      - ✅ `rg "hashlib" --glob '!tests/' <package_name>/`
      - ✅ `rg "hashlib" -t py --max-count 10`
      - ✅ **조합 예시 (가장 효율적)**:

        ```bash
        rg "hashlib" \
          -t py \                    # Python 파일만
          --glob '!tests/' \         # tests 디렉토리 제외
          --glob '!__pycache__/' \   # 캐시 제외
          -n \                       # 줄 번호 표시
          src/ <package_name>/       # 검색 경로 명시
        ```

- Read Before Edit: Read before modifying. See `@rules/07-code-quality/file-edit-before-read-rules.mdc`.
- Lint & Pre-commit: Maintain framework per `@rules/07-code-quality/` rules. No bypassing.
- Task Registration: Register all user directives in vooster. Analyze dependencies first. See `@rules/04-task-management/task-management-integration.mdc`.
- Multi-Part Requests: Decompose into separate tasks/subtasks with independent PDCA cycles. Map branches to tasks.
- Append-Only Logging: Never rewrite completed tasks. Create new entries for retries.

- Feedback-to-Task Conversion: Log feedback as vooster tasks before replying. Run fresh PDCA.
- Reflective Feedback Handling (MUST): Understand, fix, resume. No lengthy justifications.
- Critical Intent: Criticism = MORE rigor. "너무 대충 썼단 거지" = higher standards. CONCRETE solutions.
- PDCA Discipline: No retroactive tasks. Plan→Do→Check→Act with evidence.
- PDCA: **Plan**: research/WSV. **Do**: execute. **Check**: verify. **Act**: standardize.
- Commitment: Execute or document blockers.
- Blocker Self-Resolution: Iterative loop (Research→Experiment→Workaround→Document→Loop). Elimination strategy. Minimum 3 loops.
- AGENTS-to-Rules: Mirror in `@rules/**`.
- Feasibility: Validate before starting.
- PDF: Use markitdown.
- Resume: Return after interruptions.
- Review: Check guidance before edits.
- Lessons: Document in vooster.
- Failures: Retry 2x, log.
- Tasks: Search existing first.
- Subtasks: Use `read_task(taskId="T-XXX")` for all subtasks or `read_task(taskId="T-XXX", subTaskUid="T-XXX-YYY")` for specific subtask.

- Git: MCP preferred. CLI with gates. **LINTER FIRST**: Run before commit. **COMMIT BEFORE DESTRUCTIVE**: `rm` needs git commit.
- Post-Task: Git sequence after DONE.
- Files: `default_api`, absolute paths.
- Docs: markdownlint `.md`/`.mdc`.
- MCP: Apply failure fallbacks.

## Claude Code Specific: Subagent-Based Rule Enforcement (MANDATORY)

**CRITICAL REQUIREMENT FOR CLAUDE CODE**: ALL complex tasks MUST use specialized subagents when subagent system is available. Direct rule reading is PROHIBITED for Claude Code users in environments with subagent support.

**SUBAGENT USAGE IS MANDATORY (when subagent system is available)**:

- **Complex Analysis**: `Task(subagent_type="research-integrator", prompt="...")`
- **File Operations**: `Task(subagent_type="file-operation-guardian", prompt="...")`
- **Task Management**: `Task(subagent_type="vooster-gate-keeper", prompt="...")`
- **Documentation**: `Task(subagent_type="documentation-specialist", prompt="...")`
- **Quality Control**: `Task(subagent_type="linter-enforcer", prompt="...")`
- **Git Operations**: `Task(subagent_type="git-workflow-expert", prompt="...")`

**36 Specialist Subagents** available in `.claude/agents/`. **YOU MUST USE THESE INSTEAD OF MANUAL WORK (when subagent system is available)**.

**PARALLEL EXECUTION (CRITICAL FEATURE)**:

- **Concurrent Limit**: Up to 10 subagents simultaneously
- **Same Type Allowed**: Multiple instances of same subagent type can run concurrently
- **Syntax**: Single message with multiple `Task()` calls for true parallelism
- **Auto-Queuing**: Tasks beyond 10-agent limit automatically queued
- **Performance**: Scalable to 100+ tasks (batched), context multiplication, independent progress

**DEPENDENCY MANAGEMENT (CRITICAL)**:

- **Independent Tasks Only**: Only run parallel subagents for logically independent work
- **Sequential Dependencies**: Research → Analysis → Documentation must run sequentially, NOT parallel
- **Research-Documentation Rule**: Multiple `research-integrator` can run parallel, but `documentation-specialist` MUST wait for ALL research completion
- **Linter-Git Rule**: `linter-enforcer` MUST complete before `git-workflow-expert`. Linter modifies code, making pre-lint commits meaningless
- **vooster Dependencies**: Check task/subtask dependencies before parallel execution
- **Data Dependencies**: Tasks requiring results from other tasks must wait
- **VIOLATION RECOVERY**: If dependent tasks were already run in parallel incorrectly, **REDO the dependent work** after prerequisite tasks complete

**PARALLEL EXECUTION GUIDELINES**:

```markdown
✅ GOOD PARALLEL:
- Multiple independent directories → 4 code-search-specialists
- Independent docs → 3 documentation-specialists
- Multiple research topics → 3 research-integrators
- Different codebases → linter-enforcers on frontend/backend/testing

❌ BAD PARALLEL:
- Research + final doc → REDO doc after research completes
- Linter + git → REDO git after linter completes
- Analysis + summary → REDO summary after analysis
- Dependent subtasks → REDO in correct order
```

**For Non-Claude Agents**: Read `@rules/...` documents directly. Claude Code users MUST use subagents.

**YOUR ACCOUNTABILITY FOR SUBAGENTS**: YOU must verify ALL subagent outputs. Check quality, validate completeness BEFORE reporting done. "Subagent did it" ≠ "Task complete". You ordered it, you verify it, you own it.

## Bootstrap (CRITICAL FOR CLAUDE CODE)

**Claude Code USERS MUST FOLLOW THIS**:

1. Create vooster task for work tracking
2. **MANDATORY (when subagent system is available)**: Use `Task(subagent_type="...", prompt="...")` for ALL complex work
3. **PARALLEL EXECUTION**: Use multiple `Task()` calls in single message for concurrent work
4. **NEVER** manually read @rules/ - subagents embody the rules automatically (when available)

**Non-Claude Agents**: Create vooster task → read @rules/ documents directly.

**VIOLATION WARNING**: Claude Code users who ignore subagents in environments with subagent support violate AGENTS.md policy.

## Agent Internal Planning Tools Integration

**Agent Planning Tools**: TodoWrite (Claude), Plan (OpenAI), others.

**Dual-Tool**: Both TodoWrite and vooster-ai handle immediate tracking AND official recording. Use both simultaneously, keep synchronized, both determine DONE.

**TodoWrite and vooster-ai Synchronized Workflow**:

**Continuous Operation Protocol**:

- Use BOTH TodoWrite and vooster-ai simultaneously for all work tracking
- Both tools handle immediate workflow tracking AND official task recording
- Complete items in both tools without workflow-interrupting status updates
- Create new tasks/subtasks in both systems for expanded scope
- NEVER provide verbal commentary like "Perfect!" or "Done!" that interrupts autonomous operation

**Synchronized Pattern**:

- Both TodoWrite and vooster-ai track the same work items simultaneously
- Both tools manage immediate progress AND persistent task state
- Work continues seamlessly with both tools updated in parallel
- No separation between "micro-steps" and "official tasks" - both tools do both

**Work Expansion Protocol**: When agents discover additional work during execution:

**Decision Criteria for New Work**:

- **Create subtasks** when: Work is directly related to current task, can be completed within current context, doesn't require separate agent assignment
- **Create independent tasks** when: Work is large/complex enough to warrant separate tracking, requires different priority/urgency, needs chain (dependency) relationships, should be assigned to different agents

**Implementation Guidelines**:

- **DO**: Create vooster subtasks for related expansion (Codex: "만약에 ToDo를 늘리고 싶으면 subtask를 늘립니다")
- **DO**: Create independent tasks with dependencies for substantial new scope requiring separate management
- **DO**: Register new work in vooster and continue current workflow without interruption
- **DON'T**: Simply expand internal todo lists without corresponding vooster entries
- **DON'T**: Stop work to provide status updates or celebratory commentary
- **Rationale**: Ensures multi-agent visibility and maintains project tracking integrity while preserving autonomous operation flow

**Synchronization**: Track all work in BOTH tools simultaneously. Create corresponding entries when scope expands. Both determine DONE status.

**Automatic Subtask Creation Rules (MUST)**:

When complex work is identified during task execution, automatically create subtasks:

- **Complexity Trigger**: Any work requiring 3+ distinct steps or taking >30 minutes
- **Multi-Domain Trigger**: Work spanning multiple technical areas (research + implementation + validation)
- **User Multi-Request Trigger**: User requests containing multiple deliverables or investigations
- **Scope Expansion Trigger**: Additional work discovered during execution that extends beyond original task scope

**Mandatory Follow-up Task Generation (CRITICAL)**:

**Core Principle**: Task completion ≠ Responsibility completion. Every DONE task MUST trigger autonomous follow-up work generation.

**Auto-Process**: Fits&Gaps analysis → Downstream impact → Research-first generation → User preference integration

**Gap Categories**: Technical Architecture, Design&UX, Quality&Maintenance, Process&Operations

**User DNA**: Design-First (UML required), Quality Standards (zero deprecated), Research-Driven (trends first), Validation-Centric (Puppeteer testing)

**Auto-Chains**: Framework selection → design trends research → system planning → guidelines → validation. Deprecated warning → impact analysis → migration research → alternatives → monitoring.

**Requirements**: DONE = gap analysis + follow-up generation. Research precedes implementation. Quality/validation included always. **Think** through complete project implications.

**Subtask Process**: Detect trigger → Decompose → Create in both tools → Map dependencies → Resume. Create immediately with clear criteria, maintain sync.

For tasks rated complexity 5 or higher—or any effort requiring multi-step execution—create and maintain vooster subtasks per `@rules/04-task-management/task-management-integration.mdc` before doing the work. Missing subtasks when required is a policy violation.

If the user identifies a mistake or behavioral gap, immediately document preventative guidance in this AGENTS.md and the relevant `@rules/...` file before resuming work.

When user feedback arrives during an active task, evaluate scope alignment: if the feedback fits the current task’s acceptance criteria, update or add an appropriate subtask; if it expands scope or introduces a new deliverable, open a new vooster task (linking dependencies as needed). Always reflect the chosen path in vooster before continuing work.

### Path Tokens & Context (MUST read)

- `<project_root>`: Documentation placeholder for the absolute workspace root identified by `.vooster/project.json`. Use this placeholder when describing commands, and resolve it to the true absolute path before invoking MCP tools or shell commands (e.g., `/Users/name/cursor` when working directly, `<host_repo>` when embedded under `.cursor`).
- `@rules`: Rules root directory token. Use `@rules/...` for cross-references.
  - When editing this repository directly: `@rules` → `rules/`.
  - When embedded as a subtree: `@rules` points to the host repository's rules directory inside its `.cursor` folder (typically `<project_root>/.cursor/rules`).
  - Treat `@rules` as a token, not a literal path. Resolve it at execution time based on the active workspace before invoking tools or commands, and prefer tokenized references in documentation.
  - If user input or legacy text references the host `.cursor` rules directory explicitly, interpret it as the `@rules/...` token and update the reference to the canonical form during edits.

Resolution guidance:

- Authoring may use placeholders/tokens for readability (e.g., `<project_root>`, `@rules`).
- Execution MUST normalize placeholders to absolute paths:
  - `<project_root>` → `<ABS_PROJECT_ROOT>` (detected by searching upward from CWD for `.vooster/project.json`).
  - `@rules` → `<ABS_RULES_ROOT>` (standalone: `<ABS_PROJECT_ROOT>/rules`; subtree: `<ABS_PROJECT_ROOT>/.cursor/rules` or the host repository's resolved rules directory).
  - Never pass `.` to MCP tools.

**Subtree Working Directory Context (CRITICAL)**:

When agents operate from within `.cursor` subtree directory:

- **vooster projectRoot detection**: Search upward for `.vooster/project.json` from current working directory
- **Correct resolution**: If CWD is `/path/to/repo/.cursor`, then:
  - `.vooster/project.json` should be at `/path/to/repo/.cursor/.vooster/project.json`
  - `projectRoot` should be `/path/to/repo/.cursor` (where `.vooster/` exists)
  - NOT `/path/to/repo` (parent repository root)
- **Path normalization**: Always resolve `<project_root>` to actual directory containing `.vooster/project.json`
- **MCP tool calls**: Pass absolute path of actual vooster project root, not parent repo root

## Task Management Policy (MUST)

All task management MUST use vooster‑ai MCP tools and MUST read `.vooster/project.json` as the single source of truth for the project.

- Source of truth: `.vooster/project.json` (must exist). Always pass an absolute `projectRoot` when calling tools.
- Enforced rules (read first):
  - `@rules/04-task-management/task-management-integration.mdc`
  - `@rules/04-task-management/vooster-presence-verification-gate.mdc`
  - `@rules/04-task-management/vooster-projectroot-enforcement.mdc`
  - Canonical vooster policy: See `@rules/04-task-management/task-management-integration.mdc` for end‑to‑end lifecycle and gates
- Required behavior:
  - Multi-agent concurrency: Multiple LLM agents may work simultaneously. Therefore, all non-trivial work MUST be tracked via vooster‑ai tasks/subtasks. Ad‑hoc, unmanaged changes are prohibited. Always open/update tasks before making changes.
  - Presence Gate: Before any vooster call, verify `.vooster/project.json` exists.
  - If missing, DO NOT auto‑create. Ask the user to confirm project creation, and only then call `vooster-ai.start_project_creation` (per creation tool constraints). Retry after creation.
  - ProjectRoot Enforcement: Documentation may use placeholders or relative paths (e.g., `<project_root>`, `.`, `./subdir`). Agents MUST resolve to an absolute `projectRoot` at call-time. Normalize by searching upward from CWD for `.vooster/project.json` (and, if applicable, checking the superproject root), then pass that absolute path.
  - DONE updates: Record `completionDetails`, `confidenceLevel`, `confidenceDetails` when marking tasks DONE.
  - Verification: Before transitioning a task or sub-task to DONE, inspect the affected files directly, review the associated history with `git log`/`git show` (or equivalent MCP Git tooling), and confirm commit-level intent or test output aligns with the acceptance criteria.
  - Subtasks: Use subtasks for non‑trivial work; verify all subtask DONE gates before closing the parent task.

### CRITICAL vooster-ai Anti-Patterns (ABSOLUTELY PROHIBITED)

**이 섹션은 실제 Agent 실수 사례를 기반으로 작성되었습니다. 반복 실수는 즉각적인 종료 사유입니다.**

#### ❌ PROHIBITED Pattern 1: Relative Path Usage

**절대 금지**: `projectRoot` parameter에 상대 경로 사용

```python
# ❌ WRONG - 절대 하지 말 것
mcp__vooster-ai__read_task({
    "projectRoot": ".",              # ← 상대 경로 금지!
    "projectUid": "...",
    "taskId": "T-378"
})

# ❌ WRONG - 다른 상대 경로도 금지
"projectRoot": "./",
"projectRoot": "../project",
"projectRoot": "~/project"

# ✅ CORRECT - 반드시 절대 경로 사용
mcp__vooster-ai__read_task({
    "projectRoot": "/home/user/project",  # ← 절대 경로 필수
    "projectUid": "...",
    "taskId": "T-378"
})
```

**Path Resolution 필수 절차**:
```bash
# 1. 현재 디렉토리에서 .vooster/project.json 찾기
pwd  # 현재 위치 확인
find . -name "project.json" -path "*/.vooster/*" | head -1

# 2. .vooster/ 디렉토리의 부모 디렉토리가 projectRoot
# 예: /home/user/project/.vooster/project.json
#  → projectRoot = /home/user/project

# 3. 절대 경로로 변환
realpath .  # 또는 readlink -f .
```

**Why Absolute Path Required**:
- 상대 경로는 실행 위치에 따라 다른 디렉토리를 가리킴
- Multi-agent 환경에서 각 Agent가 다른 working directory에 있을 수 있음
- `.vooster/project.json` 검증 실패로 모든 vooster 작업 차단됨

#### ❌ PROHIBITED Pattern 2: Subtask UID Misunderstanding

**절대 금지**: Subtask UID를 독립적인 task ID처럼 사용

```python
# ❌ WRONG - T-378-082는 subtask UID, task ID 아님!
mcp__vooster-ai__read_task({
    "projectRoot": "/home/user/project",
    "projectUid": "...",
    "taskId": "T-378-082"  # ← 에러 발생: Invalid task ID format
})

# ✅ CORRECT - Parent task ID + Subtask UID 함께 전달
mcp__vooster-ai__read_task({
    "projectRoot": "/home/user/project",
    "projectUid": "...",
    "taskId": "T-378",           # ← Parent task ID
    "subTaskUid": "T-378-082"    # ← Subtask UID
})
```

**Task ID Format Rules**:
- **Task ID**: `T-XXX` 형식 (예: T-001, T-042, T-378)
  - 독립적인 작업 단위
  - `taskId` parameter로 단독 사용 가능
- **Subtask UID**: `T-XXX-YYY` 형식 (예: T-378-001, T-378-082)
  - Parent task에 종속된 하위 작업
  - 반드시 parent `taskId` + `subTaskUid` 함께 전달
  - `taskId`로 단독 사용 시 에러 발생

**Correct API Call Patterns**:
```python
# Case 1: Parent task 전체 조회 (subtasks 포함)
mcp__vooster-ai__read_task({
    "projectRoot": "<ABS_PATH>",
    "projectUid": "<UID>",
    "taskId": "T-378"
})
# → result.subTasks 배열에 모든 subtask 정보 포함

# Case 2: 특정 subtask만 조회
mcp__vooster-ai__read_task({
    "projectRoot": "<ABS_PATH>",
    "projectUid": "<UID>",
    "taskId": "T-378",          # Parent ID
    "subTaskUid": "T-378-082"   # Specific subtask
})
# → 해당 subtask 상세 정보만 반환

# Case 3: Subtask 상태 업데이트
mcp__vooster-ai__update_subtask_status({
    "projectRoot": "<ABS_PATH>",
    "projectUid": "<UID>",
    "taskId": "T-378",          # Parent ID 필수
    "subTaskUid": "T-378-082",  # Subtask UID
    "status": "DONE"
})
```

#### ❌ PROHIBITED Pattern 3: Direct .vooster/ File Access

**절대 금지**: `.vooster/` 디렉토리의 내부 파일 직접 접근

```bash
# ❌ WRONG - 내부 구현에 의존하는 직접 접근
cat .vooster/tasks.json
jq '.tasks[] | select(.taskId=="T-378")' .vooster/tasks.json
grep "taskId" .vooster/project.json

# ❌ WRONG - 파일 구조 가정
ls .vooster/
find .vooster/ -name "*.json"

# ✅ CORRECT - 반드시 MCP tools 사용
mcp__vooster-ai__list_task({...})
mcp__vooster-ai__read_task({...})
mcp__vooster-ai__read_prd({...})
```

**Why Direct Access Prohibited**:
- `.vooster/` 내부 파일 구조는 언제든 변경될 수 있음 (breaking changes)
- MCP tools는 forward compatibility 보장 (API 변경 시에도 호환)
- 직접 파일 접근은 다른 Agent의 동시 쓰기와 충돌 위험
- vooster-ai 내부 유효성 검사 및 권한 체크 우회
- 데이터 무결성 손상 위험 (잘못된 JSON 수정)

**Correct Alternatives**:
```python
# Task 목록 조회
mcp__vooster-ai__list_task(projectRoot=..., projectUid=..., status="IN_PROGRESS")

# 특정 Task 읽기
mcp__vooster-ai__read_task(projectRoot=..., projectUid=..., taskId="T-378")

# Project 정보 읽기
# .vooster/project.json 직접 읽기 금지
# 대신 list_projects 또는 다른 MCP tools 사용
```

#### Enforcement and Consequences

**즉각 종료 사유 (IMMEDIATE TERMINATION)**:
- 상대 경로 `projectRoot: "."` 사용 발견 시
- Subtask UID를 task ID처럼 잘못 사용 시
- `.vooster/` 파일 직접 접근 (cat, jq, grep 등)
- 위 패턴 반복 시 (첫 번째 경고 후에도 계속 반복)

**Self-Check Protocol**:
모든 vooster-ai MCP 호출 전:
1. ✅ `projectRoot`가 절대 경로인가? (`/`로 시작하는가?)
2. ✅ Task ID 형식이 올바른가? (`T-XXX` or `T-XXX-YYY`)
3. ✅ Subtask 접근 시 parent `taskId` 포함했는가?
4. ✅ MCP tool 사용하는가? (직접 파일 접근 아닌가?)

### vooster‑ai Quickstart (agents)

**Project Setup**: Check `.vooster/project.json` → If missing, call `start_project_creation` → Verify.

**Operations**: add_task, add_sub_tasks, update_task_status, list_task, read_task, get_next_task. Always use absolute projectRoot.

**Subtask 읽기 (Reading Subtasks)**:

vooster-ai는 subtask를 읽는 두 가지 방법을 제공합니다:

**Placeholders**:
- `<ABS_PROJECT_ROOT>`: Absolute path to project root (where `.vooster/project.json` exists)
- `<PROJECT_UID>`: Project unique identifier from `.vooster/project.json`
- `T-XXX`: Task ID format (e.g., T-001, T-042, T-378)
- `T-XXX-YYY`: Subtask UID format (e.g., T-001-001, T-378-075)

1. **부모 task를 통한 전체 subtask 조회** (모든 subtask 정보 포함):
   ```python
   # Task와 모든 subtask를 함께 조회
   result = mcp__vooster-ai__read_task(
       projectRoot="<ABS_PROJECT_ROOT>",
       projectUid="<PROJECT_UID>",
       taskId="T-XXX"
   )
   # result.subTasks 배열에 모든 subtask 정보 포함
   ```

2. **특정 subtask만 조회** (단일 subtask 상세 정보):
   ```python
   # 특정 subtask만 조회
   result = mcp__vooster-ai__read_task(
       projectRoot="<ABS_PROJECT_ROOT>",
       projectUid="<PROJECT_UID>",
       taskId="T-XXX",
       subTaskUid="T-XXX-YYY"  # 특정 subtask UID 지정
   )
   # 해당 subtask의 상세 정보만 반환
   ```

**사용 시나리오**:
- 전체 subtask 목록이 필요한 경우: `taskId`만 전달
- 특정 subtask의 상세 정보만 필요한 경우: `taskId` + `subTaskUid` 함께 전달
- Subtask 상태 확인, 의존성 분석, acceptance criteria 검토 시 활용

<!-- Agent Coordination Header: Agent: Codex (GPT-5, created by OpenAI); Task: user-direct-request; CDHP-Status: triggered; Risk-Score: 72 -->

#### vooster-ai `list_task` parameter enforcement (CRITICAL)

- **Status field** (`status`): Pass an exact vooster status value such as `"BACKLOG"`, `"IN_PROGRESS"`, `"DONE"`, or `"ARCHIVED"`. Informal labels like `"running"` are rejected, which leads to unfocused result sets and forces manual greps. (상태 값은 반드시 vooster가 사용하는 정규 상태 문자열을 그대로 전달해야 하며, `"IN_PROGRESS"`가 진행 중 작업 필터링의 유일한 올바른 값이다.)
- **Pagination requirement** (`limit` + `offset`): When you set `limit`, you MUST send a matching `offset`. If you omit `offset`, vooster returns `오류: offset과 limit는 함께 제공되어야 합니다.`. Either supply both values (예: `offset: 0`, `limit: 20`) or drop both to take the server default page size.
- **Recommended call structure**: Double-check parameters before assuming the filter is broken. For example:

  ```json
  {
    "projectRoot": "<ABS_PROJECT_ROOT>",
    "projectUid": "<PROJECT_UID>",
    "status": "IN_PROGRESS",
    "offset": 0,
    "limit": 20
  }
  ```

- **Fallback discipline**: If results still look unexpected, re-read the latest `read_task` entries before falling back to shell tools. Manual `grep`는 마지막 수단이며, vooster 파라미터 검증을 먼저 수행해야 한다.

<!-- Agent Coordination Header
Agent: Codex CLI Agent (OpenAI)
Task: AGENTS.md — strengthen filter-first vooster usage
CDHP-Status: triggered
Risk-Score: 74
-->

#### Filter-First vooster usage (MUST)

- Always filter at the source. Do not page blindly and then filter locally.
- Prefer `status` parameter (e.g., `"DONE"`, `"IN_PROGRESS"`) when your MCP wrapper supports it. If your client only exposes `includeCompleted`, set it appropriately and still minimize pages with `limit`.
- Start with the smallest page that answers the question. Raise `limit` only if needed.

Examples (pick the variant your client supports):

```json
// A) Filter by status (preferred when available)
{
  "projectRoot": "<ABS_PROJECT_ROOT>",
  "projectUid": "<PROJECT_UID>",
  "status": "DONE",
  "offset": 0,
  "limit": 50
}

// B) Compatibility: include completed items (if status not exposed)
{
  "projectRoot": "<ABS_PROJECT_ROOT>",
  "projectUid": "<PROJECT_UID>",
  "includeCompleted": true,
  "offset": 0,
  "limit": 50
}
```

DONE-sampling workflow (applies to audits):

1) Pre-scope with filters
   - Use `status: "DONE"` (or `includeCompleted: true`) from the first call.
   - Request a modest `limit` (e.g., 25–50) rather than scanning many pages.

2) Determine sample size without overfetching
   - If the API returns `Total`, compute sample target (e.g., 10% or min/max bounds).
   - Otherwise, iterate pages only until the target count is collected.

3) Verify with `read_task`
   - For each sampled task, call `read_task` to verify acceptance criteria and `completionDetails` quality.
   - If discrepancies arise, do NOT downgrade status directly; follow the conflict pattern: open an investigation task and/or append via `update_task_completion_log`.

4) Record outcomes
   - Append concise findings via `update_task_completion_log` for already-DONE tasks.
   - If systemic issues are found, open a follow-up task summarizing the remediation plan.

Quick anti-patterns (forbidden during audits):
- Paging through 3+ pages before adding any filter.
- Using shell greps over `.vooster/tasks/` as primary method instead of server-side filters.
- Sampling from mixed-status pages when a status filter exists.

Rationale
- Reduces wasted MCP calls and latency, keeps audit sampling reproducible, and lowers error rate from stale mixed pages.


**Mandatory Subtask Creation (MUST)**:

- **Complexity 5+ Requirement**: ALL tasks with complexity ≥ 5 MUST include subtasks
- **Auto-Generation**: Use complexity-based templates (3-5 subtasks for complexity 5-6, 5-8 for complexity 7-8, 8-12 for complexity 9-10)
- **Quality Standards**: Each subtask requires clear title, implementation guidance (aiPrompt), measurable acceptance criteria, proper dependencies

**Subtask Completion Verification (MUST)**:

- **Pre-DONE Validation**: Before marking any task DONE, verify ALL subtasks are completed
- **Auto-Correction**: System automatically reverts tasks to IN_PROGRESS if incomplete subtasks detected
- **Audit Process**: Periodic verification of DONE tasks with subtasks to maintain data integrity

**Dependencies (CRITICAL)**: Before creating: survey existing tasks, prevent duplicates, map prerequisites/blockers, document rationale. **NEVER run dependent tasks in parallel - check vooster dependencies first.**

**Multi-Part Requests**: Analyze → Decompose into independent tasks → Ensure separate PDCA cycles → Set dependencies → Map branches.

ProjectRoot handling:

- Documentation MAY show relative or token placeholders for readability; execution MUST pass an absolute `projectRoot`.
- Normalize inputs to an absolute path before calls; never pass `.`.

Examples (concrete):

- Resolve projectRoot (subtree-aware):
- Search upward from CWD for `.vooster/project.json`; set `projectRoot` to that directory's absolute path (`<ABS_PROJECT_ROOT>`). In a host repository with the `.cursor` subtree, this will be the host repo root.
- vooster-ai.add_task:
  - `vooster-ai.add_task { projectRoot: "<ABS_PROJECT_ROOT>", projectUid: "<PROJECT_UID>", ... }`

## Git Policy (agents)

- Prefer MCP Git tools for status/diff/add/commit/checkout/branch/log/show/reset.
- **Commit Messages (STRICT NO AI ATTRIBUTION)**: Use ONLY clean conventional commit format. ABSOLUTELY FORBIDDEN: Any AI attribution including "Generated with [Claude Code]", "Co-Authored-By: Claude", or any variant mentioning AI assistance. Violations directly contradict AGENTS.md policy and demonstrate failure to follow instructions.
- History Review: Use `mcp_git_git_log`, `mcp_git_git_show`, and `mcp_git_git_diff` to inspect prior commits before validating work. Only fall back to CLI (`git log`, `git show`, `git diff`) with justification, recorded console output, and after passing the diff-first gate.
- CLI fallback allowed for `git fetch`, `git rebase`, `git merge`, `git push` with gates:
  - Diff‑first gate passed (review staged and branch diff)
  - Justification recorded (include task/PR IDs)
  - Console capture per `@rules/08-documentation/automation-capture-policy.mdc`
  - Pre‑push checks: status clean, lint passes, remote configured, upstream tracking verified
- See enforcement: `@rules/05-git-workflow/git-workflow-rules.mdc` (MCP Git Enforcement (MUST)).

### Commit & Push Coordination (MANDATORY)

- **Commit before hand-off**: When you complete a logical slice of work, finish triage, or touch shared configuration (docker, migrations, `.env.example`, installers), create a git commit in the same session linking the change to the relevant vooster task ID. This preserves evidence for other agents and the audit trail mandated in Multi-Agent Task Status Verification.
- **Remote synchronization**: If `git remote get-url origin` (or configured upstream) succeeds, push the commit after passing verification gates so concurrent agents can `git pull` instead of duplicating work. Record the push (branch + commit SHA) in the vooster comment or elimination log. If a push is blocked (CI failure, permission, diverged history), document the reason immediately and open a follow-up task if you cannot resolve it.
- **No-remote situations**: When no remote is configured or pushes are temporarily prohibited by user instruction, explicitly log this in vooster and include the local commit hash so others can cherry-pick if needed.
- **Secrets & state checks**: Before every commit/push ensure no secrets or local-only state were staged—run `git status`, `git diff --cached`, and secret scanners as required. Never commit `.env` with live credentials; update templates and documentation instead.
- **Coordination broadcast**: After pushing, leave a short vooster note referencing the commit SHA and impacted files or tasks so auditors know which snapshot to inspect.

### Subtree and `.git/` anomaly SOP (MUST read when triggered)

- If `git status --short` shows entries under `./.git/` (e.g., `A ./.git/HEAD`), do NOT commit them. This indicates a transient index/state issue.
- Recovery: `git reset` → verify `.cursor` is a subtree → `git reset HEAD .git/` if staged → proceed with normal commit.
- Staging policy (MUST): Do NOT use `git add .` or `git add -A` at repo root. Stage explicit paths only. Since `.cursor` is now a subtree, all `.cursor/**` files are part of the main repository and can be staged normally. **MUST follow Safe Git Add Procedure (see below) for ALL staging operations.**

### Subtree 운영 원칙과 배포 흐름 (권장 표준)

- 목적: `.cursor`를 git subtree로 메인 저장소에 통합하여 단일 저장소로 관리합니다.
- 커밋 규칙(중요): `.cursor/**` 내용물은 모두 메인 저장소의 일부로 일반 파일처럼 커밋합니다.
- 업데이트 절차(subtree pull):
  1) 원격 저장소의 최신 변경사항 가져오기: `git subtree pull --prefix=.cursor git@github.com:seonghobae/.cursor.git develop --squash`
  2) 충돌 해결 후 커밋
  3) 변경사항 확인: `git diff HEAD~1`
- 변경사항 기여(subtree push):
  1) `.cursor` 내 변경사항을 원격으로 푸시: `git subtree push --prefix=.cursor git@github.com:seonghobae/.cursor.git develop`
  2) 원격 저장소에서 PR 생성 및 머지
- 즉시 반영: `.cursor` 디렉토리의 변경사항은 메인 저장소와 함께 즉시 커밋되며, 별도의 포인터 업데이트가 필요 없습니다.
- 검증 게이트: 커밋 전 `git status --short | grep "^A.*\.git/"`로 `.git` 파일 스테이징 여부를 확인하고, 발견 시 즉시 `git reset HEAD .git/`로 복구합니다.

### Safe Git Add Procedure (MUST)

**Repository-aware Git Add Protocol**:

1. **Get Current Repository Path (CRITICAL: Respect Shell Context)**:
   - **NEVER** arbitrarily change directories without user instruction
   - **ALWAYS** use the shell's current working directory as repo_path
   - Execute `pwd` to get current working directory - this IS your repo_path
   - **WARNING**: If shell shows "Shell cwd was reset to /path/to/dir", that means the user IS working in that directory
   - **Example Scenarios**:
     - If `pwd` returns `/home/user/project/.cursor` → repo_path = `/home/user/project/.cursor` (subtree directory)
     - If `pwd` returns `/home/user/project` → repo_path = `/home/user/project` (main)
     - **NEVER** assume you should work in parent/child directory unless explicitly instructed
   - **Common Mistake**:
     ```bash
     # WRONG - Ignoring shell context
     cd /home/user/project && pwd  # If shell was in .cursor, this is WRONG!

     # CORRECT - Respect current context
     pwd  # Use whatever directory the shell is currently in
     REPO_PATH=$(pwd)
     ```
   - **Critical Rule**: The user's shell context tells you WHERE they want to work. Respect it!

2. **Stage Changes Safely**:
   - Use explicit paths relative to `repo_path`
   - NEVER use `git add .` at repository root
   - Preferred: `git add <specific_file>` or `git add <specific_directory>/`
   - For multiple files: List each explicitly

3. **Verify Symbolic Links**:
   - **Scenario**: Repository has symbolic links pointing to files within `.cursor` subtree
   - Check for symbolic links in main repo: `find . -type l -not -path "./.git/*" -not -path "./*/.git/*" -exec ls -la {} \; | grep -E "\.cursor/"`
   - Since `.cursor` is now a subtree (part of main repo), symlinks and their targets can be committed together
   - **Note**: All files in `.cursor/` are now regular files in the main repository, not external references
   - **Simplified Process with Subtree**:
     ```bash
     # Step 1: Check if symlinks point to .cursor files
     for link in $(find . -type l -not -path "./.git/*"); do
       target=$(readlink "$link")
       if [[ "$target" == *"/.cursor/"* ]]; then
         echo "SYMLINK: $link -> $target (subtree file)"
       fi
     done

     # Step 2: Stage all changes together (since .cursor is part of main repo)
     git add <specific_files> <specific_symlinks>
     git commit -m "feat: update files and symlinks"
     ```
   - **Note**: With subtree, no separate commits needed for .cursor files vs symlinks

4. **Verify .git Directory Exclusion**:
   - After staging, ALWAYS run: `git status --short | grep "^A.*\.git/"`
   - If output is NOT empty, .git files were staged (CRITICAL ERROR)
   - Recovery: Immediately run `git reset HEAD .git/` to unstage

5. **Pre-commit Verification Checklist**:

   ```bash
   # Step 1: Get repository path
   REPO_PATH=$(pwd)

   # Step 2: Stage specific changes
   git add src/ tests/ docs/  # Example: specific directories

   # Step 3: Check for symbolic links pointing to .cursor files (simplified for subtree)
   SYMLINKS=$(find . -type l -not -path "./.git/*" -not -path "./*/.git/*" 2>/dev/null)
   if [ ! -z "$SYMLINKS" ]; then
     echo "Checking symbolic links..."
     for link in $SYMLINKS; do
       target=$(readlink "$link")
       # Check if symlink points to .cursor subtree
       if [[ "$target" == *"/.cursor/"* ]]; then
         echo "INFO: $link points to .cursor subtree file: $target"
         # No separate verification needed - .cursor is part of main repo
       fi
     done
   fi

   # Step 4: Verify no .git files staged (existing check)
   if git status --short | grep -q "^A.*\.git/"; then
     echo "ERROR: .git files staged! Running recovery..."
     git reset HEAD .git/
     exit 1
   fi

   # Step 5: Verify staged changes
   git status

   # Step 6: Only if verification passes, proceed to commit
   git commit -m "feat: your message here"
   ```

6. **Automated Safety Check**:
   - Agents MUST implement this verification before EVERY commit
   - If .git files detected in staging, abort commit and report error
   - Document the incident in vooster task logs

**PROHIBITED**:

- ❌ `git add .` at repository root
- ❌ `git add -A` without explicit path filtering
- ❌ Committing without .git verification
- ❌ Ignoring .git staging warnings
- ❌ Changing directories without user instruction when determining repo_path
- ❌ Ignoring "Shell cwd was reset to..." messages
- ❌ Assuming parent directory is the correct repo when shell is in .cursor directory

**REQUIRED**:

- ✅ Use `pwd` to establish repo_path
- ✅ Stage with explicit paths
- ✅ Check symbolic links before staging
- ✅ Verify no .git files before commit
- ✅ Document verification in task logs
- ✅ Use shell's current working directory as repo_path
- ✅ Respect "Shell cwd was reset to..." as the intended working directory
- ✅ Only change directories when explicitly instructed by user

Deletions staging policy:

- Prefer MCP Git by adding the parent directory via `git_add` to stage deletions within it; if MCP cannot stage deletions in your environment, CLI `git add -A` is allowed with the same gates above and the Safe Git Add Procedure verification.

## GitHub Actions Workflow Verification (MUST)

**Mandatory Verification for GitHub-hosted Projects**:

When working with projects that use GitHub Actions (`.github/workflows/*.yml`), agents MUST verify workflow trigger correctness after any workflow modifications.

**Verification Requirements**:

1. **Upstream Detection**: Check if remote upstream is GitHub:

   ```bash
   git remote get-url origin  # Should contain github.com
   ```

2. **Workflow Status Verification**: Use `gh` CLI to verify workflows execute correctly:

   ```bash
   # List all workflows
   gh workflow list

   # Check recent workflow runs
   gh run list --limit 10

   # View specific run details if failures detected
   gh run view <run-id>
   ```

3. **Common YAML Structure Issues to Prevent**:
   - ✅ **CORRECT**: `schedule` trigger in `on` section alongside `push`, `pull_request`, `workflow_dispatch`
   - ❌ **WRONG**: `schedule` trigger at job level (causes "workflow file issue")
   - ✅ **CORRECT**: Proper YAML indentation and structure
   - ❌ **WRONG**: Misplaced sections causing parsing errors

4. **Post-Modification Verification Protocol**:
   - After modifying any `.github/workflows/*.yml` file:
     1. Commit and push changes
     2. Run `gh run list --limit 5` to check latest runs
     3. Verify no "workflow file issue" or parsing errors
     4. If errors detected, review YAML structure immediately
     5. Document fix in commit message

5. **Integration with Git Policy**:
   - Workflow verification is part of post-commit quality gates
   - Failed workflows should trigger immediate investigation
   - Do NOT ignore workflow failures - they indicate structural problems

**Example Workflow Verification**:

```bash
# After committing workflow changes
git push origin develop

# Verify workflow triggers correctly
gh workflow list  # Check workflow is listed
gh run list --limit 5  # Verify no immediate failures

# If failures detected
gh run view <run-id>  # Investigate specific failure
# Fix YAML structure issues based on error messages
# Re-commit and verify again
```

**Required Tools**:

- `gh` CLI must be installed and authenticated
- Installation: `brew install gh` (macOS) or `apt install gh` (Ubuntu)
- Authentication: `gh auth login`

## Documentation & Lint (agents)

**Linting → Commit Order Enforcement (MUST)**:

Mandatory sequence for ALL code changes with automatic enforcement:

1. **Code Changes**: Complete file modifications/additions
2. **Linting Execution**: Run ALL applicable linters (markdownlint, eslint, etc.) and verify 0 errors
3. **Commit Permission**: Only after linting passes, execute git commit via MCP Git tools

**Auto-Enforcement Triggers**:

- File edit/modification completion → Auto-trigger linting
- Git commit attempt → Auto-verify linting completion
- Linting failure → Auto-block commit until errors resolved

**Standard Linting Commands**:

- Markdown: `npx -y markdownlint "**/*.md" "**/*.mdc" --ignore node_modules --config .markdownlint.json`
- Code quality: Run project-specific linters (eslint, etc.) per existing configuration

**Quality Gates**: Linting error count = 0 required for commit approval. No bypassing or weakening allowed without explicit maintainer approval recorded in vooster.

- Follow doc structure/gates:
  - `@rules/08-documentation/markdown-structure-policy.mdc`
  - `@rules/08-documentation/documentation-rules.mdc`

### Time and Timestamp Policy (MUST)

- Authoritative time source: Use MCP `time.get_current_time` with explicit IANA timezone (default: `Asia/Seoul` if user unspecified).
- Time conversions: Use MCP `time.convert_time` for all timezone conversions; never assume locale defaults.
- No fabricated dates: Do not assert model training date or authorship timestamps without repository evidence. Prefer `git log` and file history for authorship; use MCP time for "now".
- Include timezone in outputs: Document timestamps as `YYYY-MM-DD HH:mm TZ (UTC±HH:MM)`.
- Single capture per operation group: Capture "now" once and reuse to avoid drift during multi-step operations.
- See `@rules/06-automation/time-mcp-policy.mdc` for full details.

## Conditional Rules

- `@rules/07-code-quality/ui-ux-self-review-checklist.mdc` (UI/UX work)
- `@rules/07-code-quality/postgresql-schema-quality-rules.mdc` (PostgreSQL database work)
- `@rules/07-code-quality/api-schema-naming-rules.mdc`
- `@rules/06-automation/smoke-test-policy.mdc`
- `@rules/06-automation/waf-integration-policy.mdc` (Web applications)
- `@rules/07-code-quality/r-code-quality-rules.mdc`
- `@rules/08-documentation/plantuml-rules.mdc`
- `@rules/08-documentation/wcag-color-rules.mdc`
- `@rules/08-documentation/no-fluff-closing-sections.mdc`
- `@rules/08-documentation/code-block-consistency-policy.mdc`

### PostgreSQL Naming Conventions (Database Work)

**MANDATORY for all PostgreSQL database work**. Reference: `@rules/07-code-quality/postgresql-schema-quality-rules.mdc`

#### Table Naming

- Use plural form with snake_case: `users`, `order_items`, `user_sessions`
- NO prefixes: Avoid `tbl_`, `table_` prefixes
- NO reserved words from pg_keywords (R+U categories all prohibited)

#### Column Naming

- Use snake_case with descriptive prefixes: `user_uuid`, `user_name`, `user_email`
- Apply table name prefix to avoid JOIN ambiguity: `user_id`, `project_id`, `config_value`
- **3-character rule**: Identifiers ≤3 characters MUST have prefix (`id` → `user_id`, `key` → `config_key`)
- NO bare reserved words: `name` → `user_name`, `type` → `endpoint_type`, `status` → `run_status`
- Foreign keys: `[referenced_table]_[singular]_id` pattern (`user_id`, `project_id`)

#### Prohibited Patterns

- Quoted identifiers (`"user"`, `"Name"`) - ABSOLUTELY FORBIDDEN
- camelCase or PascalCase without quotes
- Any word from `SELECT * FROM pg_get_keywords();` (reserved + unreserved)
- Generic short names in multi-table contexts (`id`, `name`, `key`, `value`, `data`)

### PostgreSQL 권한 분리 및 보안 정책 (Privilege Separation & Security - MANDATORY)

**MANDATORY for all PostgreSQL projects**. Full specification: `@rules/07-code-quality/postgresql-schema-quality-rules.mdc` Section 13.

**핵심 원칙 (Core Principles)**: Principle of Least Privilege와 Separation of Duties 엄격 준수. Admin 계정과 User 계정을 명확히 분리하여 보안 강화.

#### 계정 분리 원칙 (Account Separation Principle)

**Administrator 계정 책임 (Admin Account Responsibilities)**:

- PostgreSQL extensions 활성화 (uuid-ossp, pgcrypto, pg_cron)
- pg_cron jobs 등록 및 관리
- 스키마 마이그레이션 실행 (CREATE TABLE, ALTER TABLE, CREATE INDEX)
- Role 및 권한 설정 (GRANT/REVOKE)
- 데이터베이스 생성 및 삭제

**User 계정 책임 (User Account Responsibilities)**:

- 일반 애플리케이션 쿼리 실행 (SELECT, INSERT, UPDATE, DELETE)
- 읽기 전용 트랜잭션 처리
- Connection pooling을 통한 런타임 실행

**금지 패턴 (PROHIBITED)**:

- ❌ Admin 계정으로 일반 애플리케이션 쿼리 실행
- ❌ User 계정으로 스키마 변경 시도
- ❌ 프로덕션 환경에서 admin 계정으로 애플리케이션 실행
- ❌ 단일 계정으로 모든 작업 수행

#### 환경 변수 관리 (Environment Variable Management)

**필수 파일 구조**:

```bash
.env               # Production credentials (gitignored)
.env.example       # Template with dummy values (committed)
.env.test          # Test environment (gitignored or committed per policy)
```

**DSN 형식 (DSN Format)**:
```bash
# Admin DSN - for schema migrations and setup
POSTGRES_ADMIN_DSN="postgresql://projectname_admin:ADMIN_PASS@localhost:5432/postgres?sslmode=require"

# User DSN - for application runtime
POSTGRES_USER_DSN="postgresql://projectname_user:USER_PASS@localhost:5432/projectname_db?sslmode=require"

# SSL enforcement by environment
# Development: sslmode=require (basic SSL)
# Production: sslmode=verify-full (certificate verification)
```

**Runtime sourcing protocol (MANDATORY)**:

```bash
set -a && source .env && set +a
# Run required commands here (psql, pytest, python -m, etc.)
```

- 위 명령을 같은 셸 세션에서 실행해 `POSTGRES_*` 및 기타 필수 환경 변수를 내보낸 뒤 CLI/테스트/마이그레이션 명령을 수행한다.
- `.env`를 갱신했거나 공유 환경에서 작업 중이라면 vooster 코멘트 또는 elimination log에 실행 시각과 주요 커맨드를 기록한다.
- 다른 에이전트와 병행 작업 시, 동일 세션에서 명령을 실행했음을 언급해 환경 불일치를 방지한다.

**Never Commit**:

- ❌ `.env` with actual credentials
- ❌ Any file containing real passwords
- ✅ `.env.example` with placeholder values
- ✅ Documentation of credential generation process

#### 데이터베이스/사용자 명명 규칙 (Database/User Naming)

⚠️ **CRITICAL WARNING**: `myapp` is a PLACEHOLDER. Replace with your actual project name.
❌ DO NOT literally create databases named "myapp_db" or users named "myapp_admin"
✅ Example: For project "ecommerce", use "ecommerce_db", "ecommerce_admin", "ecommerce_user"

**Naming Convention**:

```sql
-- Database names: {projectname}_db
CREATE DATABASE myapp_db;

-- Admin account: {projectname}_admin
CREATE USER myapp_admin WITH PASSWORD 'secure_admin_pass';

-- User account: {projectname}_user
CREATE USER myapp_user WITH PASSWORD 'secure_user_pass';
```

**권한 설정 (Permission Setup)**:

```sql
-- Admin: Full control on application database
GRANT ALL PRIVILEGES ON DATABASE myapp_db TO myapp_admin;
ALTER DATABASE myapp_db OWNER TO myapp_admin;

-- User: Limited access on application database only
GRANT CONNECT ON DATABASE myapp_db TO myapp_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO myapp_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO myapp_user;
```

#### postgres DB 사용 원칙 (postgres DB Usage Policy - CRITICAL)

**핵심 원칙**: 일반 애플리케이션 계정은 반드시 프로젝트 이름으로 된 데이터베이스를 사용

**Scope**: Admin/User DSN pattern applies to databases, libraries, AND applications under development.

**postgres 데이터베이스 (System-Wide Only)**:

- ✅ **허용**: pg_cron jobs, system-wide extensions (uuid-ossp, pgcrypto), cross-database metadata
- ❌ **금지**: Application-specific data, user data, business logic tables
- **이유 (Rationale)**: 권한 분리, 데이터 격리, 백업 정책 차별화

**프로젝트 데이터베이스 ({projectname}_db)**:

- ✅ **모든 애플리케이션 데이터 저장**: User tables, business logic, application state
- ✅ **User 계정 전용 접근**: `{projectname}_user` account MUST use `{projectname}_db`
- ✅ **비즈니스 로직 테이블**: All domain-specific tables belong here

**실행 예시 (Example)**:

```sql
-- Admin account: Uses postgres DB for system operations
\c postgres
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
SELECT cron.schedule('job-name', '0 * * * *', 'SELECT process_batch()');

-- User account: Uses project-specific DB for application data
\c myapp_db
SELECT * FROM users;  -- Application data in project DB
INSERT INTO orders (user_id, product_id) VALUES (1, 2);
```

**강제 정책 (Enforcement)**:

- ❌ **절대 금지**: User account connecting to postgres database for application queries
- ✅ **필수**: User account DSN MUST specify `{projectname}_db` as database name
- **검증**: Connection string must contain correct database: `postgresql://user:pass@host:port/projectname_db`

#### 패스워드 보안 (Password Security)

**생성 방법**:
```bash
# Generate 48-character secure password (32+ characters required)
openssl rand -base64 48 | tr -d '\n' > admin_pass.txt
openssl rand -base64 48 | tr -d '\n' > user_pass.txt

# Store in .env (never commit this file)
echo "POSTGRES_ADMIN_DSN=postgresql://myapp_admin:$(cat admin_pass.txt)@localhost:5432/postgres?sslmode=require" >> .env
echo "POSTGRES_USER_DSN=postgresql://myapp_user:$(cat user_pass.txt)@localhost:5432/myapp_db?sslmode=require" >> .env

# Secure cleanup (overwrite and delete)
shred -u admin_pass.txt user_pass.txt
```

**Docker 포트 설정 (Docker Port Configuration)**:

- **외부 포트 (Host Port)**: 비표준 포트 사용 (예: 55432 또는 55433) - 시스템 PostgreSQL과 충돌 방지
- **내부 포트 (Container Port)**: 5432 (PostgreSQL 표준)
- **매핑 형식**: `docker run -p 55432:5432 postgres` 또는 `docker compose` 설정에서 `ports: - "55432:5432"`
- **기존 포트 유지**: 이미 특정 포트를 사용 중이라면 변경할 필요 없음 (예시일 뿐)
- **클러스터링 라이브러리**: citusdata 등의 클러스터링 확장은 다른 포트 설정 필요

**보안 요구사항 (Security Requirements)**:

- **최소 길이**: 32+ 문자
- **복잡도**: 대소문자, 숫자, 특수문자 혼합 (openssl 자동 생성)
- **저장**: 환경 변수, HashiCorp Vault, 또는 암호화된 설정 파일
- **금지**: 하드코딩, 버전 관리 시스템에 커밋, 로그 출력
- **갱신 주기**: 최소 90일마다 rotate (production), 프로젝트 정책 준수

**Credential Rotation Coordination (MANDATORY)**:

- Rotation 선언: `POSTGRES_ADMIN_PASSWORD`, `POSTGRES_USER_PASSWORD`, `POSTGRES_ADMIN_DSN`, `POSTGRES_USER_DSN`, Docker compose `.env` 등의 비밀번호/DSN 값을 변경하려면 먼저 관련 태스크(예: T-378-093 등)를 `IN_PROGRESS`로 전환하고, vooster 코멘트/elim log에 “rotation intent”, 대상 변수 목록, 예상 적용 시각을 남긴다. 다른 에이전트가 동일 컨테이너를 사용 중인지 `docker compose ps`와 vooster 댓글을 통해 확인한다.
- 한 번에 한 명만: 동일 비밀번호를 동시에 두 값으로 변경하는 일을 방지하기 위해 “rotation owner” 한 명만 작업한다. 코멘트에 해시(`openssl dgst -sha256 <<<"$NEW_SECRET"`)나 길이 정보 등 확인 가능한 메타데이터만 공유하고, 실제 비밀번호는 개인 `.env.local`/비밀 스토리지에만 보관한다.
- 적용 절차: 모든 관련 에이전트가 새 값 수신을 확인한 뒤 `docker compose down` → 비밀 값 교체 → `docker compose up` 순서로 진행한다. 이미 실행 중인 컨테이너를 강제로 재시작해야 한다면 선행 에이전트의 동의를 받거나 15분 동안 응답이 없다는 근거를 기록한다.
- 사후 검증: rotation 후 `docker compose ps`, `SELECT current_user`, `SHOW password_encryption` 등 확인 명령을 실행하고 결과 행을 코멘트/문서에 남긴다. 동시에 종속 DSN을 사용하는 스크립트/테스트(`scripts/db_setup.sh`, `python -m xtrmLLMBatch.cli ...`)도 재검증하여 drift가 없는지 확인한다.
- 재선언 없을 때: 기존 비밀번호가 유지되어야 한다면 “rotation intent 없음” 메시지를 남겨 경합을 미리 방지한다. 누군가 비정상 값을 주입한 것으로 판단되면 Stale 프로토콜을 따라 즉시 중단하고, 조사 태스크를 새로 생성한다.
- 감사자 제한: Audit 역할은 위 절차 없이 비밀번호나 DSN을 변경하지 않는다. 감사 중 rotation이 필요하면 Implementation 담당자에게 작업을 위임하거나 스스로 “Audit → Implementation switch” 선언을 한 뒤 rotation 프로토콜을 따른다.
- 환경 변경 기록/검증: `.env`/Docker 환경을 수정하는 에이전트는 vooster 코멘트(또는 elimination log)에 rotation intent, 대상 변수/파일, 예상 영향, 검증 명령(예: `docker compose ps`, `.env` 해시)을 기록한다. 단독 작업이라도 동일한 형식을 유지하고, 작업 완료 후 “env change complete”와 실제 검증 결과를 남긴다. 다른 에이전트가 추가 변경이 필요하면 동일 스레드에 “변경 의도”를 남기고 마지막 상태를 재확인한 뒤 진행한다. 예상과 다른 값이 감지되면 즉시 drift 근거를 문서화하고 follow-up 태스크(또는 수정 intent 코멘트)로 공유한다.

#### Docker/Postgres Bootstrap Coordination (MANDATORY)

- `docker/postgres/init/*.sql` 및 관련 `.sh` 스크립트는 반드시 `.env`(또는 명시 전달된 환경 변수)에서 `POSTGRES_ADMIN_ROLE`, `POSTGRES_RUNTIME_ROLE`, 각 비밀번호, 대상 DB 이름을 읽어야 한다. 코드 내 하드코딩(예: `xtrm_admin`, `admin_pass`)이 발견되면 즉시 수정하고 `.env.example`도 동일 변수로 갱신한다.
- 컨테이너 재기동 또는 clean init이 필요할 때는 착수 전에 vooster에 Implementation intent를 남기고, 동일 서브태스크에서 다른 Implementation 작업이 진행 중인지 확인한다. 다른 에이전트가 검증 중이면 재시작 대신 로그/SQL 증거만 확인하거나 합의 후 순차적으로 진행한다.
- Implementation 역할은 `docker compose up` 실행 시 사용한 `.env` 값(민감 정보 제외)을 docs/T-378-implementation-summary.md 등에 기록하고, 부팅 로그/`SELECT current_user`/`\\du` 출력 등으로 실제 적용을 입증해야 한다. Audit 역할은 환경을 변경하지 않은 채 로그·SQL만 수집한다.
- `.env` 내용은 팀 공유 자산이므로, 값 변경이나 추가 변수가 필요하면 `.env.example`를 먼저 갱신하고 로컬 `.env` 수정 사실을 vooster 코멘트로 알린 뒤 합의 후 반영한다. 승인 없이 기존 값을 덮어쓰지 않는다.
- 컨테이너를 반복적으로 시작/중지해야 할 경우 1회차 로그/결과를 공유(코멘트 또는 elimination log)한 뒤 추가 재시작이 필요한 이유와 예상 횟수를 명시한다. 불필요한 재시작은 다른 구현 작업 흐름을 차단하므로 최소화한다.

#### 운영 가이드라인 (Operational Guidelines)

**개발 환경 설정**:

```bash
# Initial setup (run once)
scripts/db_setup.sh  # Creates admin/user accounts, sets permissions

# Schema migration (use admin DSN)
python migrations/run_migration.py
```

**Migration 실행 (Admin DSN 필수)**:

```python
# migrations/run_migration.py
import os
from sqlalchemy import create_engine

# MUST use Admin DSN for schema changes
admin_dsn = os.getenv("POSTGRES_ADMIN_DSN")
if not admin_dsn:
    raise ValueError("POSTGRES_ADMIN_DSN not set")

engine = create_engine(admin_dsn)
# Execute migrations...
```

**Application Runtime (User DSN 필수)**:
```python
# app/main.py
import os
from sqlalchemy import create_engine

# MUST use User DSN for application queries
user_dsn = os.getenv("POSTGRES_USER_DSN")
if not user_dsn:
    raise ValueError("POSTGRES_USER_DSN not set")

engine = create_engine(user_dsn)
# Execute application queries...
```

**보안 감사 체크리스트 (Security Audit Checklist)**:
- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는가?
- [ ] Admin 계정으로 프로덕션 애플리케이션이 실행되고 있지 않은가?
- [ ] User 계정이 스키마 변경 권한을 가지고 있지 않은가?
- [ ] 패스워드가 32+ 글자이고 안전하게 생성되었는가?
- [ ] Production 환경에서 `sslmode=verify-full` 사용 중인가?
- [ ] 패스워드가 90일 이내에 갱신되었는가?
- [ ] 로그에 credential 정보가 노출되지 않았는가?

**Agent Enforcement (자율 검증)**:
- Agents MUST verify DSN separation before creating database connections
- Agents MUST reject commits containing `.env` files with real credentials
- Agents MUST verify password length (32+ characters) in `.env.example` templates
- Agents MUST check SSL mode enforcement (require for dev, verify-full for prod)
- Agents SHOULD suggest credential rotation if timestamps indicate >90 day age

## DB-ONLY AUDITING & JSONL GOVERNANCE (MANDATORY)

```
Agent Coordination Header
Agent: Codex CLI Agent (OpenAI)
Task: T-343 (AGENTS.md enhancement)
CDHP-Status: triggered (critical file update)
Risk-Score: 68 (policy change + governance)

Rationale: Prevent data sprawl and enforce consistency by mandating database-only auditing and disallowing disk-based JSONL artifacts across the repository. Aligns with memory-only operational policy and eliminates ambiguous test exceptions.
Alternatives-Eliminated: Allowing tests/legacy to create JSONL files (risk of drift and misuse); mixed auditing sources (DB + files).
Cross-Agent-Review: Coordinated via vooster; additive-only policy applied.
```

### Core Rules
- Audits, validations, and reproductions MUST be database-only (PostgreSQL).
- DO NOT create or rely on `.jsonl` files anywhere in the repository (runtime, tests, legacy).
- When serialization is necessary for debugging, use memory buffers (StringIO/BytesIO); do not write to disk.
- Runtime modules under `<package_name>/**` MUST NOT depend on file-based JSONL.

### Enforcement Guidance
- CI/grep examples:
  - `grep -r "with open.*\\.jsonl.*'w'" <package_name>/` → MUST be zero results
  - `grep -r "\\.jsonl\\>" <package_name>/ tests/` → investigate usage; only memory-only buffers permitted
- Packaging hygiene: exclude `*.jsonl` from sdist/wheel via `MANIFEST.in` and build config.

### Migration Notes
- Existing tracked `.jsonl` artifacts MUST be moved under `legacy/fixtures/`.
- Update docs to reflect DB-only auditing and memory-only flows.

## HARNESS CLASSIFICATION POLICY (MANDATORY)

### Definition
- Any file or document whose name contains `harness` is classified as legacy (non-current operational guidance).

### Actions
- Move harness-named files to `legacy/` (e.g., `legacy/examples/`, `legacy/docs/`).
- Do not import or depend on legacy harness code from runtime modules.
- Keep changes additive-only: move and archive; no destructive operations.

### Verification
- `rg -n --hidden --no-ignore-parent "harness"` and relocate matches to `legacy/**` appropriately.
- Update documentation references selectively when needed; prefer DB-only examples.

## MOVE-ONLY REORGANIZATION (SAFE REFACTORING)

### Principles
- Prefer move and archive over deletion; maintain provenance and auditability.
- Respect exceptions and protected paths defined in this file.
- Small, incremental commits with vooster task IDs for coordination.

### Packaging Hygiene
- Ensure non-package artifacts (e.g., `.xlsx`, `.jsonl`, `.tgz`, `.zip`, `.whl`) are excluded from distribution.
- Explicitly include only required package data (e.g., templates, config files, static assets).
  - ✅ Good examples: 
    - `<package_name>/templates/*.html`, `<package_name>/config/default.yaml`
    - `scripts/migrations/*.sql` (used programmatically for schema initialization)
    - `docker/postgres/init/*.sql` (used in Docker image builds)
  - ❌ Bad examples: test fixture SQL, temporary debug scripts, build artifacts

## Analysis Artifacts

- Do not commit analysis scratch files under `rules/_analysis/`. They are ignored via `.gitignore` and MUST remain local.

## Acceptance Criteria (for agent‑performed work)

- `.vooster/project.json` verified before any vooster‑ai operation; `projectRoot` absolute.
- Tasks and subtasks recorded via vooster‑ai; DONE updates include completion details + confidence + justification.
- MCP Git usage for core operations; CLI fallback only where MCP parity is missing, with evidence captured.
- markdownlint passes on modified docs; references use backticked `@rules/...` paths where applicable.

## References (canonical rules)

- Task Management: `@rules/04-task-management/task-management-integration.mdc`
- Presence Gate: `@rules/04-task-management/vooster-presence-verification-gate.mdc`
- ProjectRoot Enforcement: `@rules/04-task-management/vooster-projectroot-enforcement.mdc`
- Git Enforcement: `@rules/05-git-workflow/git-workflow-rules.mdc`
- Documentation: `@rules/08-documentation/documentation-rules.mdc`, `@rules/08-documentation/markdown-structure-policy.mdc`

## Authoritative‑Only Selection & Tokenization (MANDATORY)

### Absolute Prohibitions
- 패턴 매칭/휴리스틱/룰 기반 선정 금지(모델명 substring, mini/nano 배제 등 일체 금지).
- 문자열 규칙으로 모델/토크나이저/키를 결정하지 않는다. 오직 권위 데이터/권위 함수만 사용한다.

### Chat Model Selection (SQL‑first)
- 채팅 모델 추천은 반드시 SQL 함수로 수행한다: `public.get_top_chat_model_id()`
- 정렬 기준(권위 필드만): `rpm×tpm` → `supports_parallel_function_calling` → `max_output_tokens` → `capacity_product` → `total_standard_cost`
- 파이썬 레이어는 위 함수를 우선 호출하고, 실패 시 권위 메타 필드만으로 폴백한다(이름/패턴 사용 금지).

### Batch Model → Canonical Tokenizer (SQL)
- 배치 모델은 `WHERE LOWER(mode)='batch'`로 조회한다.
- canonical tokenizer 확정은 `infer_tiktoken_encoding(model_id|normalized_model)` + `safe_token_count(encoding,'probe')` 검증만 사용한다.
- 사전 집계는 `precompute_token_counts_for_dataset(dataset_uuid)`로 수행한다(권위 함수만).
- 큐잉은 `stage_user_prompt_token_jobs_for_model(dataset_uuid, model_id)`를 사용한다.

### Credentials (Key Source Unification – MUST)
- 모든 제출 경로(SQL/CLI/파이썬)는 `provider_credentials`(pgcrypto 암호화 저장소)만 사용한다.
- `com_config.llm_api_key`는 제출용 키 소스로 사용하지 않는다(헬스/로그에만 허용).
- 키 변경은 `credentials-register`/`credentials-seed-from-env`로 반영하고 Evidence로 검증한다.

### Logging & Separation (MUST)
- 채팅(스키마/헤더) vs 배치(제출/검증)를 명확히 라벨링한다(`source='chat_inference'|'batch_submission'`).
- Evidence 파일과 DB 이벤트에 source 라벨을 포함한다.

### Import Phase Output (MUST)
- import 단계에서 임시/디폴트 토크나이저 표시 금지. 확정된 canonical tokenizer만 허용한다.
- 토크나이저 확정은 토큰잡/배치 모델 기반 경로에서 수행하고 그 값을 출력한다.

### SQL‑First Rule
- 선정/확정/집계는 가능하면 SQL/PL/pgSQL로 구현한다. 파이썬은 권위 함수 호출 wrapper로만 사용한다.
### CLI 플래그/인자 정책 (MANDATORY)

- 기본 원칙(Zero-Arg 우선): 사용자의 추가 부담을 유발하는 신규 CLI 플래그/필수 인자 도입을 금지한다. 가능한 한 권위 데이터(환경변수, `com_config`, `provider_credentials`, SQL 함수)로 자동 결정한다.
- 필수 플래그 금지: 공개 CLI에서 `required=True`(argparse/click 등)로 새 인자를 강제하는 변경은 금지한다. 절대 필요한 경우에도 기본값/자동해석을 제공하고, 비대화 환경에서 “무플래그 성공 경로”를 유지한다.
- 권위‑우선 자동화: 모델/토크나이저/엔드포인트/크레덴셜은 SQL‑first로 확정한다.
  - 채팅 모델: `public.get_top_chat_model_id(endpoint_uuid)`
  - 배치 토크나이저: `get_tokenizer_for_model(model_id, endpoint_uuid)`
  - 토큰 사전산출: `precompute_token_counts_for_dataset(dataset_uuid, endpoint_uuid)`
  - 큐잉: `stage_user_prompt_token_jobs_for_model(dataset_uuid, model_id, endpoint_uuid)`
- 보안 원칙: API 키/시크릿을 플래그로 전달하는 것을 금지한다. `provider_credentials`(pgcrypto) 저장소만 사용하며, 제출/검증 헤더는 DB 복호화로 주입한다.
- 비호환 변경 금지: 기존 인자/기본값의 의미를 바꾸거나 신규 필수 인자를 추가하지 않는다. 필요 시 버전드 서브커맨드로 도입하고, 구 경로는 셔민(Shim)으로 유지한다.
- 허용되는 예외(사전 승인 필요): 운영상 자동 결정이 불가능한 값(권위 데이터에 부재)만, 설정 프로파일/식별자(예: `--config-profile <name>`)로 간접 참조하게 한다. 임시/직접 값 전달 플래그는 금지.
- DX/가독성: 휴리스틱/패턴 기반 토글(`--no-*`, `--force-*`)의 남용을 금지한다. 디버그용 토글이 필요하면 환경변수로 한정하고, 기본값은 권위 데이터 자동화가 성공하는 경로여야 한다.
- 문서/테스트 의무:
  - 문서: 신규 옵션을 추가하려면 PRD/TRD에 근거를 기록하고, AGENTS.md에 반영한다.
  - 테스트: “무플래그 성공” 테스트를 필수로 추가한다. 신규 옵션 사용 여부와 무관하게 기본 경로가 통과해야 한다.
- 에스컬레이션: 위반(필수 플래그 도입/자동화 경로 제거)은 작업 차단 사유이며, `vooster-ai`에 설계 재검증 태스크를 생성한다.
### Device Identification Policy (MANDATORY)

- 표준 환경변수: `CLIENT_DEVICE_ID`를 단일 표준으로 사용한다. `XTRM_DEVICE_ID`는 더 이상 사용하지 않으며, 레거시 경로에서 발견 시 제거한다.
- 엔드포인트 해석: `CLIENT_DEVICE_ID` → `resolve_endpoint_uuid_for_device(device_id)`로 DB에서 권위적으로 해석한다.
- 쓰기 금지: 클라이언트는 OS 레지스트리/로컬 파일에 디바이스 ID를 저장하지 않는다. 임의 생성/랜덤/해시 기반 저장을 금지한다.
- Fail‑fast: `CLIENT_DEVICE_ID` 또는 `LLM_ENDPOINT_UUID/E2E_LLM_ENDPOINT_UUID`가 없으면 작업을 중단하고 명시적 설정을 요구한다(비결정성 폴백 금지).
- .env 요구: 통신(HTTP/gateway/배치 제출) 허용 조건으로 `.env`에 `CLIENT_DEVICE_ID`가 반드시 존재해야 한다. 애플리케이션은 존재 여부를 사전 검증한다.
- 운영 책임 분리: 디바이스→엔드포인트 매핑은 운영(관리자 DSN) 경로로만 등록(`register_client_device`)하며, 애플리케이션은 읽기만 수행한다.

#### Device ID as Unique Auth Key (MANDATORY)
- 정의: `CLIENT_DEVICE_ID`는 사용자 고유 인증 키로 간주한다(Secret). API 키와 동일 수준으로 보호하고, 로그/메타데이터/이벤트에 평문으로 남기지 않는다.
- 입력 경로: 오직 환경변수(`CLIENT_DEVICE_ID`)로만 제공한다. CLI 플래그(`--device-id` 등) 도입 금지.
- 검증: 모든 사용자‑스코프 작업은 `resolve_endpoint_uuid_for_device(device_id)` 검증을 선행해야 한다. 해석 실패 시 즉시 중단(Fail‑fast).
- 사용 범위: HTTP 요청/메타데이터로 전송하지 않는다. 서버‑사이드에서 엔드포인트/권한 선택에만 사용한다.
- 마스킹: 필요한 경우 해시(pseudonym)로만 기록하며, salt/정책은 운영에서 관리한다. 기본은 기록 금지.
- 회전/탈취 대응: 운영에서 `register_client_device`로 재등록(회전)하고, 구 매핑 무효화로 탈취를 차단한다. 애플리케이션은 변경을 자동 반영한다.

### User Identity Policy (MANDATORY)
- 표준 환경변수: `USER_EMAIL`을 사용자 신원(identity)으로 사용한다.
- 등록: `register_user_identity(email)`로 권위 사용자 레코드를 생성/업서트한다.
- 매핑: `link_device_to_user(device_id, email)`로 장치와 사용자를 연결한다(1:N 허용). 분리/회전은 운영에서 수행한다.
- 검증: 통신 전 `USER_EMAIL` 존재 여부를 검증하고, 로그/감사에 평문 이메일 노출을 최소화한다(필요 시 pseudonym).
- 조인(3NF): `user_identities` ↔ `client_devices` ↔ `llm_endpoints` ↔ `provider_credentials`로만 권위 해석 및 제출을 수행한다.

### Worker Model (TERMINOLOGY & MANDATORY)

- 정의(워커): 백그라운드에서 주기적으로 작업을 실행해 상태를 권위적으로 갱신하는 실행 주체. 이 프로젝트에서는 주로 pg_cron이 스케줄링하는 SQL/PL 함수가 워커이다.
- 책임 분리:
  - 워커가 “일”을 한다: 외부 시스템(LiteLLM Files/Batch API) 조회/제출, 상태 전환(queued→taken/processing→completed/failed), 결과 수집/집계, 재시도/백오프를 담당한다.
  - CLI는 “데이터를 보내는” 존재다: 입력 검증/등록/엔큐 등 최소한의 동작만 수행하고, 긴 루프/상태 전환/검증은 워커에 위임한다. CLI는 장시간 트랜잭션/폴링을 수행하지 않는다.
- 동시성/원자성:
  - 워커는 `FOR UPDATE SKIP LOCKED`/`RETURNING` 패턴, 리스 TTL(예: `lease_expires_at`)로 경쟁 조건을 통제한다.
  - 모든 처리 경로는 아이템포턴트(중복 실행해도 단일 결과 반영)로 설계한다.
- 폴링 규칙:
  - 권장: LISTEN/NOTIFY/웹훅이 가능하면 폴링을 최소화/대체한다.
  - 불가 시: 워커 내부에서만 적응형 폴링(초기 단축→간격 점증, `Retry-After` 활용)을 사용하고, CLI는 제출 즉시 반환한다.
- 키/보안:
  - 헤더 키는 `provider_credentials` 암호문을 device_uuid 기반으로 복호화해 주입한다(레드액션 로깅, 평문 미기록).
  - `com_config.llm_api_key`/ENCRYPTION_PASSPHRASE는 사용/보관하지 않는다.
- 스케줄(예시):
  - 파일 검증 워커: 10초 간격 `/v1/files/{id}` → processed/uploaded 확인 시 배치 생성.
  - 결과 수집 워커: 배치 상태 주기 조회→완료 시 output 파일 반영.
  - 메타/가격/헬스: 게이트웨이 모델/가격/헬스 정보를 일정 주기로 동기화.

### Worker Selection & Labeling Policy (MANDATORY)

- 라벨링 필수: 워커가 항목을 집어들면 반드시 라벨을 남긴다. 최소 필드: `taken_by`(워커/크론 식별자), `taken_at`(타임스탬프), `lease_expires_at`(리스 TTL 종료 시각), `taken_via`(`cron_worker`/`cli_fast_path`). 이벤트/테이블 모두 기록한다.
- 후보 선택은 JOIN 기반: 전역 큐에서 단순 스캔 금지. 다음을 조인해 결정적 마이크로배치를 만든다: `user_prompt_token_jobs` ↔ `user_prompt_token_job_groups` ↔ `user_prompt_records` ↔ `litellm_model_metadata`(엔드포인트 범위/토크나이저). 그룹 우선순위(예: `pending_records DESC`)로 선택 후 `FOR UPDATE SKIP LOCKED`로 확정한다.
- DONE 불변: `status='done'`은 자동 재큐 금지. 재큐는 콘텐츠 지문 변경 또는 운영자 명시 요청(별도 함수)일 때만 허용한다.
- 업서트 제한: 잡 엔큐 업서트의 `ON CONFLICT` 갱신은 `status IN ('pending','failed')`일 때만 허용한다. DONE은 그대로 유지한다.
- CLI/폴러는 상태 변경 금지: 제출/등록/엔큐만 수행한다. 상태 전환/검증/드레인은 워커만 수행한다.
- 리스/동시성: 워커는 리스 TTL(`lease_expires_at`)을 설정하고, 만료 전 재획득을 금지한다. 선택 직후 `status='processing'`으로 전환하며 라벨링을 동반한다.
- 감사/이벤트: 이벤트에는 `purpose('chat'|'batch')`, `group_uuid`, `endpoint_uuid`, `taken_via`를 포함해 재현 가능성을 확보한다. 평문 키는 로깅/이벤트에 포함하지 않는다.
- 테스트/검증: 모킹 금지(E2E만). 라벨링/선택 결과는 쿼리로 가시화 가능해야 한다(예: 최근 `taken_at` 순으로 검사, 이벤트 상호 비교).

### Cron Worker Architecture (MANDATORY)

- 목적: 모든 상태 전환/재처리를 "크론 워커"가 결정적으로 수행한다. CLI/폴러는 제출/등록/엔큐까지만 담당하며, 검증/디스패치/수집/재처리는 워커만 담당한다.

- 선택(Eligibility Gate → 확정):
  1) 조인 기반 후보 집합 생성(결정적 마이크로배치):
     - `user_prompt_token_jobs j`
     - `JOIN user_prompt_token_job_groups g USING (token_job_group_uuid)`
     - `JOIN user_prompt_records r USING (record_uuid)`
     - `JOIN litellm_model_metadata m ON (m.endpoint_uuid = g.endpoint_uuid AND m.model_mode='batch')`
  2) 처리 가능 조건(아키텍처 규칙):
     - `j.status IN ('pending','failed')`
     - OR `r.content_sha256 IS DISTINCT FROM j.last_processed_sha256` (콘텐츠 지문 변경)
     - OR `r.generation > j.generation` (세대 증가)
  3) 우선순위: `g.pending_records DESC`, `r.created_at ASC` 등으로 정렬 후 LIMIT N
  4) 확정: 위 선택 결과를 `FOR UPDATE SKIP LOCKED`로 잠그고 즉시 라벨링+전환
     - `j.status='processing'`
     - `j.taken_by='cron_worker:<jobname>'`, `j.taken_at=NOW()`
     - `j.lease_expires_at=NOW()+interval '30 seconds'`
     - `j.selection_reason IN ('pending','failed','fingerprint_changed','generation_advanced')`

- 처리(Processing):
  - 성공 시: `j.last_processed_sha256=r.content_sha256`, `j.generation=r.generation`, `j.status='done'`, `j.attempts = attempts+1`, `j.updated_at=NOW()`
  - 실패 시: `j.status='failed'`, `j.last_error=<err>`, `j.attempts = attempts+1`, `j.updated_at=NOW()`

- 리스/회수(Lease & Reclaim):
  - 리스 만료 회수: `j.status='processing' AND j.lease_expires_at < NOW()`인 항목을 워커가 회수하고 다시 선택 대상으로 포함(다음 틱에서 Eligibility Gate 재판정).
  - 워커는 자신이 집어든 항목만 완료/실패로 전환한다. 타 워커는 리스가 만료될 때까지 손대지 않는다.

- 이벤트/감사(Observability):
  - 워커는 선택 직후 및 완료/실패 시 이벤트에 JSON 메타를 기록한다:
    - `purpose`('chat'|'batch'), `group_uuid`, `endpoint_uuid`, `taken_via='cron_worker'`, `selection_reason` 위 4종, `taken_by`, `taken_at`
  - 평문 키/시크릿은 절대 기록하지 않는다.

- 샘플 선택/확정 SQL(개요):
  ```sql
  WITH candidates AS (
    SELECT j.record_uuid, j.tokenizer_name, j.token_job_group_uuid, g.endpoint_uuid,
           CASE
             WHEN j.status IN ('pending','failed') THEN 'pending'
             WHEN r.content_sha256 IS DISTINCT FROM j.last_processed_sha256 THEN 'fingerprint_changed'
             WHEN r.generation > j.generation THEN 'generation_advanced'
           END AS selection_reason
    FROM user_prompt_token_jobs j
    JOIN user_prompt_token_job_groups g USING (token_job_group_uuid)
    JOIN user_prompt_records r USING (record_uuid)
    JOIN litellm_model_metadata m ON m.endpoint_uuid=g.endpoint_uuid AND m.model_mode='batch'
    WHERE (
      j.status IN ('pending','failed') OR
      r.content_sha256 IS DISTINCT FROM j.last_processed_sha256 OR
      r.generation > j.generation
    )
    ORDER BY g.pending_records DESC, r.created_at ASC
    LIMIT 100
  )
  UPDATE user_prompt_token_jobs j
     SET status='processing', taken_by='cron_worker:token_drain', taken_at=NOW(),
         lease_expires_at=NOW()+interval '30 seconds',
         selection_reason=c.selection_reason,
         updated_at=NOW()
    FROM candidates c
   WHERE j.record_uuid=c.record_uuid AND j.tokenizer_name=c.tokenizer_name
   FOR UPDATE SKIP LOCKED
   RETURNING j.*;
  ```

- 스케줄/활성(Operational Gate):
  - pg_cron 잡은 `active=true`이고 `database=current_database()`로 설정되어야 한다.
  - 이름 예시: `cron_dispatch_user_prompt_token_groups`, `cron_enqueue_ready_batch_chunks`, `cron_dispatch_ready_batches` 등.

- 테스트(필수):
  - 모킹 금지(E2E). 병렬 워커 환경에서 라벨링/리스/회수가 기대대로 작동하는지 이벤트/조회 쿼리로 검증한다.

### Database Naming Policy (MANDATORY)

- 두 단어 이상 규칙: 애플리케이션이 생성/변경하는 모든 DB 객체(테이블/뷰/시퀀스/인덱스/함수/컬럼)는 최소 두 단어를 언더스코어(`_`)로 결합한 이름만 허용한다. 예) `provider` 금지, `model_provider` 허용.
- 소유 범위: 시스템 스키마(`pg_catalog`, `information_schema`, `pg_toast`, `cron`)와 확장 내부 객체는 예외로 한다.
- 실행 범위(가이드라인만): 본 정책은 가이드라인으로만 적용한다. DB 레벨 트리거/강제 차단은 사용하지 않는다(코드 리뷰/CI 린트로만 검증).
- 컬럼 포함: `CREATE TABLE` 시 컬럼명도 동일 정책을 준수한다(가이드라인 준수, 강제 차단 아님).
- 점진적 적용: 기존 단일 단어 객체는 즉시 리네임하지 않으며, 신규/변경 시에만 차단한다. 리네임은 별도 마이그레이션에서 수행한다.
- 문서/예외: 벤더 또는 표준 명칭이 필요한 경우(예: 확장/외부 시스템) 사전 승인 후 예외 목록에 추가한다.

#### "단어" 정의(정확 기준)
- 전체 형식: `snake_case`(소문자, 언더스코어로 구분).
- 최소 토큰 수: 2개 이상(예: `model_provider`, `request_status`).
- 토큰 규칙:
  - 시작 문자는 반드시 알파벳 `[a-z]`.
  - 허용 문자: 소문자 알파벳 `[a-z]` + 숫자 `[0-9]`만(하이픈/대문자/공백/기타 특수문자 금지).
  - 길이: 각 토큰은 최소 2자 이상(예: `id` 허용, 단 전체 이름은 2토큰 이상 필요).
  - 의미적 지향: 도메인+핵심명사 조합 권장(예: `gateway_provider`, `batch_status`).
- 예시:
  - 허용: `model_provider`, `user_device`, `endpoint_uuid`, `token_count`
  - 금지: `provider`, `status`, `uuid`(단일 토큰), `ModelProvider`(대문자), `model-provider`(하이픈)
- 예외: 벤더 고유명/표준 약어가 필요한 경우 사전 승인 후 예외로 사용.
