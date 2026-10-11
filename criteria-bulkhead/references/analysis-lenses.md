# 분석 기준 카탈로그

## 사용법

이 문서는 빠짐없이 채울 설문지가 아니다. 먼저 문제의 영향과 현재 흐름을 복원한 뒤, 주 기준 2~4개와 교차 기준을 선택하라. 각 질문을 **대상·조건·수치·시간·실패 결과**로 답하라. 근거가 없으면 미확인으로 표시하고 계측 또는 판별 실험을 제안하라.

## 1. 정확성·불변식

- 절대 깨지면 안 되는 비즈니스·데이터 규칙은 무엇인가?
- 입력 검증, 상태 전이, 계산, 저장, 전달 중 어디서 위반될 수 있는가?
- 중복, 누락, 순서 역전, 부분 적용, 반올림, 시간대·시계 오차가 결과를 바꾸는가?
- 실패 후 원상 복구, 보상, 수동 교정 중 무엇이 가능한가?
- 정확성을 논리적 처리 완료, 영속화, 외부 반영 중 어디까지로 보는가?

## 2. 정합성·동시성

- 어떤 데이터와 불변식에 정합성이 필요한가? 모든 데이터에 같은 수준이 필요한가?
- 단일 쓰기 주체인가, 여러 쓰기 주체인가? 충돌 시 권위와 승자 규칙은 무엇인가?
- read-your-writes, monotonic reads, causal order, bounded staleness 중 사용자에게 실제 필요한 보장은 무엇인가?
- 트랜잭션 범위와 격리 수준은 무엇이며 dirty/non-repeatable/phantom read, lost update, write skew가 가능한가?
- optimistic/pessimistic lock, CAS, unique constraint, serialization 중 어디서 충돌을 검출하는가?
- 복제 지연·캐시·비동기 처리에서 stale state를 얼마나 오래 허용할 수 있는가?
- 강한 정합성의 지연·가용성 비용과 eventual consistency의 충돌·보상 비용 중 무엇을 감당하는가?

## 3. 성능·용량

### 워크로드

- 읽기/쓰기 비율, 요청 형태, payload와 레코드 크기, fan-out/fan-in은 어떠한가?
- steady, burst, peak, 성장률, skew, hot key·hot partition은 어떠한가?
- 동시 사용자/연결/작업 수와 도착률은 얼마인가?

### 경로와 자원

- critical path에 직렬 단계, round trip, 동기 I/O가 몇 개인가?
- CPU 계산·압축·암호화·직렬화, 메모리 allocation·GC·working set, 디스크 IOPS·throughput·fsync, 네트워크 RTT·대역폭 중 무엇이 지배적인가?
- lock·connection pool·thread/event loop·file descriptor·queue·rate limit 중 포화 지점은 어디인가?
- 캐시 hit rate와 miss penalty, index selectivity, scan 범위, batching 효과는 어떠한가?

### 지표

- throughput과 latency를 함께 보았는가? p50뿐 아니라 p95/p99와 timeout 비율은 어떠한가?
- service time과 queue wait를 분리했는가? Little's Law(`L = λW`)로 동시 작업·대기 증가가 설명되는가?
- 평균 부하가 아니라 포화 직전과 overload에서 어떻게 무너지는가?
- 최적화가 다른 자원, 쓰기 비용, tail latency, 정확성으로 병목을 이동시키는가?

## 4. 확장성·탄력성

- 무엇이 늘어나는가: 사용자, QPS, 데이터, tenant, 지역, 기능, 팀?
- 수직/수평 확장 중 어느 축이며 상태·세션·락·로컬 디스크가 수평 확장을 막는가?
- 파티션 키가 분포·지역성·쿼리 패턴과 맞는가? 재샤딩과 hot partition 비용은 어떠한가?
- 병렬화 가능한 비율과 직렬 병목은 얼마인가? Amdahl의 법칙상 기대 이득이 제한되는가?
- autoscaling 신호가 실제 병목보다 늦거나 흔들리지 않는가? cold start와 scale-in 중단은 어떤 영향을 주는가?
- 데이터와 조직의 소유 경계가 함께 확장되는가, 중앙 병목이 남는가?

