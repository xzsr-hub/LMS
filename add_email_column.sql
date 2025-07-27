-- Add email column to readers table if it doesn't exist
USE library_management;

-- Check if email column exists and add it if not
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                   WHERE TABLE_SCHEMA = 'library_management' 
                   AND TABLE_NAME = 'readers' 
                   AND COLUMN_NAME = 'email');

SET @sql = IF(@col_exists = 0, 
              'ALTER TABLE readers ADD COLUMN email VARCHAR(100) COMMENT "电子邮箱" AFTER phone',
              'SELECT "Email column already exists" as message');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;