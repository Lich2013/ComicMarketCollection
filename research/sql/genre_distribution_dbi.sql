-- 全局题材分布与 DBI 计算
SELECT 
    genre,
    COUNT(*) as circle_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM circles WHERE genre IS NOT NULL AND genre != ''), 2) as ratio
FROM circles
WHERE genre IS NOT NULL AND genre != ''
GROUP BY genre
ORDER BY circle_count DESC;