## 5. 가용성·신뢰성·내구성

- 어떤 기능에 어떤 SLI/SLO가 필요한가? 전체 평균이 핵심 사용자 여정을 숨기지 않는가?
- 단일 장애점과 공통 장애 원인은 무엇인가? 복제본도 같은 region, control plane, credential, 배포에 묶여 있는가?
- failover가 자동인지, 탐지와 전환에 얼마나 걸리며 split-brain 위험은 무엇인가?
- retry budget, timeout hierarchy, circuit breaking, load shedding, backpressure가 조화를 이루는가?
- RTO/RPO는 무엇인가? backup이 아니라 실제 restore와 replay가 검증됐는가?
- 프로세스 재시작, 노드·AZ·region 상실, 의존성 저하, 자격 증명 만료에서 지속되는가?
- 목표 SLO보다 의존성 조합의 가용성이 낮지 않은가?

## 6. 실패·복구·저하 모드

- crash, omission, timeout, 느린 응답, corrupt response, Byzantine/악성 입력을 구분했는가?
- 각 단계가 성공했는지 모르는 **모호한 실패**에서 재시도하면 중복되는가? idempotency key와 deduplication의 범위·보존 기간은 무엇인가?
- 부분 성공 뒤 rollback, compensation, roll-forward 중 무엇을 하는가?
- queue backlog, retry storm, thundering herd, cascading failure를 무엇이 증폭하는가?
- 기능을 끄거나 품질을 낮춰 핵심 경로를 살릴 수 있는가? degraded mode의 정확성은 무엇인가?
- 복구 순서와 속도가 재오염·재과부하를 만들지 않는가?

## 7. 데이터·스토리지·수명주기

- source of truth는 어디이며 파생 데이터·인덱스·캐시는 어떻게 재생성하는가?
- access pattern에 맞는 모델과 인덱스인가? 읽기 최적화가 write amplification과 저장 비용을 얼마나 만드는가?
- 데이터 생성, 변경, 보존, archive, 삭제, 복구의 수명주기는 무엇인가?
- schema evolution, backfill, dual-write에서 구·신 버전이 공존 가능한가?
- 데이터 크기보다 cardinality, skew, tombstone, fragmentation, compaction이 문제인가?
- 개인정보 삭제와 백업·로그·캐시의 잔존이 충돌하지 않는가?

## 8. 네트워크·분산 시스템

- 호출 수, RTT, 대역폭, packet loss, connection setup, DNS/TLS 비용이 경로에 어떤 영향을 주는가?
- 네트워크 단절을 실패와 구분할 수 있는가? timeout 뒤 원격 작업의 완료 여부는 어떻게 아는가?
- 메시지 전달 보장은 at-most/at-least/effectively-once 중 무엇이며 소비자의 멱등성이 맞물리는가?
- 순서 보장의 범위가 partition/key/global 중 어디까지 필요한가?
- quorum과 replica 배치가 latency, failure tolerance, stale read에 미치는 영향은 무엇인가?
- clock skew와 시간 기반 만료·정렬·lease가 안전한가?
- CAP/PACELC는 실제 partition과 평시 latency/consistency 선택을 설명할 때만 적용하라.

## 9. 보안·개인정보·오용

- 자산, 행위자, 신뢰 경계, 공격 면은 무엇인가?
- 인증과 인가가 모든 경로·tenant·객체 수준에서 일관적인가?
- 입력 검증, injection, SSRF, replay, credential leakage, privilege escalation 가능성은 무엇인가?
- 암호화의 전송/저장 범위와 키 회전·폐기·접근 감사는 가능한가?
- rate limit과 quota가 공격뿐 아니라 noisy neighbor를 격리하는가?
- 수집 최소화, 보존 기간, 삭제, 마스킹, 데이터 지역성과 규제 요구는 무엇인가?
- 안전장치가 가용성·운영·사용성에 만드는 비용은 무엇인가?

## 10. 운영성·관측 가능성

