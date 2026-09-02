-- Standardize all user-visible agronomy wording on "soil moisture".
SET NAMES utf8mb4;

UPDATE management_task_template
SET title = REPLACE(REPLACE(title, '土壤墒情', '土壤湿度'), '墒情', '土壤湿度'),
    note = REPLACE(REPLACE(note, '土壤墒情', '土壤湿度'), '墒情', '土壤湿度')
WHERE title LIKE '%墒情%' OR note LIKE '%墒情%';

UPDATE management_task
SET title = REPLACE(REPLACE(title, '土壤墒情', '土壤湿度'), '墒情', '土壤湿度'),
    note = REPLACE(REPLACE(note, '土壤墒情', '土壤湿度'), '墒情', '土壤湿度')
WHERE title LIKE '%墒情%' OR note LIKE '%墒情%';
