#!/bin/bash
# AI Company プロンプトテンプレート機能の統合スクリプト

set -e

echo "🚀 AI Company Prompt Template System Integration"
echo "================================================"

# プロジェクトディレクトリ
PROJECT_DIR="/home/aicompany/ai_co"
cd "$PROJECT_DIR"

# 仮想環境アクティベート
source venv/bin/activate

echo ""
echo "📦 Installing dependencies..."
pip install jinja2 > /dev/null 2>&1

echo ""
echo "📂 Creating directories..."
mkdir -p config/prompts/{task,pm,dialog,result,slack}
mkdir -p db

echo ""
echo "🔧 Setting up prompt template manager..."

# プロンプトテンプレートマネージャーのテスト
echo "Testing PromptTemplateManager..."
python3 -c "
from libs.prompt_template_manager import PromptTemplateManager
manager = PromptTemplateManager()
if manager.initialize():
    print('✅ PromptTemplateManager initialized successfully')
else:
    print('❌ Failed to initialize PromptTemplateManager')
    exit(1)
"

echo ""
echo "📝 Creating sample templates..."

# TaskWorker用のカスタムテンプレート作成
cat > /tmp/task_advanced.j2 << 'EOF'
You are an advanced TaskWorker with specialized capabilities.

Task ID: {{ task_id }}
Task Type: {{ task_type }}
Priority: {{ priority | default('normal') }}

User Request:
{{ user_prompt }}

{% if rag_context %}
=== Similar Past Tasks ===
{{ rag_context }}
{% endif %}

{% if context_files %}
=== Context Files ===
{% for file in context_files %}
- {{ file }}
{% endfor %}
{% endif %}

Advanced Instructions:
1. Analyze the request thoroughly
2. Consider all edge cases
3. Implement comprehensive error handling
4. Write clean, maintainable code
5. Include unit tests where appropriate
6. Document your implementation
7. Use AI Company's Core modules

{% if performance_hints %}
Performance Optimization Hints:
{{ performance_hints }}
{% endif %}

You have full permissions to use all tools.
Implement the solution without asking for permissions.
EOF

# プロンプトテンプレートを登録
python3 << EOF
from libs.prompt_template_manager import PromptTemplateManager

manager = PromptTemplateManager()
manager.initialize()

# Advanced task template
with open('/tmp/task_advanced.j2', 'r') as f:
    content = f.read()

success = manager.create_template(
    worker_type='task',
    template_name='advanced',
    template_content=content,
    variables=['task_id', 'task_type', 'priority', 'user_prompt',
               'rag_context', 'context_files', 'performance_hints'],
    description='Advanced template with comprehensive instructions'
)

if success:
    print('✅ Created advanced task template')
else:
    print('⚠️  Advanced template already exists')

# PM Worker specialized template
pm_template = '''You are PMWorker specialized in project organization.

Task ID: {{ task_id }}
Git Branch: auto/{{ task_id }}

Files Created:
{% for file in files %}
- {{ file.path }} ({{ file.size }} bytes)
{% endfor %}

Project Rules:
{{ project_rules }}

Actions Required:
1. Analyze file types and content
2. Determine correct placement based on:
   - *_worker.py → workers/
   - *_manager.py → libs/
   - *.sh → scripts/
   - *.conf/json → config/
3. Move files to appropriate directories
4. Update import paths if needed
5. Commit with: 🤖 [Auto] Task {{ task_id }}: [summary]
6. Merge to develop branch

Ensure all paths are relative and follow AI Company standards.'''

manager.create_template(
    worker_type='pm',
    template_name='file_organization',
    template_content=pm_template,
    variables=['task_id', 'files', 'project_rules'],
    description='Specialized template for file organization'
)

print('✅ Created PM worker template')
EOF

echo ""
echo "🔧 Creating command shortcuts..."

# ai-promptコマンドに実行権限付与
chmod +x scripts/ai-prompt

# Binラッパー作成
cat > bin/ai-prompt << 'EOF'
#!/bin/bash
cd /home/aicompany/ai_co
source venv/bin/activate
exec python3 scripts/ai-prompt "$@"
EOF
chmod +x bin/ai-prompt

echo ""
echo "📊 Testing the system..."

# テンプレート一覧表示
echo "Available templates:"
ai-prompt list

echo ""
echo "🎯 Integration complete!"
echo ""
echo "Usage examples:"
echo "  ai-prompt list                              # List all templates"
echo "  ai-prompt show task default                 # Show template details"
echo "  ai-prompt generate task default --vars task_id=test_001 user_prompt='Test task'"
echo "  ai-prompt create worker template file.j2    # Create new template"
echo "  ai-prompt rollback task default 1          # Rollback to version 1"
echo ""
echo "To integrate with workers, add PromptTemplateMixin:"
echo "  from core.prompt_template_mixin import PromptTemplateMixin"
echo "  class MyWorker(BaseWorker, PromptTemplateMixin):"
echo "      ..."
