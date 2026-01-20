import os
import time
import datetime
import mysql.connector
import csv
import json
import schedule
import subprocess
import logging
import docker
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/backups/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_HOST = os.environ.get('DB_HOST', 'mysql')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
BACKUP_DIR = '/app/backups'
BACKUP_INTERVAL = int(os.environ.get('BACKUP_INTERVAL_HOURS', 24))  # Default: 24 hours
BACKUP_FORMAT = os.environ.get('BACKUP_FORMAT', 'both')  # csv, sql, or both

if not DB_PASSWORD:
    raise RuntimeError(
        "DB_PASSWORD is not set. Provide it via environment variables (recommended via a local .env file)."
    )

class DatabaseBackupService:
    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.docker_client = None
        self.container_labels = {}
        self.ensure_backup_directory()
        self.load_container_metadata()
        
    def load_container_metadata(self):
        """Load Docker container labels and metadata"""
        try:
            self.docker_client = docker.from_env()
            
            # Get MySQL container metadata
            mysql_container = self.docker_client.containers.get(DB_HOST)
            self.container_labels = mysql_container.labels
            
            logger.info(f"Loaded container labels for {DB_HOST}")
            logger.info(f"Database type: {self.container_labels.get('backup.database.type', 'unknown')}")
            logger.info(f"Database version: {self.container_labels.get('backup.database.version', 'unknown')}")
            
        except Exception as e:
            logger.warning(f"Could not load Docker metadata: {e}")
            self.container_labels = {}

    def ensure_backup_directory(self):
        """Create backup directory if it doesn't exist"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            logger.info(f"Created backup directory: {self.backup_dir}")

    def wait_for_db(self) -> bool:
        """Wait for database to be available"""
        logger.info("Waiting for database connection...")
        for attempt in range(30):
            try:
                conn = mysql.connector.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    user=DB_USER,
                    password=DB_PASSWORD
                )
                conn.close()
                logger.info("Database connection established")
                return True
            except Exception as e:
                logger.warning(f"Database connection attempt {attempt + 1}/30 failed: {e}")
                time.sleep(5)
        
        logger.error("Database not available after 30 attempts")
        return False

    def get_databases(self) -> List[str]:
        """Get list of databases excluding system databases"""
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD
            )
            cursor = conn.cursor()
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Filter out system databases
            exclude_dbs = {'information_schema', 'performance_schema', 'mysql', 'sys'}
            db_list = [db[0] for db in databases if db[0] not in exclude_dbs]
            logger.info(f"Found databases: {db_list}")
            return db_list
        except Exception as e:
            logger.error(f"Error getting databases: {e}")
            return []

    def get_tables(self, database: str) -> List[str]:
        """Get list of tables in a database"""
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=database
            )
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            cursor.close()
            conn.close()
            
            table_list = [table[0] for table in tables]
            logger.info(f"Database '{database}' tables: {table_list}")
            return table_list
        except Exception as e:
            logger.error(f"Error getting tables for database {database}: {e}")
            return []

    def backup_table_to_csv(self, database: str, table: str, timestamp: str) -> str:
        """Backup a single table to CSV format"""
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=database
            )
            cursor = conn.cursor()
            
            # Get table data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Create backup file with proper labels
            backup_file = f"{self.backup_dir}/{database}_{table}_backup_{timestamp}.csv"
            
            with open(backup_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write metadata header with Docker labels
                writer.writerow([f"# Database Backup Metadata"])
                writer.writerow([f"# Database: {database}"])
                writer.writerow([f"# Table: {table}"])
                writer.writerow([f"# Backup Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([f"# Record Count: {len(rows)}"])
                writer.writerow([f"# Format: CSV"])
                
                # Add Docker container labels
                if self.container_labels:
                    writer.writerow([f"# Container Labels:"])
                    writer.writerow([f"#   Database Type: {self.container_labels.get('backup.database.type', 'unknown')}"])
                    writer.writerow([f"#   Database Name: {self.container_labels.get('backup.database.name', 'unknown')}"])
                    writer.writerow([f"#   Database Version: {self.container_labels.get('backup.database.version', 'unknown')}"])
                    writer.writerow([f"#   Backup Priority: {self.container_labels.get('backup.priority', 'normal')}"])
                    writer.writerow([f"#   Retention Days: {self.container_labels.get('backup.retention.days', '7')}"])
                
                writer.writerow([])  # Empty row separator
                
                # Write column headers
                writer.writerow(columns)
                
                # Write data
                writer.writerows(rows)
            
            cursor.close()
            conn.close()
            
            logger.info(f"CSV backup completed: {backup_file} ({len(rows)} records)")
            return backup_file
            
        except Exception as e:
            logger.error(f"Error backing up table {database}.{table} to CSV: {e}")
            return None

    def backup_database_to_sql(self, database: str, timestamp: str) -> str:
        """Backup entire database to SQL format using mysqldump"""
        try:
            backup_file = f"{self.backup_dir}/{database}_full_backup_{timestamp}.sql"
            
            # Create mysqldump command
            cmd = [
                'mysqldump',
                f'--host={DB_HOST}',
                f'--port={DB_PORT}',
                f'--user={DB_USER}',
                '--single-transaction',
                '--routines',
                '--triggers',
                database
            ]
            
            # Add metadata comments to SQL file
            with open(backup_file, 'w') as f:
                f.write(f"-- Database Backup Metadata\n")
                f.write(f"-- Database: {database}\n")
                f.write(f"-- Backup Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Format: SQL\n")
                f.write(f"-- Generated by: MySQL Database Backup Service\n")
                
                # Add Docker container labels
                if self.container_labels:
                    f.write(f"-- Container Labels:\n")
                    f.write(f"--   Database Type: {self.container_labels.get('backup.database.type', 'unknown')}\n")
                    f.write(f"--   Database Name: {self.container_labels.get('backup.database.name', 'unknown')}\n")
                    f.write(f"--   Database Version: {self.container_labels.get('backup.database.version', 'unknown')}\n")
                    f.write(f"--   Backup Priority: {self.container_labels.get('backup.priority', 'normal')}\n")
                    f.write(f"--   Retention Days: {self.container_labels.get('backup.retention.days', '7')}\n")
                
                f.write(f"\n")
                
                # Execute mysqldump and write to file
                env = dict(os.environ)
                # Avoid passing the password via process args; mysqldump reads it from MYSQL_PWD.
                env['MYSQL_PWD'] = DB_PASSWORD
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, env=env)
                
                if result.returncode != 0:
                    logger.error(f"mysqldump failed: {result.stderr}")
                    return None
            
            logger.info(f"SQL backup completed: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Error backing up database {database} to SQL: {e}")
            return None

    def create_backup_manifest(self, backup_info: Dict[str, Any], timestamp: str):
        """Create a manifest file with backup metadata"""
        manifest_file = f"{self.backup_dir}/backup_manifest_{timestamp}.json"
        
        manifest = {
            "backup_timestamp": timestamp,
            "backup_date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "database_host": DB_HOST,
            "database_port": DB_PORT,
            "backup_format": BACKUP_FORMAT,
            "container_labels": self.container_labels,
            "service_metadata": {
                "database_type": self.container_labels.get('backup.database.type', 'unknown'),
                "database_name": self.container_labels.get('backup.database.name', 'unknown'),
                "database_version": self.container_labels.get('backup.database.version', 'unknown'),
                "backup_priority": self.container_labels.get('backup.priority', 'normal'),
                "retention_days": self.container_labels.get('backup.retention.days', '7'),
                "backup_enabled": self.container_labels.get('backup.enabled', 'false')
            },
            "databases": backup_info
        }
        
        try:
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"Backup manifest created: {manifest_file}")
        except Exception as e:
            logger.error(f"Error creating backup manifest: {e}")

    def cleanup_old_backups(self, retention_days: int = 7):
        """Remove backup files older than retention_days"""
        try:
            cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
            removed_count = 0
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff_time:
                    if filename.endswith(('.csv', '.sql', '.json')):
                        os.remove(file_path)
                        removed_count += 1
                        logger.info(f"Removed old backup: {filename}")
            
            if removed_count > 0:
                logger.info(f"Cleanup completed: {removed_count} old backup files removed")
            
        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")

    def perform_backup(self):
        """Perform complete database backup"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Starting backup process at {datetime.datetime.now()}")
        
        if not self.wait_for_db():
            logger.error("Cannot connect to database, backup aborted")
            return
        
        databases = self.get_databases()
        if not databases:
            logger.warning("No databases found to backup")
            return
        
        backup_info = {}
        
        for database in databases:
            logger.info(f"Backing up database: {database}")
            db_backup_info = {
                "tables": {},
                "full_backup": None
            }
            
            # SQL backup (full database)
            if BACKUP_FORMAT in ['sql', 'both']:
                sql_backup = self.backup_database_to_sql(database, timestamp)
                if sql_backup:
                    db_backup_info["full_backup"] = sql_backup
            
            # CSV backup (individual tables)
            if BACKUP_FORMAT in ['csv', 'both']:
                tables = self.get_tables(database)
                for table in tables:
                    csv_backup = self.backup_table_to_csv(database, table, timestamp)
                    if csv_backup:
                        db_backup_info["tables"][table] = csv_backup
            
            backup_info[database] = db_backup_info
        
        # Create backup manifest
        self.create_backup_manifest(backup_info, timestamp)
        
        # Cleanup old backups
        self.cleanup_old_backups()
        
        logger.info("Backup process completed successfully")

    def run_scheduler(self):
        """Run the backup scheduler"""
        logger.info(f"Starting backup scheduler - backup interval: {BACKUP_INTERVAL} hours")
        
        # Schedule backup every N hours
        schedule.every(BACKUP_INTERVAL).hours.do(self.perform_backup)
        
        # Perform initial backup
        self.perform_backup()
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

if __name__ == "__main__":
    backup_service = DatabaseBackupService()
    backup_service.run_scheduler()