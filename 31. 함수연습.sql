USE WNTRADE;

-- 단일행 함수 
-- 1. 문자형함수
-- 2. 숫자형함수
-- 3.
-- 4.
-- 5. 

SELECT field('JAVA', 'SQL', 'JAVA', 'C')
, find_in_set('JAVA', 'SQL,JAVA,C')
, instr('네 인생을 살아라', '인생')
, locate('인생', '네 인생을 살아라');

SELECT field('오땅', '홈런볼', '오땅', '초콜릿'); 
select replace('ABC-DEF', '-', '*');
SELECT reverse('ABCDEF');

SELECT now(), sysdate(); -- 현재 날짜시간
SELECT curdate(), curtime();

SELECT now() AS 'START', SLEEP(5), now() AS 'END';
SELECT sysdate() AS 'START', SLEEP(5), sysdate() AS 'END';

SELECT 고객번호, IF (마일리지>1000, 'VIP', 'GOLD') AS 등급
FROM 고객;

SELECT 주문수량, IF(12500 * 450 > 500000, '초과달성', '미달성')
FROM 주문세부;

/*
* 주문금액 = 단가 * 주문수량
* 주문금액
**/

SELECT 주문번호
, 단가
, 주문수량
, 단가 * 주문수량 AS 주문금액
, CASE 
		WHEN 단가 * 주문수량 >= 5000000 THEN '초과달성'
        WHEN 단가 * 주문수량 >= 4000000 THEN '달성'
        ELSE '미달성'
END AS 달성여부
FROM 주문세부;

-- 마일리지 등급 부여 VIP, GOLD, SILVER, BRONZE
SELECT 고객번호
, 담당자명 AS 고객명
,마일리지
, CASE 
		WHEN 마일리지 >= 100000 THEN 'VIP'
        WHEN 마일리지 >= 50000 THEN 'GOLD'
        WHEN 마일리지 >= 20000 THEN 'SILVER' 
        ELSE 'BRONZE'
END AS 마일리지등급 
FROM 고객;

-- 부서코드 > 부서명으로

SELECT 사원번호
,이름
,부서번호
,CASE 부서번호
    WHEN 부서번호 = 'A1' THEN '영업부'
    WHEN 부서번호 = 'A2' THEN '기획부'
    WHEN 부서번호 = 'A3' THEN '개발부'
    WHEN 부서번호 = 'A4' THEN '홍보부'
    ELSE '미배정'
END AS 부서명
FROM 사원;

-- 주문 테이블에 배송상태 추가 
-- 발송일 컬럼 기준, '배송대기' '빠른배송' '일반배송'으로 설정
SELECT 주문번호
,주문일
,발송일
,CASE
    WHEN 발송일 IS NULL THEN '배송대기'
    WHEN DATEDIFF(발송일, 주문일) <= 2 THEN '빠른배송'
    ELSE '일반배송'
  END AS 배송상태
FROM 주문;

/*연습1. 고객회사명 앞2글자 '*' 마스킹 처리
 * 연습2. 주문세부 정보중 주문금액, 할인금액, 실제주문금액 출력(1단위에서 버림)
 * 연습3. 전체 사원의 이름, 생일, 만나이, 입사일, 입사일수, 입사500일기념일 출력
 * 연습4. 고객 정보의 도시컬럼을 '대도시', '도시'로 구분하고 마일리지 VVIP, VIP, 일반고객 구분
 * 연습5. 주문테이블의 주문일을 주문년도, 분기, 월, 일, 요일, 한글요일로 출력
 * 연습6. 발송일이 요청일보다 7일 이상 늦은 주문건 출력
 * */

SELECT 도시
, count(고객번호)
, count(도시)
, count(distinct 지역)
, sum(마일리지)
, avg(마일리지)
, min(마일리지)
FROM 고객
-- WHERE 도시 LIKE '서울%'
GROUP BY 도시;

#고객 담당자 이름 묶어보기
SELECT 담당자직위
, 도시
, count(고객번호)
, SUM(마일리지)
, avg(마일리지)
FROM 고객
GROUP BY 담당자직위, 도시
ORDER BY 1,2; 
# 1,2번이 뭔지 모르겠삼. 

-- GROUP BY 조건 
-- 고객 - 도시별로 그룹 - 고객수, 평균마일리지, 고객수가 > 10만 추출
SELECT 도시
,count(고객번호) as 고객수
, avg(마일리지) as 평균마일리지
FROM 고객
GROUP BY 도시
HAVING count(고객번호) > 10;

-- 고객번호 t로 시작하는 고객을 도시별로 묶어 마일리지 합 출력, 단  1000 이상만 
SELECT 도시
, sum(마일리지)
FROM 고객
WHERE 고객번호 LIKE 'T%'
GROUP BY 도시
HAVING SUM(마일리지) >= 1000;

-- 광역시 고객, 담당자 직위별로 최대마일리지, 단, 1만점 이상 레코드만 출력
SELECT 담당자직위
, max(마일리지)
FROM 고객
WHERE 도시 LIKE '%광역시'
GROUP BY 담당자직위 
HAVING MAX(마일리지) >= 10000;
-- GROUP BY 에 들어가지 않는 컬럼은 나올 수 없음. GROUPING한 값이 아니기 때문

SELECT 담당자직위
, max(마일리지)
FROM 고객
WHERE 도시 LIKE '%광역시'
GROUP BY 담당자직위
WITH ROLLUP -- 총계 행이 추가
HAVING MAX(마일리지) >= 10000;


-- 연습1. 담당자 직위에 마케팅이 있는 고객의 담당자직위, 도시별 고객수 출력 
-- 단, 담당자직위별 고객수와 전체 고객수도 출력
-- 연습2. 제품 주문년도별 주문건수 출력
-- 연습 3. 주문년도, 분기별 주문건수 합계 출력