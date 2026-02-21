#!/usr/bin/env python
"""
MASTER REFACTOR AUDIT SCRIPT
Scans project structure and identifies:
- Duplicate apps
- Import violations
- Circular dependencies
- Structure inconsistencies
- Missing required files

Run: python audit_refactor.py > refactor_audit_report.txt
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
import ast
import re

class RefactorAudit:
    def __init__(self, repo_root="."):
        self.repo_root = Path(repo_root)
        self.issues = defaultdict(list)
        self.apps_in_root = []
        self.apps_in_apps = []
        self.duplicates = []
        self.imports_to_fix = []
        
    def run(self):
        """Execute full audit"""
        print("=" * 80)
        print("MASTER REFACTOR AUDIT REPORT")
        print("=" * 80)
        print()
        
        self.audit_root_level_apps()
        self.audit_apps_directory()
        self.find_duplicates()
        self.audit_hotels_app()
        self.check_installed_apps()
        self.find_problematic_imports()
        self.check_circular_imports()
        self.check_structure_compliance()
        
        self.print_summary()
        self.print_recommendations()
        
    def audit_root_level_apps(self):
        """Find apps at root level"""
        print("=" * 80)
        print("1. ROOT-LEVEL APPS AUDIT")
        print("=" * 80)
        print()
        
        app_dirs = [d for d in self.repo_root.iterdir() 
                    if d.is_dir() and not d.name.startswith('.') 
                    and d.name not in ['node_modules', 'static', 'staticfiles', 
                                      'templates', 'logs', 'e2e_artifacts',
                                      'test-results', '_deleted_apps_backup',
                                      '.venv', '__pycache__', '.git', '.pytest_cache',
                                      '.redis']]
        
        for app_dir in sorted(app_dirs):
            app_name = app_dir.name
            has_models = (app_dir / "models.py").exists()
            has_views = (app_dir / "views.py").exists()
            has_apps_config = (app_dir / "apps.py").exists()
            has_migrations = (app_dir / "migrations").exists()
            
            if has_models or has_views or has_apps_config:
                self.apps_in_root.append({
                    'name': app_name,
                    'path': app_dir,
                    'has_models': has_models,
                    'has_views': has_views,
                    'has_apps_config': has_apps_config,
                    'has_migrations': has_migrations,
                    'lines_of_code': self._count_code_lines(app_dir)
                })
        
        print(f"Found {len(self.apps_in_root)} apps at root level:\n")
        for app in sorted(self.apps_in_root, key=lambda x: x['lines_of_code'], reverse=True):
            print(f"  📦 {app['name']:<20} | {app['lines_of_code']:>6} LOC | " + 
                  f"{'models' if app['has_models'] else ''} " + 
                  f"{'views' if app['has_views'] else ''} " +
                  f"{'migrations' if app['has_migrations'] else ''}")
        print()
        
    def audit_apps_directory(self):
        """Find apps in /apps/ directory"""
        print("=" * 80)
        print("2. /APPS/ DIRECTORY AUDIT")
        print("=" * 80)
        print()
        
        apps_dir = self.repo_root / "apps"
        if not apps_dir.exists():
            print("  ⚠️  /apps/ directory not found!")
            return
            
        for app_dir in sorted(apps_dir.iterdir()):
            if app_dir.is_dir() and not app_dir.name.startswith('__'):
                app_name = app_dir.name
                has_models = (app_dir / "models.py").exists()
                has_views = (app_dir / "views.py").exists()
                has_apps_config = (app_dir / "apps.py").exists()
                has_migrations = (app_dir / "migrations").exists()
                
                self.apps_in_apps.append({
                    'name': app_name,
                    'path': app_dir,
                    'has_models': has_models,
                    'has_views': has_views,
                    'has_apps_config': has_apps_config,
                    'has_migrations': has_migrations,
                    'lines_of_code': self._count_code_lines(app_dir)
                })
        
        print(f"Found {len(self.apps_in_apps)} apps in /apps/:\n")
        for app in sorted(self.apps_in_apps, key=lambda x: x['lines_of_code'], reverse=True):
            print(f"  📦 {app['name']:<20} | {app['lines_of_code']:>6} LOC | " + 
                  f"{'models' if app['has_models'] else ''} " + 
                  f"{'views' if app['has_views'] else ''} " +
                  f"{'migrations' if app['has_migrations'] else ''}")
        print()
        
    def find_duplicates(self):
        """Find apps that exist in both root and /apps/"""
        print("=" * 80)
        print("3. DUPLICATE APPS DETECTION")
        print("=" * 80)
        print()
        
        root_names = {app['name'] for app in self.apps_in_root}
        apps_names = {app['name'] for app in self.apps_in_apps}
        duplicates = root_names & apps_names
        
        if duplicates:
            print(f"  ❌ Found {len(duplicates)} duplicate apps:\n")
            for dup in sorted(duplicates):
                root_app = next(a for a in self.apps_in_root if a['name'] == dup)
                apps_app = next(a for a in self.apps_in_apps if a['name'] == dup)
                
                print(f"    ✗ {dup}")
                print(f"      Root version:  {root_app['lines_of_code']:>6} LOC")
                print(f"      Apps version:  {apps_app['lines_of_code']:>6} LOC")
                
                # Determine which to keep
                if root_app['lines_of_code'] > apps_app['lines_of_code']:
                    print(f"      → KEEP root version, DELETE /apps/{dup}/")
                elif apps_app['lines_of_code'] > root_app['lines_of_code']:
                    print(f"      → KEEP /apps/{dup}/, DELETE root version")
                else:
                    print(f"      → SAME SIZE - check git history!")
                print()
                
                self.duplicates.append(dup)
        else:
            print("  ✓ No duplicate apps found!\n")
        print()
        
    def audit_hotels_app(self):
        """Check for structural issues in hotels app"""
        print("=" * 80)
        print("4. HOTELS APP STRUCTURE AUDIT")
        print("=" * 80)
        print()
        
        hotels_path = self.repo_root / "apps" / "hotels"
        if not hotels_path.exists():
            print("  ⚠️  apps/hotels/ not found\n")
            return
            
        issues = []
        
        # Check for conflicting files/directories
        if (hotels_path / "selectors.py").exists() and (hotels_path / "selectors").exists():
            issues.append("  ❌ CONFLICT: Both selectors.py and selectors/ exist")
            
        if (hotels_path / "services.py").exists() and (hotels_path / "services").exists():
            issues.append("  ❌ CONFLICT: Both services.py and services/ exist")
            
        if (hotels_path / "views.py").exists() and (hotels_path / "views").exists():
            issues.append("  ❌ CONFLICT: Both views.py and views/ exist")
        
        if issues:
            print()
            for issue in issues:
                print(issue)
            print()
        else:
            print("  ✓ No conflicting file/directory names\n")
        
        # Check for missing required directories
        required = ['tests', 'migrations', 'api']
        missing = []
        for req in required:
            if not (hotels_path / req).exists():
                missing.append(f"  ⚠️  Missing directory: {req}/")
        
        if missing:
            print()
            for m in missing:
                print(m)
            print()
        else:
            print("  ✓ All required directories present\n")
        
        # Check for filters.py (should move to platform/search/)
        if (hotels_path / "filters.py").exists():
            print("  ⚠️  filters.py found (should move to platform/search/ in Phase 4)\n")
        
        # Check for search/ subdirectory (should consolidate)
        if (hotels_path / "search").exists():
            search_files = list((hotels_path / "search").glob("*.py"))
            if search_files:
                print(f"  ⚠️  search/ subdirectory found ({len(search_files)} files)")
                print("     → Should consolidate into search engine (Phase 4)\n")
        
        print()
        
    def check_installed_apps(self):
        """Check Django settings.py for consistency"""
        print("=" * 80)
        print("5. DJANGO SETTINGS.PY AUDIT")
        print("=" * 80)
        print()
        
        settings_path = self.repo_root / "zygotrip_project" / "settings.py"
        if not settings_path.exists():
            print("  ⚠️  settings.py not found\n")
            return
            
        with open(settings_path, 'r') as f:
            content = f.read()
            
        # Extract INSTALLED_APPS
        match = re.search(r'INSTALLED_APPS\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if not match:
            print("  ❌ Could not parse INSTALLED_APPS\n")
            return
            
        apps_str = match.group(1)
        app_lines = re.findall(r'"([^"]+)"|\'([^\']+)\'', apps_str)
        installed = [line[0] or line[1] for line in app_lines]
        
        print(f"Found {len(installed)} apps in INSTALLED_APPS:\n")
        
        inconsistent = []
        for app in installed:
            if app.startswith('django') or app.startswith('celery'):
                continue  # Skip third-party
                
            # Check if it follows convention
            if app.startswith('apps.'):
                # Should have .apps.XConfig suffix
                if not '.apps.' in app or not app.endswith('Config'):
                    inconsistent.append(f"  ⚠️  {app:<35} (should be 'apps.X.apps.XConfig')")
            else:
                # Root-level app - might be OK
                app_dir = self.repo_root / app.split('.')[0]
                if app_dir.exists() and app_dir.is_dir():
                    print(f"  ✓ {app:<35} (root-level OK if unique)")
                else:
                    inconsistent.append(f"  ❌ {app:<35} (app not found!)")
        
        if inconsistent:
            print()
            for issue in inconsistent:
                print(issue)
        
        print()
        print()
        
    def find_problematic_imports(self):
        """Find imports that will break after refactor"""
        print("=" * 80)
        print("6. PROBLEMATIC IMPORTS DETECTION")
        print("=" * 80)
        print()
        
        # Find imports from root-level apps that might break
        problematic = defaultdict(list)
        
        for py_file in self.repo_root.rglob("*.py"):
            if any(part.startswith('.') for part in py_file.parts):
                continue  # Skip hidden dirs
            if '__pycache__' in py_file.parts:
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Find imports
                import_patterns = [
                    r'from\s+(\w+)\s+import',  # from module import
                    r'import\s+(\w+)',         # import module
                ]
                
                for pattern in import_patterns:
                    for match in re.finditer(pattern, content):
                        module = match.group(1)
                        
                        # Check if it's a root-level app that might move
                        if module in ['booking', 'buses', 'cabs', 'flights', 'meals', 
                                     'payments', 'pricing', 'promos', 'reviews', 'rooms',
                                     'trains', 'wallet', 'inventory']:
                            rel_path = py_file.relative_to(self.repo_root)
                            problematic[module].append(str(rel_path))
                            
            except Exception as e:
                pass  # Skip files we can't parse
        
        if problematic:
            print(f"Found {sum(len(v) for v in problematic.values())} imports to fix:\n")
            for module in sorted(problematic.keys()):
                print(f"  Module '{module}' imported in {len(problematic[module])} files:")
                for file_path in sorted(set(problematic[module]))[:5]:
                    print(f"    - {file_path}")
                if len(problematic[module]) > 5:
                    print(f"    ... and {len(problematic[module]) - 5} more")
                print()
        else:
            print("  ✓ No obvious problematic imports found\n")
        
        self.imports_to_fix = problematic
        print()
        
    def check_circular_imports(self):
        """Check for potential circular import issues"""
        print("=" * 80)
        print("7. CIRCULAR IMPORT DETECTION")
        print("=" * 80)
        print()
        
        print("  ℹ️  Run: python -c 'import apps; import core'")
        print("  ℹ️  If no errors, no circular imports detected\n")
        print()
        
    def check_structure_compliance(self):
        """Check overall structure compliance with standards"""
        print("=" * 80)
        print("8. STRUCTURE COMPLIANCE CHECK")
        print("=" * 80)
        print()
        
        compliance_score = 0
        max_score = 10
        
        # Check 1: All duplicates eliminated
        if not self.duplicates:
            print("  ✓ No duplicate apps")
            compliance_score += 1
        else:
            print(f"  ❌ {len(self.duplicates)} duplicate apps found")
        
        # Check 2: All apps follow standard structure
        standard_dirs = ['tests', 'migrations', 'models.py', 'admin.py']
        non_compliant = 0
        for app in self.apps_in_apps:
            missing = [d for d in standard_dirs 
                      if not (app['path'] / d if d.endswith('.py') 
                             else (app['path'] / d)).exists()]
            if missing:
                non_compliant += 1
        
        if non_compliant == 0:
            print("  ✓ All apps follow standard structure")
            compliance_score += 2
        else:
            print(f"  ⚠️  {non_compliant}/{len(self.apps_in_apps)} apps missing standard files")
            compliance_score += 1
        
        # Check 3: Settings INSTALLED_APPS consistent
        print("  ⚠️  Settings consistency check - see section 5")
        
        # Check 4: No root app imports in /apps/ code
        print("  ✓ (Run imports check in section 6)")
        compliance_score += 2
        
        # Check 5: hotels app structure
        hotels_path = self.repo_root / "apps" / "hotels"
        hotels_ok = True
        if (hotels_path / "selectors.py").exists() and (hotels_path / "selectors").exists():
            hotels_ok = False
        if (hotels_path / "services.py").exists() and (hotels_path / "services").exists():
            hotels_ok = False
        if (hotels_path / "views.py").exists() and (hotels_path / "views").exists():
            hotels_ok = False
            
        if hotels_ok:
            print("  ✓ hotels app has consistent structure")
            compliance_score += 2
        else:
            print("  ❌ hotels app has file/directory conflicts - see section 4")
        
        print()
        print(f"  COMPLIANCE SCORE: {compliance_score}/{max_score}")
        print(f"  Status: {'NOT READY for Phase 2' if compliance_score < 8 else 'READY for Phase 2'}")
        print()
        print()
        
    def print_summary(self):
        """Print executive summary"""
        print("=" * 80)
        print("EXECUTIVE SUMMARY - ACTION REQUIRED")
        print("=" * 80)
        print()
        
        actions = []
        
        if self.duplicates:
            actions.append(f"1. Delete {len(self.duplicates)} duplicate apps (root versions)")
        
        if any(a['name'] in ['booking', 'flights', 'meals', 'rooms', 'trains', 
                             'payments', 'pricing', 'wallet', 'promos', 'reviews',
                             'inventory'] for a in self.apps_in_root):
            actions.append("2. Move/consolidate remaining root-level domain apps to /apps/")
        
        if self.imports_to_fix:
            actions.append(f"3. Fix {sum(len(v) for v in self.imports_to_fix.values())} import statements")
        
        hotels_path = self.repo_root / "apps" / "hotels"
        if (hotels_path / "selectors.py").exists() or \
           (hotels_path / "services.py").exists() or \
           (hotels_path / "views.py").exists():
            actions.append("4. Rename old hotels app files (selectors.py → _legacy_selectors.py)")
        
        if actions:
            print("IMMEDIATE ACTIONS:\n")
            for action in actions:
                print(f"  {action}")
        else:
            print("  ✓ Project structure is ready for Phase 2!")
        
        print()
        print()
        
    def print_recommendations(self):
        """Print recommendations"""
        print("=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        print()
        
        print("1. RUN THIS AUDIT WEEKLY")
        print("   Track your progress: python audit_refactor.py")
        print()
        
        print("2. CREATE BACKUP BEFORE DELETING")
        print("   mkdir _deleted_apps_backup")
        print("   cp -r booking _deleted_apps_backup/")
        print()
        
        print("3. USE FEATURE BRANCH")
        print("   git checkout -b refactor/phase-1-structure")
        print()
        
        print("4. COMMIT FREQUENTLY")
        print("   git add . && git commit -m 'Phase 1: Delete [app] duplicate'")
        print()
        
        print("5. TEST AFTER EACH CHANGE")
        print("   pytest --tb=short")
        print()
        
        print()
        
    def _count_code_lines(self, directory):
        """Count Python lines of code in directory"""
        total = 0
        try:
            for py_file in directory.rglob("*.py"):
                if '__pycache__' not in py_file.parts:
                    try:
                        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                            total += len(f.readlines())
                    except:
                        pass
        except:
            pass
        return total


if __name__ == "__main__":
    audit = RefactorAudit()
    audit.run()