#!/bin/bash
#!/bin/bash
echo "📚 Knowledge Base Updated to v5.1"
echo "=================================="
echo "Date: $(date)"
echo ""
echo "Updated files:"
ls -la /home/aicompany/ai_co/knowledge_base/*.md
echo ""
echo "Total KB files:"
find /home/aicompany/ai_co/knowledge_base -name "*.md" | wc -l
