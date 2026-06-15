-- 提取含有简介且长度大于 10 的社团文本源
SELECT 
    id, 
    name, 
    genre, 
    description 
FROM circles 
WHERE description IS NOT NULL 
  AND LENGTH(description) > 10;
