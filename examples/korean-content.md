# 인공지능 시대의 문서 처리

이 문서는 한국어 처리를 테스트하기 위한 예제 문서입니다.

**마크다운 처리의 중요성**

최근 LLM(Large Language Model)의 발전으로 문서 생성이 자동화되고 있습니다. 하지만 생성된 문서는 종종 구조적 문제를 가지고 있습니다.

특히 **볼드체**를 제목 대신 사용하는 경우가 많아, 문서의 계층 구조가 불명확해지는 문제가 있습니다.

## 문서 전처리

### 구조 정규화

문서의 구조를 정규화하는 것은 다음과 같은 이유로 중요합니다:

- 마크다운 뷰어에서 올바른 목차 생성
- 자동화된 문서 처리 파이프라인과의 호환성
- 검색 엔진 최적화 (SEO)
- 접근성 개선

**텍스트 정제**

원본 문서에는 불필요한 공백, 중복된 줄바꿈, 일관성 없는 들여쓰기 등이 포함될 수 있습니다. 이러한 요소들을 제거하면 문서의 품질이 향상됩니다.

### 의미론적 분할

문서를 의미 있는 단위로 분할하는 것은 RAG 시스템에서 특히 중요합니다.

한국어 문서의 경우 다음과 같은 특성을 고려해야 합니다:
- 조사와 어미의 다양성
- 띄어쓰기 규칙의 복잡성
- 한자어와 외래어의 혼용

**임베딩 생성**

문서 청크를 벡터로 변환하는 과정입니다. embeddinggemma와 같은 모델을 사용하면 로컬 환경에서도 효율적으로 임베딩을 생성할 수 있습니다.

## 검색 및 재정렬

### 의미론적 검색

키워드 기반 검색과 달리, 의미론적 검색은 문서의 의미를 이해하고 관련성 있는 결과를 반환합니다.

예를 들어 "인공지능"을 검색하면 "AI", "머신러닝", "딥러닝" 등의 관련 개념도 함께 찾을 수 있습니다.

**유사도 계산**

두 벡터 간의 코사인 유사도를 계산하여 의미적 관련성을 측정합니다:

```python
import numpy as np

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """두 벡터의 코사인 유사도 계산"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

### 청크 재정렬

문서 청크를 의미론적 유사도에 따라 재정렬하면 더 자연스러운 흐름을 만들 수 있습니다.

두 가지 주요 방법이 있습니다:
1. 순차적 재정렬: 시작 청크에서 가장 유사한 청크로 이어지는 체인 생성
2. 토픽 클러스터링: K-means 등의 알고리즘으로 주제별 그룹화

**클러스터링 예제**

```python
from sklearn.cluster import KMeans

# 청크들을 3개 토픽으로 그룹화
kmeans = KMeans(n_clusters=3, random_state=42)
labels = kmeans.fit_predict(embeddings)

# 각 클러스터별로 청크 정렬
for cluster_id in range(3):
    cluster_chunks = [chunk for chunk, label in zip(chunks, labels) if label == cluster_id]
    print(f"클러스터 {cluster_id}: {len(cluster_chunks)}개 청크")
```

## 중복 제거

### 중복 감지

임베딩 유사도가 매우 높은(예: 0.95 이상) 청크들은 중복 또는 거의 중복일 가능성이 높습니다.

**병합 전략**

중복된 청크를 처리하는 방법:
- 규칙 기반: 가장 긴 청크를 선택하거나 최신 버전을 유지
- LLM 기반: Gemma 2B 같은 소형 모델로 내용을 지능적으로 병합

LLM 기반 병합의 장점:
- 두 청크의 고유한 정보를 모두 보존
- 자연스러운 문장으로 재구성
- 중복 표현 제거

### 효율성

중복 제거를 통해 다음과 같은 이점을 얻을 수 있습니다:
- 저장 공간 절약 (10-30%)
- 검색 속도 향상
- 처리 비용 감소

## 성능 최적화

**로컬 모델 사용**

클라우드 API 대신 로컬 모델을 사용하면:
- 비용 절감 (API 호출 비용 제거)
- 프라이버시 보호 (데이터가 외부로 전송되지 않음)
- 지연 시간 감소 (네트워크 왕복 시간 제거)
- 오프라인 작업 가능

**GPU 메모리 관리**

소비자용 GPU(2-4GB VRAM)에서 효율적으로 작동하려면:
1. 모델을 순차적으로 로드
2. 사용 후 메모리에서 언로드
3. 배치 크기 조정
4. 그래디언트 체크포인팅 활용

## 실전 활용 사례

### RAG 시스템 구축

검색 증강 생성(Retrieval-Augmented Generation) 시스템에서 Markdown Reallocator를 활용할 수 있습니다:

1. LLM이 생성한 문서를 전처리
2. 의미론적으로 청크 분할
3. 중복 제거로 데이터베이스 최적화
4. 검색 성능 향상

### 문서 정리 자동화

기술 문서나 블로그 포스트를 자동으로 정리:
- 형식 오류 수정
- 관련 섹션 재배치
- 중복 내용 병합
- 일관된 스타일 적용

**배치 처리**

여러 문서를 한 번에 처리하려면:

```python
from markdown_reallocator import MarkdownPreprocessor, MarkdownSplitter
from pathlib import Path

preprocessor = MarkdownPreprocessor()
splitter = MarkdownSplitter()

# 모든 마크다운 파일 처리
for md_file in Path("docs").glob("**/*.md"):
    content = md_file.read_text(encoding="utf-8")
    cleaned = preprocessor.preprocess(content)
    chunks = splitter.split(cleaned)
    print(f"{md_file.name}: {len(chunks)}개 청크 생성")
```

## 결론

Markdown Reallocator는 LLM 시대에 필수적인 문서 처리 도구입니다. 로컬 환경에서 효율적으로 작동하며, 다양한 언어를 지원합니다.

특히 한국어 문서 처리에서도 우수한 성능을 보여주며, 실제 프로덕션 환경에서 활용 가능합니다.

## 참고 자료

- [LangChain 한국어 문서](https://python.langchain.com/docs/get_started/introduction)
- [한국어 자연어 처리](https://github.com/ko-nlp/awesome-korean-nlp)
- [임베딩 모델 비교 연구](https://arxiv.org/abs/2212.03533)
