-- 统计特定题材的社交平台采纳率
SELECT 
    genre,
    COUNT(*) as total_circles,
    ROUND(SUM(CASE WHEN twitter_url IS NOT NULL AND twitter_url != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as twitter_pct,
    ROUND(SUM(CASE WHEN pixiv_url IS NOT NULL AND pixiv_url != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as pixiv_pct
FROM circles
GROUP BY genre
HAVING total_circles >= 50
ORDER BY twitter_pct DESC;
