-- 提取特定日期的 Block 社团题材构成
SELECT 
    day, 
    hall, 
    block, 
    genre, 
    COUNT(*) as circle_count 
FROM circles 
WHERE block = 'ア' 
GROUP BY day, hall, block, genre 
ORDER BY day, circle_count DESC;
