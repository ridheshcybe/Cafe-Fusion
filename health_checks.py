import os
import smtplib
from datetime import datetime
from flask import current_app
from sqlalchemy import text
from extensions import db


class HealthCheckResult:
    def __init__(self, service_name: str, status: bool, message: str, details: dict = None):
        self.service_name = service_name
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()


def check_database():
    """Check database connection and basic operations."""
    try:
        # Test basic connection
        result = db.session.execute(text("SELECT 1"))
        if result.fetchone()[0] != 1:
            return HealthCheckResult("database", False, "Database query failed")
        
        # Test table existence - using the correct table name 'user' instead of 'users'
        try:
            db.session.execute(text("SELECT COUNT(*) FROM user"))
            db.session.execute(text("SELECT COUNT(*) FROM menu_item"))
            db.session.execute(text("SELECT COUNT(*) FROM \"order\""))
            db.session.execute(text("SELECT COUNT(*) FROM order_item"))
            db.session.execute(text("SELECT COUNT(*) FROM inventory_item"))
            db.session.execute(text("SELECT COUNT(*) FROM coupon"))
        except Exception as e:
            return HealthCheckResult(
                "database", 
                False, 
                f"Database tables not properly initialized: {str(e)}"
            )
        
        return HealthCheckResult(
            "database", 
            True, 
            "Database connection successful",
            {"tables_exist": True}
        )
    except Exception as e:
        return HealthCheckResult(
            "database", 
            False, 
            f"Database connection failed: {str(e)}"
        )

def check_email_service():
    """Check email service configuration and connectivity."""
    try:
        mail_username = current_app.config.get('GMAIL_EMAIL')
        mail_password = current_app.config.get('GMAIL_APP_PASSWORD')

        # Check required configuration
        if not all([mail_username, mail_password]):
            return HealthCheckResult(
                "email", 
                False, 
                "Email service not fully configured",
                {
                    "username": bool(mail_username),
                    "password": bool(mail_password)
                }
            )
        
        # Test SMTP connection
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            
            server.login(mail_username, mail_password)
            server.quit()
            
            return HealthCheckResult(
                "email", 
                True, 
                "Email service connection successful",
                {
                    "server": "smtp.gmail.com",
                    "port": 587,
                }
            )
        except smtplib.SMTPAuthenticationError:
            return HealthCheckResult("email", False, "Email authentication failed")
        except smtplib.SMTPConnectError:
            return HealthCheckResult("email", False, "Cannot connect to email server")
        except Exception as e:
            return HealthCheckResult("email", False, f"Email service error: {str(e)}")
            
    except Exception as e:
        return HealthCheckResult("email", False, f"Email check failed: {str(e)}")


def check_file_system():
    """Check file system permissions and storage."""
    try:
        # Check write permissions in current directory
        test_file = "health_check_test.tmp"
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            write_permission = True
        except Exception:
            write_permission = False
        
        # Check instance directory
        instance_dir = current_app.instance_path
        instance_exists = os.path.exists(instance_dir)
        instance_writable = False
        if instance_exists:
            try:
                test_file = os.path.join(instance_dir, "health_check_test.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                instance_writable = True
            except Exception:
                pass
        
        return HealthCheckResult(
            "file_system", 
            write_permission and instance_writable, 
            "File system check completed",
            {
                "current_dir_writable": write_permission,
                "instance_dir_exists": instance_exists,
                "instance_dir_writable": instance_writable,
                "instance_path": instance_dir
            }
        )
    except Exception as e:
        return HealthCheckResult("file_system", False, f"File system check failed: {str(e)}")


def check_required_config():
    """Check required configuration values."""
    try:
        required_configs = ['SECRET_KEY', 'DATABASE_URL']
        
        missing_configs = []
        for config in required_configs:
            if not current_app.config.get(config):
                missing_configs.append(config)
        
        if missing_configs:
            return HealthCheckResult(
                "configuration", 
                False, 
                f"Missing required configuration: {', '.join(missing_configs)}",
                {"missing": missing_configs}
            )
        
        # Check for weak secret key
        secret_key = current_app.config.get('SECRET_KEY')
        if secret_key and len(secret_key) < 24:
            return HealthCheckResult(
                "configuration", 
                False, 
                "SECRET_KEY is too short (should be at least 24 characters)",
                {"secret_key_length": len(secret_key)}
            )
        
        return HealthCheckResult(
            "configuration", 
            True, 
            "All required configuration present",
            {"configs_checked": required_configs}
        )
    except Exception as e:
        return HealthCheckResult("configuration", False, f"Configuration check failed: {str(e)}")


def run_all_health_checks():
    """Run all health checks and return results."""
    checks = [
        check_database,
        check_email_service,
        check_file_system,
        check_required_config
    ]
    
    results = []
    for check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            results.append(HealthCheckResult(
                check_func.__name__,
                False,
                f"Health check failed to run: {str(e)}"
            ))
    
    return results


def get_overall_health():
    """Get overall health status."""
    results = run_all_health_checks()
    
    failed_checks = [r for r in results if not r.status]
    overall_status = len(failed_checks) == 0
    
    return {
        "status": "healthy" if overall_status else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": results,
        "failed_count": len(failed_checks),
        "total_count": len(results)
    }