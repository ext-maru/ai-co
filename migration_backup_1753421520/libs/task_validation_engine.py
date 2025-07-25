"""
🏛️ Elder Task Validation Engine
Validates tasks through Elder hierarchy before assignment to servants
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of task validation through Elder hierarchy"""

    is_valid: bool
    approval_token: Optional[str] = None
    reason: Optional[str] = None
    consulted_elders: List[str] = None
    validation_timestamp: Optional[datetime] = None
    priority_adjustment: Optional[str] = None


class TaskValidationEngine:
    """🏛️ Elder Hierarchy Task Validation System"""

    def __init__(self):
        """初期化メソッド"""
        self.validation_log_path = Path(
            "/home/aicompany/ai_co/logs/task_validation.log"
        )
        self.validation_log_path.parent.mkdir(exist_ok=True)

        # Elder consultation rules
        self.elder_specialties = {
            "knowledge_sage": ["learning", "documentation", "research", "analysis"],
            "incident_sage": ["security", "crisis", "emergency", "monitoring"],
            "task_sage": ["planning", "coordination", "optimization", "workflow"],
            "rag_sage": ["search", "information", "retrieval", "discovery"],
        }

        # Servant type validation rules
        self.servant_capabilities = {
            "knight": {
                "allowed_tasks": [
                    "testing",
                    "quality_assurance",
                    "security",
                    "guard_duty",
                    "coverage",
                ],
                "restricted_tasks": [
                    "system_shutdown",
                    "data_deletion",
                    "configuration_change",
                ],
                "elder_requirements": [
                    "task_sage"
                ],  # Minimum elder consultation required
            },
            "dwarf": {
                "allowed_tasks": [
                    "building",
                    "optimization",
                    "infrastructure",
                    "deployment",
                    "mining",
                ],
                "restricted_tasks": ["security_bypass", "unauthorized_access"],
                "elder_requirements": ["task_sage", "incident_sage"],
            },
            "wizard": {
                "allowed_tasks": [
                    "analysis",
                    "automation",
                    "monitoring",
                    "debugging",
                    "spellcasting",
                ],
                "restricted_tasks": ["destructive_magic", "unauthorized_automation"],
                "elder_requirements": ["knowledge_sage", "task_sage"],
            },
            "elf": {
                "allowed_tasks": [
                    "monitoring",
                    "logging",
                    "alerting",
                    "surveillance",
                    "watching",
                ],
                "restricted_tasks": ["privacy_violation", "unauthorized_surveillance"],
                "elder_requirements": ["incident_sage"],
            },
        }

        # High-risk keywords requiring additional validation
        self.high_risk_keywords = [
            "delete",
            "remove",
            "destroy",
            "shutdown",
            "disable",
            "bypass",
            "override",
            "escalate",
            "privilege",
            "admin",
            "root",
            "sudo",
            "configuration",
            "settings",
            "credentials",
            "password",
            "secret",
        ]

    async def validate_task(
        self,
        servant_type: str,
        servant_id: str,
        task_description: str,
        priority: str = "medium",
    ) -> ValidationResult:
        """Validate task through Elder hierarchy consultation"""

        try:
            # Step 1: Basic validation
            basic_validation = await self._basic_validation(
                servant_type, servant_id, task_description
            )
            if not basic_validation.is_valid:
                return basic_validation

            # Step 2: Risk assessment
            risk_level = await self._assess_risk_level(task_description)

            # Step 3: Elder consultation
            consultation_result = await self._consult_elders(
                servant_type, task_description, risk_level, priority
            )

            if not consultation_result.is_valid:
                return consultation_result

            # Step 4: Generate approval token
            approval_token = await self._generate_approval_token(
                servant_type,
                servant_id,
                task_description,
                consultation_result.consulted_elders,
            )

            # Step 5: Log validation
            await self._log_validation(
                servant_type,
                servant_id,
                task_description,
                "APPROVED",
                consultation_result.consulted_elders,
                approval_token,
            )

            return ValidationResult(
                is_valid=True,
                approval_token=approval_token,
                reason="Task approved through Elder hierarchy",
                consulted_elders=consultation_result.consulted_elders,
                validation_timestamp=datetime.now(),
                priority_adjustment=consultation_result.priority_adjustment,
            )

        except Exception as e:
            logger.error(f"Error validating task: {e}")
            return ValidationResult(
                is_valid=False, reason=f"Validation error: {str(e)}"
            )

    async def _basic_validation(
        self, servant_type: str, servant_id: str, task_description: str
    ) -> ValidationResult:
        """Perform basic task validation"""

        # Validate servant type
        if servant_type not in self.servant_capabilities:
            return ValidationResult(
                is_valid=False, reason=f"Unknown servant type: {servant_type}"
            )

        # Validate task description
        if not task_description or len(task_description.strip()) < 10:
            return ValidationResult(
                is_valid=False, reason="Task description too short or empty"
            )

        # Check for restricted tasks
        capabilities = self.servant_capabilities[servant_type]
        task_lower = task_description.lower()

        for restricted_task in capabilities["restricted_tasks"]:
            if restricted_task in task_lower:
                return ValidationResult(
                    is_valid=False,
                    reason=f"Task contains restricted operation: {restricted_task}",
                )

        # Check if task aligns with servant capabilities
        task_keywords = task_lower.split()
        allowed_tasks = capabilities["allowed_tasks"]

        # Look for at least one matching capability
        has_matching_capability = any(
            any(keyword in task_keyword for task_keyword in task_keywords)
            for keyword in allowed_tasks
        )

        if not has_matching_capability:
            logger.warning(
                f"Task may not align with {servant_type} capabilities: {task_description[:50]}..."
            )

        return ValidationResult(is_valid=True, reason="Basic validation passed")

    async def _assess_risk_level(self, task_description: str) -> str:
        """Assess risk level of task"""

        task_lower = task_description.lower()

        # Check for high-risk keywords
        high_risk_count = sum(
            1 for keyword in self.high_risk_keywords if keyword in task_lower
        )

        if high_risk_count >= 2:
            return "high"
        elif high_risk_count == 1:
            return "medium"
        else:
            return "low"

    async def _consult_elders(
        self, servant_type: str, task_description: str, risk_level: str, priority: str
    ) -> ValidationResult:
        """Consult appropriate Elders based on task and servant type"""

        consulted_elders = []

        # Always consult required elders for servant type
        required_elders = self.servant_capabilities[servant_type]["elder_requirements"]
        consulted_elders.extend(required_elders)

        # Consult additional elders based on task content
        task_lower = task_description.lower()

        for elder, specialties in self.elder_specialties.items():
        # 繰り返し処理
            if elder not in consulted_elders:
                for specialty in specialties:
                    if specialty in task_lower:
                        consulted_elders.append(elder)
                        break

        # High-risk tasks require additional elder consultation
        if risk_level == "high":
            if "incident_sage" not in consulted_elders:
                consulted_elders.append("incident_sage")
            if "knowledge_sage" not in consulted_elders:
                consulted_elders.append("knowledge_sage")

        # Simulate elder consultation (in real system, this would query elder systems)
        consultation_results = await self._simulate_elder_consultation(
            consulted_elders, servant_type, task_description, risk_level, priority
        )

        # Check if all elders approve
        if all(result["approved"] for result in consultation_results):
            # Check for priority adjustments
            priority_adjustments = [
                result["priority_adjustment"]
                for result in consultation_results
                if result.get("priority_adjustment")
            ]

            final_priority = priority_adjustments[0] if priority_adjustments else None

            return ValidationResult(
                is_valid=True,
                reason="All consulted elders approved",
                consulted_elders=consulted_elders,
                priority_adjustment=final_priority,
            )
        else:
            # Find disapproval reasons
            disapprovals = [
                f"{result['elder']}: {result['reason']}"
                for result in consultation_results
                if not result["approved"]
            ]

            return ValidationResult(
                is_valid=False,
                reason=f"Elder disapproval: {'; '.join(disapprovals)}",
                consulted_elders=consulted_elders,
            )

    async def _simulate_elder_consultation(
        self,
        elders: List[str],
        servant_type: str,
        task_description: str,
        risk_level: str,
        priority: str,
    ) -> List[Dict[str, Any]]:
        """Simulate consultation with Elders (placeholder for real Elder system integration)"""

        results = []

        for elder in elders:
            # Simulate elder decision-making logic
            approval = await self._elder_decision_logic(
                elder, servant_type, task_description, risk_level, priority
            )
            results.append(approval)

        return results

    async def _elder_decision_logic(
        self,
        elder: str,
        servant_type: str,
        task_description: str,
        risk_level: str,
        priority: str,
    ) -> Dict[str, Any]:
        """Simulate individual elder decision logic"""

        task_lower = task_description.lower()

        # Knowledge Sage consultation
        if elder == "knowledge_sage":
            # Approves learning, documentation, and analysis tasks
            knowledge_keywords = [
                "learn",
                "document",
                "analyze",
                "research",
                "study",
                "understand",
            ]
            if any(keyword in task_lower for keyword in knowledge_keywords):
                return {
                    "elder": elder,
                    "approved": True,
                    "reason": "Task aligns with knowledge advancement goals",
                    "confidence": 0.9,
                }
            elif risk_level == "high":
                return {
                    "elder": elder,
                    "approved": False,
                    "reason": "High-risk task requires more specific knowledge justification",
                }
            else:
                return {
                    "elder": elder,
                    "approved": True,
                    "reason": "No knowledge concerns identified",
                    "confidence": 0.7,
                }

        # Incident Sage consultation
        elif elder == "incident_sage":
            # Strict about security and system stability
            security_keywords = [
                "security",
                "monitor",
                "protect",
                "guard",
                "watch",
                "alert",
            ]
            destructive_keywords = ["delete", "remove", "destroy", "shutdown"]

            if any(keyword in task_lower for keyword in destructive_keywords):
                return {
                    "elder": elder,
                    "approved": False,
                    "reason": "Task contains potentially destructive operations",
                }
            elif any(keyword in task_lower for keyword in security_keywords):
                return {
                    "elder": elder,
                    "approved": True,
                    "reason": "Task supports system security and stability",
                    "confidence": 0.95,
                }
            else:
                return {
                    "elder": elder,
                    "approved": True,
                    "reason": "No security concerns identified",
                    "confidence": 0.8,
                }

        # Task Sage consultation
        elif elder == "task_sage":
            # Focuses on efficiency and coordination
            efficiency_keywords = [
                "optimize",
                "improve",
                "enhance",
                "coordinate",
                "automate",
            ]

            if any(keyword in task_lower for keyword in efficiency_keywords):
                # May suggest priority adjustment for optimization tasks
                return {
                    "elder": elder,
                    "approved": True,
                    "reason": "Task supports system efficiency",
                    "priority_adjustment": "high" if priority == "medium" else None,
                    "confidence": 0.9,
                }
            elif "test" in task_lower and servant_type == "knight":
                return {
                    "elder": elder,
                    "approved": True,
                    "reason": "Testing tasks are essential for quality",
                    "confidence": 0.95,
                }
            else:
                return {
                    "elder": elder,
                    "approved": True,
                    "reason": "Task coordination approved",
                    "confidence": 0.8,
                }

        # RAG Sage consultation
        elif elder == "rag_sage":
            # Supports information discovery and analysis
            search_keywords = [
                "search",
                "find",
                "discover",
                "retrieve",
                "analyze",
                "information",
            ]

            if not (any(keyword in task_lower for keyword in search_keywords)):
                continue  # Early return to reduce nesting
            # Reduced nesting - original condition satisfied
            if any(keyword in task_lower for keyword in search_keywords):
                return {
                    "elder": elder,
                    "approved": True,
                    "reason": "Task supports information discovery",
                    "confidence": 0.9,
                }
            else:
                return {
                    "elder": elder,
                    "approved": True,
                    "reason": "No information retrieval concerns",
                    "confidence": 0.75,
                }

        # Default approval for unknown elders
        return {
            "elder": elder,
            "approved": True,
            "reason": "Default approval",
            "confidence": 0.5,
        }

    async def _generate_approval_token(
        self,
        servant_type: str,
        servant_id: str,
        task_description: str,
        consulted_elders: List[str],
    ) -> str:
        """Generate unique approval token for validated task"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        token_uuid = uuid.uuid4().hex[:8]

        token_data = {
            "servant_type": servant_type,
            "servant_id": servant_id,
            "task_hash": hash(task_description) % 10000,  # Simple task hash
            "elders": sorted(consulted_elders),
            "timestamp": timestamp,
            "uuid": token_uuid,
        }

        # Create token string
        token = f"ELDER_APPROVAL_{timestamp}_{token_uuid}_{servant_type.upper()}"

        # Store token details for verification
        token_file = Path(f"/home/aicompany/ai_co/data/approval_tokens/{token}.json")
        token_file.parent.mkdir(parents=True, exist_ok=True)

        token_file.write_text(json.dumps(token_data, indent=2))

        return token

    async def verify_approval_token(self, token: str) -> Dict[str, Any]:
        """Verify approval token authenticity"""

        try:
            token_file = Path(
                f"/home/aicompany/ai_co/data/approval_tokens/{token}.json"
            )

            if not token_file.exists():
                return {"valid": False, "reason": "Token not found"}

            token_data = json.loads(token_file.read_text())

            # Check token age (valid for 24 hours)
            token_timestamp = datetime.strptime(
                token_data["timestamp"], "%Y%m%d_%H%M%S"
            )
            age_hours = (datetime.now() - token_timestamp).total_seconds() / 3600

            if age_hours > 24:
                return {"valid": False, "reason": "Token expired"}

            return {
                "valid": True,
                "token_data": token_data,
                "age_hours": round(age_hours, 2),
            }

        except Exception as e:
            return {"valid": False, "reason": f"Token verification error: {str(e)}"}

    async def _log_validation(
        self,
        servant_type: str,
        servant_id: str,
        task_description: str,
        result: str,
        consulted_elders: List[str],
        approval_token: Optional[str] = None,
    ):
        """Log task validation details"""

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "servant_type": servant_type,
            "servant_id": servant_id,
            "task_description": (
                task_description[:100] + "..."
                if len(task_description) > 100
                else task_description
            ),
            "result": result,
            "consulted_elders": consulted_elders,
            "approval_token": approval_token,
        }

        with open(self.validation_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    async def get_validation_history(
        self, servant_id: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get validation history with optional filtering"""

        if not self.validation_log_path.exists():
            return []

        history = []

        try:
            with open(self.validation_log_path, "r") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line.strip())

                        # Apply servant filter if specified
                        if not (servant_id and entry.get("servant_id") != servant_id):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if servant_id and entry.get("servant_id") != servant_id:
                            continue

                        history.append(entry)

            # Return most recent entries first
            history.reverse()

            return history[:limit]

        except Exception as e:
            logger.error(f"Error reading validation history: {e}")
            return []

    async def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""

        stats = {
            "total_validations": 0,
            "approved": 0,
            "rejected": 0,
            "approval_rate": 0.0,
            "by_servant_type": {},
            "by_elder": {},
        }

        history = await self.get_validation_history(limit=1000)

        # 繰り返し処理
        for entry in history:
            stats["total_validations"] += 1

            if entry["result"] == "APPROVED":
                stats["approved"] += 1
            else:
                stats["rejected"] += 1

            # Count by servant type
            servant_type = entry["servant_type"]
            if servant_type not in stats["by_servant_type"]:
                stats["by_servant_type"][servant_type] = {"total": 0, "approved": 0}

            stats["by_servant_type"][servant_type]["total"] += 1
            if entry["result"] == "APPROVED":
                stats["by_servant_type"][servant_type]["approved"] += 1

            # Count by elder
            for elder in entry.get("consulted_elders", []):
                if elder not in stats["by_elder"]:
                    stats["by_elder"][elder] = 0
                stats["by_elder"][elder] += 1

        # Calculate approval rate
        if stats["total_validations"] > 0:
            stats["approval_rate"] = round(
                (stats["approved"] / stats["total_validations"]) * 100, 1
            )

        return stats
