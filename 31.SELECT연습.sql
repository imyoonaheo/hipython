USE WNTRADE;
SELECT * FROM wntrade.사원;
select * from 고객;
#select 고객번호, 고객회사명 
#from 고객;
select 고객번호
	,고객회사명 as 이름
	,담당자명
	,마일리지 as 포인트
from 고객;

select 이름 as 직원명, 주소, 직위 
from 사원;

# select * from wntrade.제품;
SELECT 제품명
	, 단가
	,단가*재고 AS "주문가능금액"
	,재고 AS "구맥가능수량!!" -- *
FROM 제품;

SELECT 제품번호
, FORMAT(단가,0) AS 단가
, 주문수량
, FORMAT (단가*주문수량,0) AS 주문금액
, 할인율
, FORMAT(단가*주문수량*할인율,0) AS 할인금액
FROM 주문세부
ORDER BY 6 DESC
LIMIT 10;

SELECT 고객번호
,담당자명 
,마일리지
FROM 고객
WHERE 마일리지 >= 10000;

USE WNTRADE;
SELECT 제품명
, 재고
FROM 제품
WHERE 단가*재고 > 100000
ORDER BY 1 DESC; -- 어센딩ASC(기본) 디센딩 DESC

#사원인 직원의 이름과 입사일 정보 출력
SELECT 사원번호
, 이름
, 직위
, 입사일
FROM 사원;

SELECT*
FROM 고객
LIMIT 3;

SELECT *
FROM 고객
ORDER BY 마일리지 DESC
LIMIT 3;

# 연습문제
SELECT *
FROM 부서
ORDER BY 부서명 DESC
LIMIT 4;

SELECT *
FROM 사원
ORDER BY 직위 ASC
LIMIT 5;

SELECT *
FROM 제품
WHERE 단가 > 100
ORDER BY 단가
LIMIT 10;

SELECT DISTINCT 도시
FROM 고객;
-- WHERE 도시 = '광명시';

SELECT 23 + 5 AS '더하기'
, 23 - 5 AS '빼기'
, 23*5
, 23/5
, 23 DIV 5
, 23 % 5
, 23 MOD 5
FROM 고객;

SELECT '오늘의 고객은', CURRENT_DATE, 담당자명
FROM 고객;

SELECT 23 > 5
, 23 <= 5
, 23 > 23
, 23 < 23
, 23 = 23
, 23 != 23
, 23 <> 23;

SELECT * 
FROM 고객
WHERE 담당자직위 = '대표 이사';

# 2020년 이전 주문일 확인하기

SELECT * 
FROM 주문
WHERE 주문일 < '2021-01-01';
DESCRIBE 주문;

SELECT *
FROM 고객
WHERE 도시 = '부산광역시'
AND 마일리지 < 1000;

-- 서울, 마일리지 5000점 이상
SELECT *
FROM 고객
WHERE 도시 = '서울특별시'
AND 마일리지 >= 5000;

-- 서울이거나 마일리지 1만점 이상
SELECT *
FROM 고객
WHERE 도시 = '서울특별시'
OR 마일리지 >= 10000;

-- 서울특별시가 아닌 고객
SELECT *
FROM 고객
WHERE 도시 <> '서울특별시';

-- 서울이 아니면서 마일리지 5천점 이상
SELECT *
FROM 고객
WHERE 도시 <> '서울특별시'
AND 마일리지 >= 5000;

-- 서울특별시와 부산광역시 사는 고객
SELECT *
FROM 고객
WHERE 도시 = '서울특별시'
OR 도시 = '부산광역시';

SELECT 고객번호
,담당자명
,마일리지
,도시
FROM 고객
WHERE 도시 = '부산광역시'
UNION
SELECT 고객번호
,담당자명
,마일리지
,도시
FROM 고객
WHERE 마일리지 < 1000
ORDER BY 1;

-- 단가가 5000 이상이거나 할인율이 0.5 이상인 주문
SELECT 단가 FROM 제품
WHERE 단가 >= 5000
UNION
SELECT 할인율 FROM 주문세부
WHERE 할인율 >= 0.5;

-- 고객 도시, 사원 도시를 모두 출력
SELECT 도시 FROM 고객
UNION
SELECT 도시 FROM 사원;

SELECT*FROM 고객 WHERE 지역 IS NULL;
SELECT DISTINCT 지역 FROM 고객;
SELECT * FROM 고객 WHERE 지역 = '';
SELECT * FROM 고객 ORDER BY 지역 = ''DESC, 도시;

#IN과 BETWEEN...AND 연산자
SELECT 고객번호
,담당자명
,담당자직위 
FROM 고객
WHERE 담당자직위 = '영업 과장'
OR 담당자직위 = '마케팅 과장';

SELECT 고객번호
,담당자명
,담당자직위
FROM 고객
WHERE 담당자직위 IN('영업 과장', '마케팅 과장');

#부서가 A1, A2인 사원
SELECT* FROM 사원 WHERE 부서번호 IN('A1','A2');

#주문일이 2020-06-01 ~ 2020-06-11
SELECT*FROM 주문 WHERE 주문일 BETWEEN '2020-06-01'AND'2020-06-11';