---
inclusion: manual
---

# 테스트 전략

## Backend (Python/FastAPI)

### 단위 테스트
- pytest 사용
- 외부 의존성(Transcribe/Bedrock/DynamoDB)은 mock/fake로 대체
- 어댑터 패턴으로 테스트 용이성 확보

### REST API 테스트
```python
# httpx AsyncClient 사용
async def test_create_session():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/sessions")
        assert response.status_code == 201
```

### WebSocket 통합 테스트
- 핵심 이벤트 흐름 검증
- session.start → audio → transcript.partial → transcript.final → translation.final

## Frontend (React/TypeScript)

### 컴포넌트 테스트
- vitest + React Testing Library
- 사용자 인터랙션 중심 테스트

### 훅 테스트
```typescript
// renderHook 사용
const { result } = renderHook(() => useWebSocket(sessionId));
```

### E2E 테스트
- Playwright 사용
- 주요 시나리오:
  - 세션 시작/중지
  - 전사 이벤트 렌더링
  - 빠른 번역 입력/결과 표시
  - 질문 제안 클릭

## 테스트 커버리지 목표
- Backend: 80%+
- Frontend: 70%+
- E2E: 핵심 사용자 플로우 100%

## CI/CD 통합
- PR마다 테스트 실행
- 커버리지 리포트 생성
- E2E는 스테이징 환경에서 실행
