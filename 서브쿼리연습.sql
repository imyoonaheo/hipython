#서브 쿼리의 활용 
USE WNTRADE;
SELECT  A.고객회사명, A.담당자명, A.마일리지
FROM 고객 A
LEFT JOIN 고객 B
ON A.마일리지 < B.마일리지
WHERE B.고객번호 IS NULL;


-- 셀프 조인
SELECT 고객번호, 마일리지
FROM 고객 
WHERE 마일리지 = (
	SELECT MAX(마일리지)
	FROM 고객 
); -- 최고 마일리지 값

-- LEFT JOIN 
SELECT  A.고객회사명, A.담당자명, A.마일리지, B.고객회사명, B.마일리지
FROM 고객 A
LEFT JOIN 고객 B
ON A.마일리지 < B.마일리지
-- WHERE B.고객번호 IS NULL
order by A. 마일리지 DESC;

-- 주문번호 = 'H0250'인 고객회사명, 담당자명 
SELECT 고객.고객회사명, 고객.담당자명
FROM 고객 JOIN 주문 ON 고객.고객번호 = 주문.고객번호
WHERE 주문번호 = 'H0250' ; 

-- SUBQUERY VERSION
SELECT 고객.고객회사명, 고객.담당자명
FROM 고객
WHERE 고객.고객번호 = ( SELECT 주문.고객번호
										FROM  주문 
                                        WHERE 주문.주문번호 = 'H0250');-- 주문번호 = 'H0250' 고객


-- '부산광역시' 고객의 최소 마일리지보다 더 큰 마일리지를 가진 고객 정보를 보이시오
SELECT 담당자명
, 고객회사명 
, 마일리지
FROM 고객 
WHERE 마일리지 > (
SELECT MIN(마일리지)
FROM 고객 
WHERE 도시 = '부산광역시'
);

-- 부산광역시 고객의 주문건수
SELECT *
FROM 주문
WHERE 고객번호 IN 
(SELECT 고객번호
FROM 고객 
WHERE 도시 = '부산광역시' 
);


-- ANY,ALL,EXIST
-- ANY
SELECT 담당자명, 고객회사명, 마일리지
FROM 고객 
WHERE 마일리지 > ANY (  -- 그값에 해당하는거 모두 가져와
SELECT 마일리지
FROM 고객 
WHERE 도시 = '부산광역시'
); -- 58 ROWS / MIN [5건]


-- ALL 
SELECT 담당자명, 고객회사명, 마일리지
FROM 고객 
WHERE 마일리지 > ALL (  -- 그값에 해당하는거 모두 가져와
SELECT 마일리지
FROM 고객 
WHERE 도시 = '부산광역시'
); -- 17 ROWS / MAX[5건]

-- EXIST
SELECT 담당자명, 고객회사명, 마일리지
FROM 고객 a
WHERE exists (  -- 조건이 서브쿼리 자체에 들어간다. 
	SELECT 1
	FROM 고객 b
	WHERE 도시 = '부산광역시' AND a. 마일리지 > b.  마일리지
); -- 58 ROWS


-- 조건절에서 사용하는 서브쿼리
SELECT 도시
, AVG(마일리지) AS 평균마일리지
FROM 고객
GROUP BY 도시 
HAVING AVG(마일리지) > (SELECT AVG(마일리지) 
										FROM 고객
);

-- 인라인뷰
SELECT 담당자명
, 고객회사명
, 마일리지
, 고객.도시
, 도시_평균마일리지
, 도시_평균마일리지 - 마일리지 AS 차이
FROM 고객
, (SELECT 도시
, AVG(마일리지) AS 도시_평균마일리지
FROM 고객
GROUP BY 도시
) AS 도시별요약
WHERE 고객.도시 = 도시별요약. 도시;

-- 스칼라 서브쿼리
SELECT 고객번호
, 담당자명
, (SELECT MAX(주문일)
FROM 주문 
WHERE 주문.고객번호 = 고객.고객번호
) AS 최종주문일 
FROM 고객; 

-- CTE
WITH 도시별요약 AS
( 
SELECT 도시
, AVG(마일리지) AS 도시_평균마일리지
FROM 고객
GROUP BY 도시
)
SELECT 담당자명
, 고객회사명
, 마일리지
, 고객.도시
, 도시_평균마일리지
, 도시_평균마일리지 - 마일리지 AS 차이 
FROM 고객 
, 도시별요약
WHERE 고객.도시 = 도시별요약.도시; 
