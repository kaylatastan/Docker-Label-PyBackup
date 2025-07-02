#!/usr/bin/env python3
"""
Database Backup Manager
A utility script to manage and monitor database backups
"""

import os
import json
import datetime
import argparse
from pathlib import Path

class BackupManager:
    def __init__(self, backup_dir="/app/backups"):
        self.backup_dir = Path(backup_dir)
        if not self.backup_dir.exists():
            print(f"Backup directory not found: {backup_dir}")
            exit(1)

    def list_backups(self):
        """List all backup files with details"""
        manifests = list(self.backup_dir.glob("backup_manifest_*.json"))
        
        if not manifests:
            print("No backup manifests found.")
            return
        
        print(f"{'Backup Date':<20} {'Databases':<15} {'Files':<10} {'Format':<10}")
        print("-" * 65)
        
        for manifest_file in sorted(manifests, reverse=True):
            try:
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                
                backup_date = manifest.get('backup_date', 'Unknown')
                databases = list(manifest.get('databases', {}).keys())
                db_count = len(databases)
                backup_format = manifest.get('backup_format', 'Unknown')
                
                # Count total files
                file_count = 0
                for db_info in manifest.get('databases', {}).values():
                    file_count += len(db_info.get('tables', {}))
                    if db_info.get('full_backup'):
                        file_count += 1
                
                print(f"{backup_date:<20} {db_count:<15} {file_count:<10} {backup_format:<10}")
                
            except Exception as e:
                print(f"Error reading {manifest_file}: {e}")

    def show_backup_details(self, timestamp=None):
        """Show detailed information about a specific backup"""
        if timestamp:
            manifest_file = self.backup_dir / f"backup_manifest_{timestamp}.json"
        else:
            # Get the latest backup
            manifests = list(self.backup_dir.glob("backup_manifest_*.json"))
            if not manifests:
                print("No backup manifests found.")
                return
            manifest_file = max(manifests, key=os.path.getctime)
        
        if not manifest_file.exists():
            print(f"Backup manifest not found: {manifest_file}")
            return
        
        try:
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            print(f"Backup Details")
            print("=" * 50)
            print(f"Timestamp: {manifest.get('backup_timestamp')}")
            print(f"Date: {manifest.get('backup_date')}")
            print(f"Host: {manifest.get('database_host')}:{manifest.get('database_port')}")
            print(f"Format: {manifest.get('backup_format')}")
            print()
            
            for db_name, db_info in manifest.get('databases', {}).items():
                print(f"Database: {db_name}")
                print("-" * 30)
                
                if db_info.get('full_backup'):
                    backup_file = Path(db_info['full_backup'])
                    size = backup_file.stat().st_size if backup_file.exists() else 0
                    print(f"  Full Backup: {backup_file.name} ({size:,} bytes)")
                
                tables = db_info.get('tables', {})
                if tables:
                    print(f"  Table Backups: {len(tables)} tables")
                    for table_name, table_file in tables.items():
                        backup_file = Path(table_file)
                        size = backup_file.stat().st_size if backup_file.exists() else 0
                        print(f"    {table_name}: {backup_file.name} ({size:,} bytes)")
                print()
                
        except Exception as e:
            print(f"Error reading backup details: {e}")

    def cleanup_backups(self, days=7, dry_run=False):
        """Remove backup files older than specified days"""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)
        cutoff_timestamp = cutoff_time.timestamp()
        
        backup_files = []
        for pattern in ['*.csv', '*.sql', '*.json']:
            backup_files.extend(self.backup_dir.glob(pattern))
        
        old_files = []
        for file_path in backup_files:
            if file_path.stat().st_mtime < cutoff_timestamp:
                old_files.append(file_path)
        
        if not old_files:
            print(f"No backup files older than {days} days found.")
            return
        
        print(f"Found {len(old_files)} files older than {days} days:")
        
        total_size = 0
        for file_path in old_files:
            size = file_path.stat().st_size
            total_size += size
            print(f"  {file_path.name} ({size:,} bytes)")
        
        print(f"\nTotal size to be removed: {total_size:,} bytes")
        
        if dry_run:
            print("\n[DRY RUN] Files would be deleted with --confirm flag")
        else:
            print("\nRemoving files...")
            removed_count = 0
            for file_path in old_files:
                try:
                    file_path.unlink()
                    removed_count += 1
                    print(f"  Removed: {file_path.name}")
                except Exception as e:
                    print(f"  Error removing {file_path.name}: {e}")
            
            print(f"\nCleanup completed: {removed_count}/{len(old_files)} files removed")

    def backup_statistics(self):
        """Show backup statistics"""
        manifests = list(self.backup_dir.glob("backup_manifest_*.json"))
        
        if not manifests:
            print("No backup manifests found.")
            return
        
        total_backups = len(manifests)
        databases = set()
        total_files = 0
        total_size = 0
        
        formats = {}
        
        for manifest_file in manifests:
            try:
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                
                backup_format = manifest.get('backup_format', 'unknown')
                formats[backup_format] = formats.get(backup_format, 0) + 1
                
                for db_name, db_info in manifest.get('databases', {}).items():
                    databases.add(db_name)
                    
                    # Count files and sizes
                    if db_info.get('full_backup'):
                        backup_file = Path(db_info['full_backup'])
                        if backup_file.exists():
                            total_files += 1
                            total_size += backup_file.stat().st_size
                    
                    for table_file in db_info.get('tables', {}).values():
                        backup_file = Path(table_file)
                        if backup_file.exists():
                            total_files += 1
                            total_size += backup_file.stat().st_size
                            
            except Exception as e:
                print(f"Error reading {manifest_file}: {e}")
        
        print("Backup Statistics")
        print("=" * 40)
        print(f"Total Backup Sessions: {total_backups}")
        print(f"Unique Databases: {len(databases)}")
        print(f"Total Backup Files: {total_files}")
        print(f"Total Storage Used: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
        print()
        print("Backup Formats:")
        for fmt, count in formats.items():
            print(f"  {fmt}: {count} sessions")
        print()
        print("Databases:")
        for db in sorted(databases):
            print(f"  {db}")

def main():
    parser = argparse.ArgumentParser(description="Database Backup Manager")
    parser.add_argument("--backup-dir", default="/app/backups", 
                       help="Backup directory path (default: /app/backups)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    subparsers.add_parser("list", help="List all backups")
    
    # Details command
    details_parser = subparsers.add_parser("details", help="Show backup details")
    details_parser.add_argument("--timestamp", help="Backup timestamp (default: latest)")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Remove old backup files")
    cleanup_parser.add_argument("--days", type=int, default=7, 
                               help="Remove files older than N days (default: 7)")
    cleanup_parser.add_argument("--confirm", action="store_true", 
                               help="Actually remove files (default: dry run)")
    
    # Stats command
    subparsers.add_parser("stats", help="Show backup statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = BackupManager(args.backup_dir)
    
    if args.command == "list":
        manager.list_backups()
    elif args.command == "details":
        manager.show_backup_details(args.timestamp)
    elif args.command == "cleanup":
        manager.cleanup_backups(args.days, dry_run=not args.confirm)
    elif args.command == "stats":
        manager.backup_statistics()

if __name__ == "__main__":
    main()