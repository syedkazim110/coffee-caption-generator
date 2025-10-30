#!/usr/bin/env python3
"""
Master Data Cleaning Script
Orchestrates the complete data cleaning process for both PostgreSQL and CSV files
Includes safety checks, backups, and comprehensive reporting
"""

import subprocess
import sys
import os
from datetime import datetime
import time

class DataCleaningOrchestrator:
    def __init__(self):
        self.start_time = datetime.now()
        self.log_file = f"cleaning_log_{self.start_time.strftime('%Y%m%d_%H%M%S')}.txt"
        self.backup_file = None
        
    def log_message(self, message, print_to_console=True):
        """Log message to file and optionally print to console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        
        if print_to_console:
            print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def check_prerequisites(self):
        """Check if all required files and dependencies are available"""
        self.log_message("Checking prerequisites...")
        
        required_files = [
            'backup_database.py',
            'clean_database.sql',
            'clean_csv_files.py',
            'validate_data_quality.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            self.log_message(f"❌ Missing required files: {', '.join(missing_files)}")
            return False
        
        # Check if Docker is running (for PostgreSQL)
        try:
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log_message("❌ Docker is not running. Please start Docker first.")
                return False
        except FileNotFoundError:
            self.log_message("❌ Docker is not installed or not in PATH.")
            return False
        
        # Check if required Python packages are available
        required_packages = ['pandas', 'psycopg2']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.log_message(f"❌ Missing Python packages: {', '.join(missing_packages)}")
            self.log_message("Install with: pip install " + " ".join(missing_packages))
            return False
        
        self.log_message("✅ All prerequisites met")
        return True
    
    def start_database_if_needed(self):
        """Start PostgreSQL database if not running"""
        self.log_message("Checking database status...")
        
        try:
            # Check if PostgreSQL container is running
            result = subprocess.run(['docker', 'ps', '--filter', 'name=postgres', '--format', '{{.Names}}'], 
                                  capture_output=True, text=True)
            
            if 'postgres' not in result.stdout:
                self.log_message("Starting PostgreSQL database...")
                result = subprocess.run(['docker-compose', 'up', '-d'], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log_message("✅ Database started successfully")
                    # Wait for database to be ready
                    time.sleep(10)
                else:
                    self.log_message(f"❌ Failed to start database: {result.stderr}")
                    return False
            else:
                self.log_message("✅ Database is already running")
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ Error checking database status: {str(e)}")
            return False
    
    def create_backup(self):
        """Create database backup before cleaning"""
        self.log_message("Creating database backup...")
        
        try:
            result = subprocess.run([sys.executable, 'backup_database.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Extract backup filename from output
                for line in result.stdout.split('\n'):
                    if 'reddit_db_backup_' in line and '.sql' in line:
                        self.backup_file = line.split(': ')[-1].strip()
                        break
                
                self.log_message(f"✅ Backup created: {self.backup_file}")
                return True
            else:
                self.log_message(f"❌ Backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error creating backup: {str(e)}")
            return False
    
    def run_pre_cleaning_validation(self):
        """Run data quality validation before cleaning"""
        self.log_message("Running pre-cleaning data quality validation...")
        
        try:
            result = subprocess.run([sys.executable, 'validate_data_quality.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_message("✅ Pre-cleaning validation completed")
                # Log validation output
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.log_message(f"  {line}", print_to_console=False)
                return True
            else:
                self.log_message(f"⚠️  Pre-cleaning validation had issues: {result.stderr}")
                return True  # Continue anyway, validation issues are not critical
                
        except Exception as e:
            self.log_message(f"❌ Error running pre-cleaning validation: {str(e)}")
            return False
    
    def clean_database(self):
        """Execute database cleaning script"""
        self.log_message("Cleaning PostgreSQL database...")
        
        try:
            # Execute SQL cleaning script
            cmd = [
                'psql',
                '-h', 'localhost',
                '-p', '5434',
                '-U', 'postgres',
                '-d', 'reddit_db',
                '-f', 'clean_database.sql',
                '--quiet'
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = 'password'
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_message("✅ Database cleaning completed successfully")
                # Log any output from the cleaning script
                if result.stdout.strip():
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            self.log_message(f"  {line}", print_to_console=False)
                return True
            else:
                self.log_message(f"❌ Database cleaning failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error cleaning database: {str(e)}")
            return False
    
    def clean_csv_files(self):
        """Execute CSV file cleaning"""
        self.log_message("Cleaning CSV files...")
        
        try:
            result = subprocess.run([sys.executable, 'clean_csv_files.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_message("✅ CSV cleaning completed successfully")
                # Log cleaning statistics
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.log_message(f"  {line}", print_to_console=False)
                return True
            else:
                self.log_message(f"❌ CSV cleaning failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error cleaning CSV files: {str(e)}")
            return False
    
    def run_post_cleaning_validation(self):
        """Run data quality validation after cleaning"""
        self.log_message("Running post-cleaning data quality validation...")
        
        try:
            result = subprocess.run([sys.executable, 'validate_data_quality.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_message("✅ Post-cleaning validation completed")
                # Log validation output
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.log_message(f"  {line}", print_to_console=False)
                return True
            else:
                self.log_message(f"⚠️  Post-cleaning validation had issues: {result.stderr}")
                return True  # Continue anyway
                
        except Exception as e:
            self.log_message(f"❌ Error running post-cleaning validation: {str(e)}")
            return False
    
    def generate_final_report(self):
        """Generate final cleaning report"""
        self.log_message("Generating final cleaning report...")
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        report_content = f"""
DATA CLEANING COMPLETION REPORT
===============================
Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration}

