#!/bin/bash

# Database Backup Utility Script
# Helper script to manage the Docker database backup project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker and Docker Compose are installed
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

# Start all services
start_services() {
    log_info "Starting database backup services..."
    docker-compose up -d
    log_success "Services started successfully"
    
    log_info "Waiting for services to be ready..."
    sleep 10
    
    show_status
}

# Stop all services
stop_services() {
    log_info "Stopping database backup services..."
    docker-compose down
    log_success "Services stopped successfully"
}

# Restart services
restart_services() {
    log_info "Restarting database backup services..."
    docker-compose restart
    log_success "Services restarted successfully"
}

# Show service status
show_status() {
    log_info "Service status:"
    docker-compose ps
    echo
    
    log_info "Backup service logs (last 10 lines):"
    docker-compose logs --tail=10 backup-service
}

# View backup service logs
view_logs() {
    local lines=${1:-50}
    log_info "Showing backup service logs (last $lines lines):"
    docker-compose logs --tail=$lines -f backup-service
}

# List backup files
list_backups() {
    log_info "Backup files in ./backups directory:"
    
    if [ ! -d "./backups" ]; then
        log_warning "Backups directory does not exist yet"
        return
    fi
    
    # Count files
    local csv_count=$(find ./backups -name "*.csv" -type f | wc -l)
    local sql_count=$(find ./backups -name "*.sql" -type f | wc -l)
    local json_count=$(find ./backups -name "*.json" -type f | wc -l)
    local log_count=$(find ./backups -name "*.log" -type f | wc -l)
    
    echo "File counts:"
    echo "  CSV backups: $csv_count"
    echo "  SQL backups: $sql_count"
    echo "  Manifest files: $json_count"
    echo "  Log files: $log_count"
    echo
    
    # Show recent files
    echo "Recent backup files:"
    ls -la ./backups/ | head -20
    
    # Use backup manager if available
    log_info "Trying to use backup manager for detailed view..."
    docker-compose exec backup-service python backup_manager.py list 2>/dev/null || \
        log_warning "Backup manager not available (service may not be running)"
}

# Show backup statistics
show_backup_stats() {
    log_info "Getting backup statistics..."
    docker-compose exec backup-service python backup_manager.py stats 2>/dev/null || \
        log_error "Cannot get backup statistics (service may not be running)"
}

# Show backup details
show_backup_details() {
    local timestamp=$1
    log_info "Getting backup details..."
    
    if [ -n "$timestamp" ]; then
        docker-compose exec backup-service python backup_manager.py details --timestamp "$timestamp" 2>/dev/null || \
            log_error "Cannot get backup details (service may not be running)"
    else
        docker-compose exec backup-service python backup_manager.py details 2>/dev/null || \
            log_error "Cannot get backup details (service may not be running)"
    fi
}

# Cleanup old backups
cleanup_backups() {
    local days=${1:-7}
    local confirm=${2:-false}
    
    log_info "Cleaning up backups older than $days days..."
    
    if [ "$confirm" = "true" ]; then
        docker-compose exec backup-service python backup_manager.py cleanup --days "$days" --confirm 2>/dev/null || \
            log_error "Cannot cleanup backups (service may not be running)"
    else
        log_warning "Running in dry-run mode. Use 'cleanup $days true' to actually delete files."
        docker-compose exec backup-service python backup_manager.py cleanup --days "$days" 2>/dev/null || \
            log_error "Cannot cleanup backups (service may not be running)"
    fi
}

# Connect to MySQL database
connect_mysql() {
    log_info "Connecting to MySQL database..."
    if [ -z "$MYSQL_ROOT_PASSWORD" ]; then
        log_error "MYSQL_ROOT_PASSWORD is not set. Export it or load it from a .env file before running this command."
        exit 1
    fi
    docker-compose exec -e MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql mysql -u root
}

# Show database information
show_databases() {
    log_info "Available databases:"
    if [ -z "$MYSQL_ROOT_PASSWORD" ]; then
        log_error "MYSQL_ROOT_PASSWORD is not set. Export it or load it from a .env file before running this command."
        exit 1
    fi
    docker-compose exec -e MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql mysql -u root -e "SHOW DATABASES;" 2>/dev/null || \
        log_error "Cannot connect to database (service may not be running)"
}

# Force backup now
force_backup() {
    log_info "Forcing immediate backup by restarting backup service..."
    docker-compose restart backup-service
    log_success "Backup service restarted - backup should start shortly"
    
    log_info "Monitoring backup service logs..."
    sleep 5
    docker-compose logs --tail=20 backup-service
}

# Show help
show_help() {
    echo "Database Backup Utility Script"
    echo "=============================="
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  start              Start all services"
    echo "  stop               Stop all services"
    echo "  restart            Restart all services"
    echo "  status             Show service status"
    echo "  logs [lines]       View backup service logs (default: 50 lines)"
    echo "  list               List backup files"
    echo "  stats              Show backup statistics"
    echo "  details [timestamp] Show backup details (latest if no timestamp)"
    echo "  cleanup [days] [confirm] Cleanup old backups (default: 7 days, dry-run)"
    echo "  mysql              Connect to MySQL database"
    echo "  databases          Show available databases"
    echo "  backup             Force immediate backup"
    echo "  help               Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start           # Start all services"
    echo "  $0 logs 100        # Show last 100 log lines"
    echo "  $0 cleanup 14 true # Delete backups older than 14 days"
    echo "  $0 details         # Show latest backup details"
    echo
}

# Main script logic
case "$1" in
    "start")
        check_dependencies
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "status")
        show_status
        ;;
    "logs")
        view_logs "$2"
        ;;
    "list")
        list_backups
        ;;
    "stats")
        show_backup_stats
        ;;
    "details")
        show_backup_details "$2"
        ;;
    "cleanup")
        cleanup_backups "$2" "$3"
        ;;
    "mysql")
        connect_mysql
        ;;
    "databases")
        show_databases
        ;;
    "backup")
        force_backup
        ;;
    "help"|"")
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac