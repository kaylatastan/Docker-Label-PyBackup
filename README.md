# Docker Database Backup Project

An automated MySQL/MariaDB backup service using Docker containers with comprehensive backup features and Docker label-aware metadata.

## Features

### 🔄 Automatic Backup
- **Scheduled Backups**: Configurable backup intervals (default: every 6 hours)
- **Multiple Formats**: Support for CSV and SQL backup formats
- **Continuous Operation**: Runs as a background service with automatic restarts

### 🏷️ Comprehensive Labeling
- **Database Metadata**: Each backup includes database name, table name, and backup timestamp
- **Backup Manifest**: JSON manifest file with complete backup information
- **Record Count**: Number of records backed up for each table
- **Format Information**: Clear indication of backup format and structure

### 📊 Multi-Database Support
- **Auto-Discovery**: Automatically detects and backs up all user databases
- **Table-Level Backups**: Individual CSV backups for each table
- **Full Database Backups**: Complete SQL dumps with triggers and routines
- **System Database Filtering**: Excludes MySQL system databases

### 🏷️ **Docker Label Integration**
- **Label-Aware Metadata**: Reads Docker container labels for enhanced backup information
- **Service Discovery**: Automatically incorporates container metadata into backups
- **Priority-Based Scheduling**: Honors backup priority settings from container labels
- **Retention Management**: Uses container-defined retention policies

### 🧹 Maintenance Features
- **Automatic Cleanup**: Removes backup files older than 7 days
- **Logging**: Comprehensive logging to file and console
- **Health Monitoring**: Database connection monitoring and retry logic

## Project Structure

```
traefik-project/
├── backup-service/
│   ├── app.py              # Main backup service application
│   ├── Dockerfile          # Docker configuration for backup service
│   └── requirements.txt    # Python dependencies
├── mysql-init/
│   ├── init.sql           # Initial database schema and data
│   └── 02_additional_data.sql # Additional test data
├── backups/               # Backup files storage (mounted volume)
├── mysql-data/           # MySQL data directory (mounted volume)
├── docker-compose.yml    # Docker services configuration
└── README.md            # This documentation
```

## Quick Start

### 1. Start the Services
```bash
docker-compose up -d
```

### 2. Monitor Backup Service
```bash
# View backup service logs
docker-compose logs -f backup-service

# Check backup files
ls -la backups/
```

### 3. Access Database (Optional)
```bash
# Connect to MySQL
docker exec -it mysql mysql -u root -p
# Password: rootpassword
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `mysql` | Database hostname |
| `DB_PORT` | `3306` | Database port |
| `DB_USER` | `root` | Database username |
| `DB_PASSWORD` | ***| Database password |
| `BACKUP_INTERVAL_HOURS` | `6` | Backup frequency in hours |
| `BACKUP_FORMAT` | `both` | Backup format: `csv`, `sql`, or `both` |

### Docker Labels Configuration

The system uses Docker labels to enhance backup metadata and behavior:

#### Database Container Labels
```yaml
labels:
  - "backup.enabled=true"                    # Enable backup for this container
  - "backup.database.type=mysql"             # Database type identifier
  - "backup.database.name=mysql-database"    # Friendly database name
  - "backup.database.version=mariadb-10.6"   # Database version
  - "backup.retention.days=30"               # Retention period in days
  - "backup.priority=high"                   # Backup priority (high/normal/low)
```

#### Backup Service Labels
```yaml
labels:
  - "service.type=backup"                    # Service type identifier
  - "service.name=database-backup-service"   # Service name
  - "service.backup.formats=csv,sql"         # Supported backup formats
  - "service.backup.schedule=every-6-hours"  # Backup schedule
  - "service.backup.retention=7-days"        # Default retention
  - "service.monitoring=enabled"             # Enable monitoring
  - "service.logs=enabled"                   # Enable logging
