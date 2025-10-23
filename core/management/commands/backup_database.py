# management/commands/backup_database.py
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
import os
from datetime import datetime

class Command(BaseCommand):
    help = 'Backup MySQL database using pure Python'

    def handle(self, *args, **options):
        db_settings = settings.DATABASES['default']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'db_backup_{timestamp}.sql'
        
        try:
            with connection.cursor() as cursor:
                # Get all tables
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                
                backup_content = []
                backup_content.append("-- MySQL Database Backup")
                backup_content.append(f"-- Generated: {timestamp}")
                backup_content.append(f"-- Database: {db_settings['NAME']}")
                backup_content.append("SET FOREIGN_KEY_CHECKS=0;\n")
                
                for table in tables:
                    # Get table structure
                    cursor.execute(f"SHOW CREATE TABLE `{table}`")
                    create_table_sql = cursor.fetchone()[1]
                    backup_content.append(f"\n-- Table structure for table `{table}`")
                    backup_content.append(f"DROP TABLE IF EXISTS `{table}`;")
                    backup_content.append(create_table_sql + ";")
                    
                    # Get table data
                    cursor.execute(f"SELECT * FROM `{table}`")
                    rows = cursor.fetchall()
                    
                    if rows:
                        backup_content.append(f"\n-- Dumping data for table `{table}`")
                        
                        # Get column names
                        cursor.execute(f"DESCRIBE `{table}`")
                        columns = [col[0] for col in cursor.fetchall()]
                        
                        for row in rows:
                            values = []
                            for value in row:
                                if value is None:
                                    values.append("NULL")
                                elif isinstance(value, (int, float)):
                                    values.append(str(value))
                                else:
                                    # Escape special characters
                                    value_str = str(value).replace("'", "''").replace("\\", "\\\\")
                                    values.append(f"'{value_str}'")
                            
                            insert_sql = f"INSERT INTO `{table}` ({', '.join([f'`{col}`' for col in columns])}) VALUES ({', '.join(values)});"
                            backup_content.append(insert_sql)
                
                backup_content.append("\nSET FOREIGN_KEY_CHECKS=1;")
                
                # Write to file
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(backup_content))
                
                self.stdout.write(
                    self.style.SUCCESS(f'Backup created successfully: {backup_file}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Backup failed: {e}')
            )