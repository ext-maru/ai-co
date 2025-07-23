"""
Elder Tree Agent Entry Point
"""

import os
import sys
import importlib

def main():


"""エージェントのメインエントリポイント""" "elder_tree.agents.knowledge_sage",
        "task_sage": "elder_tree.agents.task_sage",
        "incident_sage": "elder_tree.agents.incident_sage",
        "rag_sage": "elder_tree.agents.rag_sage",
        "elder_flow": "elder_tree.workflows.simple_elder_flow",
        "code_crafter": "elder_tree.servants.simple_code_crafter",
        "quality_guardian": "elder_tree.servants.quality_guardian",
        "research_wizard": "elder_tree.servants.research_wizard",
        "crisis_responder": "elder_tree.servants.crisis_responder"
    }
    
    if agent_type not in agent_modules:
        print(f"Unknown agent type: {agent_type}")
        sys.exit(1)
    
    # 動的インポートと実行
    module_name = agent_modules[agent_type]
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, 'main'):
            module.main()
        else:
            print(f"Module {module_name} has no main() function")
            sys.exit(1)
    except ImportError as e:
        print(f"Failed to import {module_name}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to run {agent_type}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()