- 문제를 사용자보다 먼저 감지할 수 있는가? symptom 지표와 cause 지표를 구분했는가?
- 로그·메트릭·트레이스가 같은 요청·작업·데이터 변경을 correlation할 수 있는가?
- high cardinality, sampling, retention 때문에 결정적 증거가 사라지는가?
- alert가 행동 가능하며 SLO/error budget과 연결되는가?
- runbook, ownership, escalation, feature flag, kill switch, 수동 교정 도구가 있는가?
- 배포·설정·schema 변경의 영향과 rollback 가능성을 관측할 수 있는가?

## 11. 변경 용이성·호환성·마이그레이션

- 어떤 변경이 자주 일어나며 어느 컴포넌트·팀까지 파급되는가?
- API, event, schema의 하위/상위 호환성과 버전 공존 기간은 무엇인가?
- big-bang 없이 expand-contract, backfill, shadow, dual-read/write가 가능한가?
- 롤백 시 데이터 형식과 상태가 이전 코드와 호환되는가?
- 추상화가 실제 변화 축을 격리하는가, 단지 간접 계층을 늘리는가?
- 테스트 가능성과 국소 추론 가능성이 개선되는가?

## 12. 비용·효율

- 비용을 요청, 사용자, tenant, 저장 GB, 전송 GB, 운영 인시던트 단위로 볼 수 있는가?
- compute, memory, storage, egress, managed service, license, on-call·운영 인력 중 지배 비용은 무엇인가?
- peak를 위한 유휴 용량과 autoscaling/cold start 사이의 대가는 무엇인가?
- 캐시·복제·인덱스·로그·백업이 만드는 중복 비용은 정당한가?
- 복잡성 비용과 공급자 종속, 이탈 비용을 포함했는가?
- 최적화가 총비용을 줄이는지 다른 항목으로 옮기는지 확인했는가?

## 13. 사용자·제품·조직 맥락

- 기술 현상이 실제로 어떤 사용자 여정과 결과를 훼손하는가?
- 모든 사용자가 같은 보장을 필요로 하는가? tier·지역·기능별 차등이 가능한가?
- 더 단순한 제품 규칙이나 UX로 기술 제약을 완화할 수 있는가?
- 소유 팀, 의사결정 권한, on-call, 배포 주기가 아키텍처 경계와 맞는가?
- 운영자가 감당할 수 없는 복잡성을 도입하지 않는가?
- build/buy, 출시 시점, 학습 비용, 규제·계약 제약이 선택을 바꾸는가?

## 14. 엣지 케이스를 찾는 생성 규칙

무작위로 사례를 나열하지 말고 각 축의 경계값과 조합을 생성하라.

- 값: 0, 1, 최대, 최대 초과, null, 빈 값, 중복, 잘못된 형식, 매우 큰 값
- 시간: 동시에, 직전/직후, 만료 경계, 재시작 중, 배포 전환 중, clock skew
- 순서: 역순, 누락, 중복, 지연, replay, 오래된 이벤트 뒤 최신 이벤트
- 상태: 최초, 중간, 완료, 취소, 실패 후 재개, 부분 성공
- 부하: idle, steady, burst, overload, hot key, noisy neighbor
- 의존성: 빠른 실패, 느린 실패, timeout, 부분 응답, corrupt 응답, 복구 직후
- 권한·소유: 다른 tenant, 권한 변경 직후, 삭제된 사용자, 소유권 이전 중
- 버전: 구 client/신 server, 신 client/구 server, mixed schema, rollback

가장 위험한 조합부터 테스트하라. 가능성만 낮고 영향도 낮은 조합을 모두 구현하려 하지 마라.

## 기반 원리를 연결하는 법

원리의 이름, 적용 대상, 관측 연결, 선택의 대가를 한 묶음으로 설명하라.

> 도착률이 처리율에 가까워지면서 queue wait가 비선형으로 늘고 있다. 따라서 CPU 미세 최적화보다 admission control과 backpressure가 tail latency를 제한한다. 대신 일부 요청을 명시적으로 거부하거나 지연해야 한다.

유용한 원리 후보는 큐잉과 Little's Law, Amdahl의 법칙, locality와 working set, contention과 serialization, ACID·격리 이상, idempotency와 delivery semantics, replication·quorum·consensus, partitioning과 skew, cache invalidation, flow control·backpressure, failure detector와 lease다. 문제와 연결되지 않으면 언급하지 마라.
