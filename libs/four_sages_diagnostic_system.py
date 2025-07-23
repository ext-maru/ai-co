"""
Four Sages Diagnostic System
Root cause analysis and automated repair for the 4 Sages system
"""
import asyncio
import json
import subprocess
import psutil
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import sqlite3
import psycopg2
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticResult:
    """Diagnostic test result"""
    component: str
    test_name: str
    status: str  # "healthy", "warning", "critical", "error"
    message: str
    details: Dict[str, Any]
    recommended_action: str
    auto_fixable: bool


class FourSagesDiagnosticSystem:
    """Comprehensive diagnostic system for 4 Sages"""
    
    def __init__(self):
        """初期化メソッド"""
        self.base_path = Path("/home/aicompany/ai_co")
        self.results: List[DiagnosticResult] = []
        self.auto_fixes_applied = []
        
    async def run_full_diagnosis(self) -> Dict[str, Any]:
        """Run comprehensive diagnosis of all 4 Sages components"""
        logger.info("🏥 Starting Full 4 Sages System Diagnosis...")
        
        self.results = []
        self.auto_fixes_applied = []
        
        # 1. Environment checks
        await self._check_environment()
        
        # 2. Database connectivity
        await self._check_databases()
        
        # 3. Knowledge base status
        await self._check_knowledge_base()
        
        # 4. Sage process health
        await self._check_sage_processes()
        
        # 5. File system integrity
        await self._check_file_system()
        
        # 6. Configuration validation
        await self._check_configuration()
        
        # Generate report
        return self._generate_diagnostic_report()
    
    async def _check_environment(self):
        """Check environment variables and system requirements"""
        logger.info("🌍 Checking environment...")
        
        # Check essential environment variables
        env_vars = [
            "HOME", "USER", "PATH"
        ]
        
        for var in env_vars:
            if os.getenv(var):
                self.results.append(DiagnosticResult(
                    component="environment",
                    test_name=f"env_var_{var}",
                    status="healthy",
                    message=f"Environment variable {var} is set",
                    details={"value": os.getenv(var)[:50] + "..." if len(os.getenv(var)) > 50 else os.getenv(var)},
                    recommended_action="None",
                    auto_fixable=False
                ))
            else:
                self.results.append(DiagnosticResult(
                    component="environment",
                    test_name=f"env_var_{var}",
                    status="warning",
                    message=f"Environment variable {var} is missing",
                    details={},
                    recommended_action=f"Set {var} environment variable",
                    auto_fixable=False
                ))
        
        # Check Python version
        import sys
        if sys.version_info >= (3, 8):
            self.results.append(DiagnosticResult(
                component="environment",
                test_name="python_version",
                status="healthy",
                message=f"Python version is compatible: {sys.version}",
                details={"version": sys.version},
                recommended_action="None",
                auto_fixable=False
            ))
        else:
            self.results.append(DiagnosticResult(
                component="environment",
                test_name="python_version",
                status="critical",
                message=f"Python version too old: {sys.version}",
                details={"version": sys.version},
                recommended_action="Upgrade to Python 3.8+",
                auto_fixable=False
            ))
    
    async def _check_databases(self):
        """Check database connectivity"""
        logger.info("💾 Checking database connections...")
        
        # Check SQLite databases
        sqlite_dbs = [
            self.base_path / "task_history.db",
            self.base_path / "data" / "rag_knowledge.db"
        ]
        
        for db_path in sqlite_dbs:
            if db_path.exists():
                try:
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    conn.close()
                    
                    self.results.append(DiagnosticResult(
                        component="database",
                        test_name=f"sqlite_{db_path.name}",
                        status="healthy",
                        message=f"SQLite database accessible: {db_path.name}",
                        details={"path": str(db_path), "size_mb": db_path.stat().st_size / 1024 / 1024},
                        recommended_action="None",
                        auto_fixable=False
                    ))
                    
                except Exception as e:
                    self.results.append(DiagnosticResult(
                        component="database",
                        test_name=f"sqlite_{db_path.name}",
                        status="error",
                        message=f"SQLite database error: {str(e)}",
                        details={"path": str(db_path), "error": str(e)},
                        recommended_action="Repair or recreate database",
                        auto_fixable=True
                    ))
            else:
                self.results.append(DiagnosticResult(
                    component="database",
                    test_name=f"sqlite_{db_path.name}",
                    status="warning",
                    message=f"SQLite database missing: {db_path.name}",
                    details={"expected_path": str(db_path)},
                    recommended_action="Create missing database",
                    auto_fixable=True
                ))
        
        # Check PostgreSQL if configured
        await self._check_postgresql()
    
    async def _check_postgresql(self):
        """Check PostgreSQL connectivity"""
        # Look for PostgreSQL configuration
        pg_configs = [
            ".env",
            "config/database.conf",
            "configs/postgresql.conf"
        ]
        
        pg_config_found = False
        for config_file in pg_configs:
            config_path = self.base_path / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                        if not ("postgresql" in content.lower() or "postgres" in content.lower()):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if "postgresql" in content.lower() or "postgres" in content.lower():
                            pg_config_found = True
                            break
                except:
                    pass
        
        if pg_config_found:
            # Try to connect
            try:
                # PostgreSQL connection attempt with environment variables
                import os
                conn = psycopg2.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    database=os.getenv("DB_NAME", "ai_co"),
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", "")  # 環境変数から取得
                )
                conn.close()
                
                self.results.append(DiagnosticResult(
                    component="database",
                    test_name="postgresql_connection",
                    status="healthy",
                    message="PostgreSQL connection successful",
                    details={"host": "localhost", "database": "ai_co"},
                    recommended_action="None",
                    auto_fixable=False
                ))
                
            except Exception as e:
                self.results.append(DiagnosticResult(
                    component="database",
                    test_name="postgresql_connection",
                    status="error",
                    message=f"PostgreSQL connection failed: {str(e)}",
                    details={"error": str(e)},
                    recommended_action="Fix PostgreSQL connection or configuration",
                    auto_fixable=True
                ))
        else:
            self.results.append(DiagnosticResult(
                component="database",
                test_name="postgresql_config",
                status="warning",
                message="PostgreSQL configuration not found",
                details={},
                recommended_action="Configure PostgreSQL if needed",
                auto_fixable=True
            ))
    
    async def _check_knowledge_base(self):
        """Check knowledge base integrity"""
        logger.info("📚 Checking knowledge base...")
        
        kb_path = self.base_path / "knowledge_base"
        
        if kb_path.exists():
            # Count files
            md_files = list(kb_path.glob("**/*.md"))
            json_files = list(kb_path.glob("**/*.json"))
            
            if len(md_files) > 0:
                self.results.append(DiagnosticResult(
                    component="knowledge_base",
                    test_name="markdown_files",
                    status="healthy",
                    message=f"Knowledge base contains {len(md_files)} markdown files",
                    details={"md_files": len(md_files), "json_files": len(json_files)},
                    recommended_action="None",
                    auto_fixable=False
                ))
            else:
                self.results.append(DiagnosticResult(
                    component="knowledge_base",
                    test_name="markdown_files",
                    status="warning",
                    message="Knowledge base contains no markdown files",
                    details={"md_files": 0, "json_files": len(json_files)},
                    recommended_action="Initialize knowledge base with content",
                    auto_fixable=True
                ))
        else:
            self.results.append(DiagnosticResult(
                component="knowledge_base",
                test_name="kb_directory",
                status="error",
                message="Knowledge base directory missing",
                details={"expected_path": str(kb_path)},
                recommended_action="Create knowledge base directory structure",
                auto_fixable=True
            ))
    
    async def _check_sage_processes(self):
        """Check if sage processes are running properly"""
        logger.info("🧙‍♂️ Checking sage processes...")
        
        # Check for sage-related Python processes
        sage_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if any(
                        keyword in cmdline.lower() for keyword in ['sage',
                        'elder',
                        'rag',
                        'knowledge',
                        'task',
                        'incident']
                    ):
                        sage_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline[:100]
                        })
            except:
                pass
        
        if sage_processes:
            self.results.append(DiagnosticResult(
                component="processes",
                test_name="sage_processes",
                status="healthy",
                message=f"Found {len(sage_processes)} sage-related processes",
                details={"processes": sage_processes},
                recommended_action="None",
                auto_fixable=False
            ))
        else:
            self.results.append(DiagnosticResult(
                component="processes",
                test_name="sage_processes",
                status="warning",
                message="No sage-related processes found running",
                details={},
                recommended_action="Start sage processes if needed",
                auto_fixable=True
            ))
    
    async def _check_file_system(self):
        """Check file system integrity"""
        logger.info("📁 Checking file system...")
        
        # Check essential directories
        essential_dirs = [
            "libs",
            "scripts", 
            "knowledge_base",
            "data"
        ]
        
        for dir_name in essential_dirs:
            dir_path = self.base_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                file_count = len(list(dir_path.glob("**/*")))
                self.results.append(DiagnosticResult(
                    component="filesystem",
                    test_name=f"directory_{dir_name}",
                    status="healthy",
                    message=f"Directory {dir_name} exists with {file_count} items",
                    details={"path": str(dir_path), "item_count": file_count},
                    recommended_action="None",
                    auto_fixable=False
                ))
            else:
                self.results.append(DiagnosticResult(
                    component="filesystem",
                    test_name=f"directory_{dir_name}",
                    status="warning",
                    message=f"Directory {dir_name} is missing",
                    details={"expected_path": str(dir_path)},
                    recommended_action=f"Create {dir_name} directory",
                    auto_fixable=True
                ))
        
        # Check disk space
        disk_usage = psutil.disk_usage(str(self.base_path))
        free_gb = disk_usage.free / 1024 / 1024 / 1024
        
        if free_gb > 1.0:
            self.results.append(DiagnosticResult(
                component="filesystem",
                test_name="disk_space",
                status="healthy",
                message=f"Sufficient disk space: {free_gb:.1f} GB free",
                details={"free_gb": free_gb, "total_gb": disk_usage.total / 1024 / 1024 / 1024},
                recommended_action="None",
                auto_fixable=False
            ))
        else:
            self.results.append(DiagnosticResult(
                component="filesystem",
                test_name="disk_space",
                status="warning",
                message=f"Low disk space: {free_gb:.1f} GB free",
                details={"free_gb": free_gb},
                recommended_action="Free up disk space",
                auto_fixable=False
            ))
    
    async def _check_configuration(self):
        """Check configuration files"""
        logger.info("⚙️ Checking configuration...")
        
        # Check for CLAUDE.md
        claude_md = self.base_path / "CLAUDE.md"
        if claude_md.exists():
            with open(claude_md, 'r') as f:
                content = f.read()
                if "4賢者" in content or "4 Sages" in content:
                    self.results.append(DiagnosticResult(
                        component="configuration",
                        test_name="claude_md_sages",
                        status="healthy",
                        message="CLAUDE.md contains 4 Sages configuration",
                        details={"file_size": len(content)},
                        recommended_action="None",
                        auto_fixable=False
                    ))
                else:
                    self.results.append(DiagnosticResult(
                        component="configuration",
                        test_name="claude_md_sages",
                        status="warning",
                        message="CLAUDE.md missing 4 Sages configuration",
                        details={},
                        recommended_action="Update CLAUDE.md with 4 Sages info",
                        auto_fixable=True
                    ))
        else:
            self.results.append(DiagnosticResult(
                component="configuration",
                test_name="claude_md",
                status="error",
                message="CLAUDE.md file missing",
                details={},
                recommended_action="Create CLAUDE.md configuration file",
                auto_fixable=True
            ))
    
    async def apply_auto_fixes(self) -> Dict[str, Any]:
        """Apply automatic fixes for detected issues"""
        logger.info("🔧 Applying automatic fixes...")
        
        fixes_applied = []
        fixes_failed = []
        
        for result in self.results:
            if result.auto_fixable and result.status in ["error", "warning"]:
                try:
                    fix_result = await self._apply_specific_fix(result)
                    if fix_result["success"]:
                        fixes_applied.append({
                            "component": result.component,
                            "test_name": result.test_name,
                            "action": fix_result["action"],
                            "details": fix_result.get("details", {})
                        })
                    else:
                        fixes_failed.append({
                            "component": result.component,
                            "test_name": result.test_name,
                            "error": fix_result.get("error", "Unknown error")
                        })
                except Exception as e:
                    fixes_failed.append({
                        "component": result.component,
                        "test_name": result.test_name,
                        "error": str(e)
                    })
        
        self.auto_fixes_applied = fixes_applied
        
        return {
            "fixes_applied": len(fixes_applied),
            "fixes_failed": len(fixes_failed),
            "applied": fixes_applied,
            "failed": fixes_failed
        }
    
    async def _apply_specific_fix(self, result: DiagnosticResult) -> Dict[str, Any]:
        """Apply specific fix based on diagnostic result"""
        if result.component == "database" and "missing" in result.message.lower():
            return await self._fix_missing_database(result)
        elif result.component == "knowledge_base" and "missing" in result.message.lower():
            return await self._fix_missing_knowledge_base(result)
        elif result.component == "filesystem" and "missing" in result.message.lower():
            return await self._fix_missing_directory(result)
        elif result.component == "database" and "postgresql" in result.test_name:
            return await self._fix_postgresql_connection(result)
        else:
            return {"success": False, "error": "No automatic fix available"}
    
    async def _fix_missing_database(self, result: DiagnosticResult) -> Dict[str, Any]:
        """Fix missing database"""
        try:
            if "task_history" in result.test_name:
                # Create task history database
                db_path = self.base_path / "task_history.db"
                conn = sqlite3.connect(str(db_path))
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY,
                        description TEXT,
                        status TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                conn.close()
                
                return {
                    "success": True,
                    "action": "Created task_history.db with basic schema",
                    "details": {"path": str(db_path)}
                }
            
            elif "rag_knowledge" in result.test_name:
                # Create RAG knowledge database
                db_path = self.base_path / "data" / "rag_knowledge.db"
                db_path.parent.mkdir(exist_ok=True)
                
                conn = sqlite3.connect(str(db_path))
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_entries (
                        id INTEGER PRIMARY KEY,
                        content TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                conn.close()
                
                return {
                    "success": True,
                    "action": "Created rag_knowledge.db with basic schema",
                    "details": {"path": str(db_path)}
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Unknown database type"}
    
    async def _fix_missing_knowledge_base(self, result: DiagnosticResult) -> Dict[str, Any]:
        """Fix missing knowledge base"""
        try:
            kb_path = self.base_path / "knowledge_base"
            kb_path.mkdir(exist_ok=True)
            
            # Create basic structure
            (kb_path / "core").mkdir(exist_ok=True)
            (kb_path / "guides").mkdir(exist_ok=True)
            (kb_path / "technical").mkdir(exist_ok=True)
            
            # Create a basic README
            readme_path = kb_path / "README.md"
            with open(readme_path, 'w') as f:
                f.write("""# Elders Guild Knowledge Base

This is the knowledge base for the 4 Sages system.

## Structure
- `core/` - Core knowledge and principles
- `guides/` - Implementation guides
- `technical/` - Technical documentation

## 4 Sages
- 📚 Knowledge Sage - Knowledge management
- 📋 Task Sage - Task planning
- 🚨 Incident Sage - Risk assessment  
- 🔍 RAG Sage - Information retrieval
""")
            
            return {
                "success": True,
                "action": "Created knowledge base directory structure",
                "details": {"path": str(kb_path), "files_created": 1}
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _fix_missing_directory(self, result: DiagnosticResult) -> Dict[str, Any]:
        """Fix missing directory"""
        try:
            dir_name = result.test_name.split("_")[-1]
            dir_path = self.base_path / dir_name
            dir_path.mkdir(exist_ok=True)
            
            return {
                "success": True,
                "action": f"Created directory {dir_name}",
                "details": {"path": str(dir_path)}
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _fix_postgresql_connection(self, result: DiagnosticResult) -> Dict[str, Any]:
        """Attempt to fix PostgreSQL connection issues"""
        try:
            # Create a basic PostgreSQL configuration guide
            config_path = self.base_path / "docs" / "postgresql_setup.md"
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w') as f:
                f.write("""# PostgreSQL Setup Guide

## Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

## Configuration
```bash
# Create database
sudo -u postgres createdb ai_co

# Create user (optional)
sudo -u postgres createuser --interactive
```

## Connection Test
```bash
psql -h localhost -d ai_co -U postgres
```
""")
            
            return {
                "success": True,
                "action": "Created PostgreSQL setup guide",
                "details": {"guide_path": str(config_path)}
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_diagnostic_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report"""
        # Categorize results
        healthy = [r for r in self.results if r.status == "healthy"]
        warnings = [r for r in self.results if r.status == "warning"]
        errors = [r for r in self.results if r.status == "error"]
        critical = [r for r in self.results if r.status == "critical"]
        
        # Overall health score
        total_tests = len(self.results)
        healthy_score = len(healthy) / total_tests * 100 if total_tests > 0 else 0
        
        # Determine overall status
        if critical:
            overall_status = "critical"
        elif errors:
            overall_status = "error"
        elif warnings:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "health_score": healthy_score,
            "summary": {
                "total_tests": total_tests,
                "healthy": len(healthy),
                "warnings": len(warnings), 
                "errors": len(errors),
                "critical": len(critical),
                "auto_fixable": len([r for r in self.results if r.auto_fixable])
            },
            "components": {
                "environment": [r.__dict__ for r in self.results if r.component == "environment"],
                "database": [r.__dict__ for r in self.results if r.component == "database"],
                "knowledge_base": [r.__dict__ for r in self.results if r.component == "knowledge_base"],
                "processes": [r.__dict__ for r in self.results if r.component == "processes"],
                "filesystem": [r.__dict__ for r in self.results if r.component == "filesystem"],
                "configuration": [r.__dict__ for r in self.results if r.component == "configuration"]
            },
            "auto_fixes_applied": self.auto_fixes_applied,
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on diagnostic results"""
        recommendations = []
        
        errors = [r for r in self.results if r.status in ["error", "critical"]]
        warnings = [r for r in self.results if r.status == "warning"]
        
        if errors:
            recommendations.append("🚨 Critical issues detected - immediate attention required")
            for error in errors[:3]:  # Top 3 errors
                recommendations.append(f"  - {error.recommended_action}")
        
        if warnings:
            recommendations.append("⚠️ Warnings detected - recommended improvements:")
            for warning in warnings[:3]:  # Top 3 warnings
                recommendations.append(f"  - {warning.recommended_action}")
        
        auto_fixable = [r for r in self.results if r.auto_fixable and r.status in ["error", "warning"]]
        if auto_fixable:
            recommendations.append(f"🔧 {len(auto_fixable)} issues can be automatically fixed")
            recommendations.append("  - Run diagnostic system with auto-fix enabled")
        
        return recommendations


async def run_four_sages_diagnosis():
    """4賢者システムの包括的診断を実行"""
    diagnostic = FourSagesDiagnosticSystem()
    
    print("🏥 4賢者システム診断を開始します...")
    
    # 診断実行
    report = await diagnostic.run_full_diagnosis()
    
    # レポート表示
    print(f"\n📊 診断レポート - {report['timestamp']}")
    print(f"全体ステータス: {report['overall_status'].upper()}")
    print(f"健全性スコア: {report['health_score']:.1f}/100")
    
    summary = report['summary']
    print(f"\n📋 サマリー:")
    print(f"  総テスト数: {summary['total_tests']}")
    print(f"  健全: {summary['healthy']} | 警告: {summary['warnings']} | エラー: \
        {summary['errors']} | 重大: {summary['critical']}")
    
    # 自動修復可能項目
    if summary['auto_fixable'] > 0:
        print(f"  自動修復可能: {summary['auto_fixable']}")
        
        user_input = input("\n🔧 自動修復を実行しますか? (y/n): ")
        if user_input.lower() == 'y':
            print("\n🔧 自動修復を実行中...")
            fix_results = await diagnostic.apply_auto_fixes()
            print(f"  修復完了: {fix_results['fixes_applied']}")
            print(f"  修復失敗: {fix_results['fixes_failed']}")
            
            # 再診断
            print("\n🔄 再診断を実行中...")
            report = await diagnostic.run_full_diagnosis()
            print(f"新しい健全性スコア: {report['health_score']:.1f}/100")
    
    # 推奨事項表示
    if report['recommendations']:
        print("\n💡 推奨事項:")
        for recommendation in report['recommendations']:
            print(f"  {recommendation}")
    
    # 詳細レポートをJSONで保存
    report_path = Path("/home/aicompany/ai_co/data/four_sages_diagnostic_report.json")
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 詳細レポートを保存しました: {report_path}")
    
    return report


if __name__ == "__main__":
    asyncio.run(run_four_sages_diagnosis())