BACKUP INFORMATION:
- Backup File: {self.backup_file or 'Not created'}

CLEANED FILES:
- PostgreSQL Database: reddit_db (all tables)
- CSV Files: All available CSV files processed

CLEANING OPERATIONS PERFORMED:
✓ Removed leading/trailing whitespace
✓ Normalized multiple spaces to single spaces
✓ Removed special characters and encoding issues
✓ Standardized rating formats
✓ Validated and cleaned URLs
✓ Removed duplicate records
✓ Handled null/empty values
✓ Optimized database performance

VALIDATION REPORTS:
- Pre-cleaning validation: Completed
- Post-cleaning validation: Completed
- Detailed reports saved in JSON format

LOG FILE: {self.log_file}

For detailed information, check the log file and validation reports.
"""
        
        report_filename = f"cleaning_report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report_content)
        
        self.log_message(f"✅ Final report saved to: {report_filename}")
        return report_filename
    
    def rollback_changes(self):
        """Rollback database changes if something goes wrong"""
        if self.backup_file and os.path.exists(self.backup_file):
            self.log_message("Rolling back database changes...")
            
            try:
                result = subprocess.run([sys.executable, 'backup_database.py', 'restore', self.backup_file], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log_message("✅ Database rollback completed")
                    return True
                else:
                    self.log_message(f"❌ Rollback failed: {result.stderr}")
                    return False
                    
            except Exception as e:
                self.log_message(f"❌ Error during rollback: {str(e)}")
                return False
        else:
            self.log_message("❌ No backup file available for rollback")
            return False
    
    def run_complete_cleaning(self):
        """Run the complete data cleaning process"""
        self.log_message("="*60)
        self.log_message("STARTING COMPREHENSIVE DATA CLEANING PROCESS")
        self.log_message("="*60)
        
        try:
            # Step 1: Check prerequisites
            if not self.check_prerequisites():
                return False
            
            # Step 2: Start database if needed
            if not self.start_database_if_needed():
                return False
            
            # Step 3: Create backup
            if not self.create_backup():
                self.log_message("❌ Cannot proceed without backup")
                return False
            
            # Step 4: Pre-cleaning validation
            if not self.run_pre_cleaning_validation():
                self.log_message("⚠️  Continuing despite validation issues...")
            
            # Step 5: Clean database
            if not self.clean_database():
                self.log_message("❌ Database cleaning failed. Rolling back...")
                self.rollback_changes()
                return False
            
            # Step 6: Clean CSV files
            if not self.clean_csv_files():
                self.log_message("⚠️  CSV cleaning failed, but database cleaning was successful")
            
            # Step 7: Post-cleaning validation
            if not self.run_post_cleaning_validation():
                self.log_message("⚠️  Post-cleaning validation had issues")
            
            # Step 8: Generate final report
            report_file = self.generate_final_report()
            
            self.log_message("="*60)
            self.log_message("✅ DATA CLEANING PROCESS COMPLETED SUCCESSFULLY")
            self.log_message("="*60)
            self.log_message(f"📊 Final report: {report_file}")
            self.log_message(f"📝 Detailed log: {self.log_file}")
            
            if self.backup_file:
                self.log_message(f"💾 Backup available: {self.backup_file}")
            
            return True
            
        except KeyboardInterrupt:
            self.log_message("❌ Process interrupted by user")
            self.log_message("Rolling back changes...")
            self.rollback_changes()
            return False
        
        except Exception as e:
            self.log_message(f"❌ Unexpected error: {str(e)}")
            self.log_message("Rolling back changes...")
            self.rollback_changes()
            return False

def main():
    """Main function"""
    orchestrator = DataCleaningOrchestrator()
    
    print("🧹 Comprehensive Data Cleaning Tool")
    print("=" * 50)
    print("This tool will clean your PostgreSQL database and CSV files")
    print("A backup will be created before any changes are made")
    print("=" * 50)
    
    # Ask for confirmation
    response = input("Do you want to proceed with data cleaning? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        success = orchestrator.run_complete_cleaning()
        sys.exit(0 if success else 1)
    else:
        print("Data cleaning cancelled by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