```

### Backup Formats

#### CSV Format
- Individual files for each table
- Includes metadata headers with database info and Docker labels
- Human-readable format
- Example: `sampledb_products_backup_20241229_220000.csv`

#### SQL Format
- Complete database dumps
- Includes structure, data, triggers, and routines
- Enhanced with Docker label metadata in comments
- Can be restored directly to MySQL
- Example: `sampledb_full_backup_20241229_220000.sql`

## Backup File Structure

### CSV Backup Example
```csv
# Database Backup Metadata
# Database: sampledb
# Table: products
# Backup Time: 2024-12-29 22:00:00
# Record Count: 10
# Format: CSV
# Container Labels:
#   Database Type: mysql
#   Database Name: mysql-database
#   Database Version: mariadb-10.6 #mariadb yerine mysql de kullanılabilir ama mysql corrector hata verip duruyor
#   Backup Priority: high
#   Retention Days: 30

id,name,price,description
1,Laptop,1200.00,High performance laptop
2,Smartphone,800.00,Latest model smartphone
```

### Backup Manifest Example
```json
{
  "backup_timestamp": "20241229_220000",
  "backup_date": "2024-12-29 22:00:00",
  "database_host": "mysql",
  "database_port": 3306,
  "backup_format": "both",
  "container_labels": {
    "backup.enabled": "true",
    "backup.database.type": "mysql",
    "backup.database.name": "mysql-database",
    "backup.database.version": "mariadb-10.6",
    "backup.retention.days": "30",
    "backup.priority": "high"
  },
  "service_metadata": {
    "database_type": "mysql",
    "database_name": "mysql-database",
    "database_version": "mariadb-10.6",
    "backup_priority": "high",
    "retention_days": "30",
    "backup_enabled": "true"
  },
  "databases": {
    "sampledb": {
      "tables": {
        "products": "/app/backups/sampledb_products_backup_20241229_220000.csv",
        "categories": "/app/backups/sampledb_categories_backup_20241229_220000.csv"
      },
      "full_backup": "/app/backups/sampledb_full_backup_20241229_220000.sql"
    }
  }
}
```

## Database Schema

### Sample Databases
1. **sampledb**: E-commerce product catalog
   - `products`: Product information
   - `categories`: Product categories

2. **okul**: School management system
   - `ogrenciler`: Student records

## Monitoring and Maintenance

### Log Files
- **Location**: `backups/backup.log`
- **Content**: Backup operations, errors, and status messages
- **Rotation**: Automatic cleanup of old log entries

### Backup Retention
- **Default Retention**: 7 days
- **Automatic Cleanup**: Runs after each backup cycle
- **File Types**: Removes `.csv`, `.sql`, and `.json` files older than retention period

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check if MySQL container is running: `docker-compose ps`
   - Verify database credentials in docker-compose.yml
   - Wait for database initialization (first startup may take time)

2. **Permission Issues**
   - Ensure backup directory has proper permissions
   - Check Docker volume mounts

3. **Backup Files Missing**
   - Check backup service logs: `docker-compose logs backup-service`
   - Verify backup directory permissions
   - Ensure sufficient disk space

### Manual Backup
```bash
# Trigger manual backup (restart the service)
docker-compose restart backup-service
```

### Database Access
```bash
# MySQL shell access
docker exec -it mysql mysql -u root -prootpassword

# Show databases
SHOW DATABASES;

# Use specific database
USE sampledb;
SHOW TABLES;
```

## Development

### Adding New Databases
1. Add SQL scripts to `mysql-init/` directory
2. Restart MySQL container: `docker-compose restart mysql`
3. Backup service will automatically detect new databases

### Custom Backup Schedule
Modify `BACKUP_INTERVAL_HOURS` in docker-compose.yml:
```yaml
environment:
  - BACKUP_INTERVAL_HOURS=12  # Backup every 12 hours
```

### Backup Format Selection
```yaml
environment:
  - BACKUP_FORMAT=sql    # Only SQL dumps
  - BACKUP_FORMAT=csv    # Only CSV exports
  - BACKUP_FORMAT=both   # Both formats (default)
```

## Security Considerations

- Database passwords are stored in plain text in docker-compose.yml
- For production use, consider using Docker secrets or environment files
- Backup files may contain sensitive data - secure the backup directory
- Network access is restricted to Docker internal network

## License


This project is provided as-is for educational and development purposes.
