/*
테이블 갯수 1개 -> 심플쿼리 
2개 이상 -> 조인 
크로스 조인(카테지안프로덕트 연산) M개 X N개 = MN 개 결과를 반환 
내부 조인(이너조인) 조건에 만족하는 데이터만 반환 - 동등조인, 비동등조인
**/

-- CROSS JOIN
SELECT 부서.부서번호 AS 부서부서번호
, 사원.부서번호 AS 사원부서번호
, 이름
, 부서명
FROM 부서 JOIN 사원
WHERE 이름 = '배재용' ;

-- INNER JOIN 
SELECT 부서.부서번호 AS 부서부서번호
, 사원.부서번호 AS 사원부서번호
, 이름
, 부서명
FROM 부서 JOIN 사원
ON 부서.부서번호 = 사원.부서번호
WHERE 이름 = '배재용';

-- 주문, 고객 JOIN
SELECT 주문번호, 고객회사명, 주문일
FROM 주문 JOIN 고객
ON 주문.고객번호 = 고객.고객번호
WHERE 주문.고객번호 = 'ITCWH';

-- 주문 사원 INNER JOIN 주문번호별 담당자를 볼 수 있음
SELECT 주문번호, 주문.사원번호, 고객번호, 사원.이름 -- *
FROM 주문 JOIN 사원
ON 주문.사원번호 = 사원.사원번호;

-- 고객, 제품 > 크로스조인
SELECT 고객회사명, 제품명
FROM 고객 JOIN 제품; 

-- 고객, 마일리지등급 - 비동등조인
SELECT 고객.고객회사명, 고객.마일리지, 마일리지등급.등급명
FROM 고객 JOIN 마일리지등급
ON 고객.마일리지 BETWEEN 마일리지등급.하한마일리지 AND 마일리지등급.상한마일리지;

-- 5-2 예제
SELECT 사원번호
, 직위
, 사원.부서번호
, 부서명
FROM 사원 JOIN 부서
ON 사원.부서번호 = 부서.부서번호
WHERE 이름 = '이소미';

-- 5-3 예제
SELECT 고객.고객번호
,담당자명
,고객회사명
,COUNT(*)AS 주문건수
FROM 고객 JOIN 주문 
ON 고객.고객번호 = 주문.고객번호
GROUP BY 고객.고객번호
, 담당자명
, 고객회사명
ORDER BY count(*) DESC;

USE WNTRADE;

-- 사원입사일 이후 처리한 주문 조회

SELECT 주문번호
, 이름 AS 사원명
, 입사일
, 주문일
FROM 주문 JOIN 사원
ON 주문.사원번호 = 사원.사원번호 
AND 주문.주문일 >= 사원.입사일;

-- 고객회사들이 주문한 건수 집계 > 건수가 많은 순서로 출력
SELECT 고객회사명
, COUNT(*) AS 주문건수
FROM 고객 JOIN 주문
ON 고객.고객번호 =주문.고객번호
GROUP BY 고객.고객회사명 -- 고객. 고객번호
ORDER BY COUNT(*) DESC;

-- 고객회사별 주문금액 합, 큰 금액 순으로 출력 
SELECT 고객회사명
, SUM(주문수량*단가) AS 주문금액
FROM 고객 JOIN 주문
ON 고객.고객번호 =주문.고객번호
JOIN 주문세부
ON 주문.주문번호 = 주문세부.주문번호
GROUP BY 고객회사명
ORDER BY 2 desc;


SELECT 사원번호, 이름, 부서명 
FROM 사원 LEFT JOIN 부서
ON 사원.부서번호 = 부서.부서번호;

-- 사원이 없는 부서
SELECT 이름
, 부서.*
FROM 사원 RIGHT JOIN 부서
ON 사원.부서번호 = 부서.부서번호
WHERE 사원.부서번호 IS NULL;

-- 주문 안한 고객
SELECT 주문                           
FROM 고객 RIGHT JOIN 주문
ON 고객.고객번호 = 주문.고객번호
WHERE 주문.주문수량 IS NULL;


