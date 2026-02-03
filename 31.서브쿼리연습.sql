#서브 쿼리의 활용 
USE WNTRADE;
SELECT  A.고객회사명, A.담당자명, A.마일리지
FROM 고객 A
LEFT JOIN 고객 B
ON A.마일리지 < B.마일리지
WHERE B.고객번호 IS NULL;