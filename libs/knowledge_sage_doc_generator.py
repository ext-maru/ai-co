"""
Knowledge Sage Document Generator
Automatic documentation generation and content synthesis
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jinja2 import Environment, Template

from libs.knowledge_sage_standalone_ml import KnowledgeSageStandaloneML


class KnowledgeSageDocGenerator(KnowledgeSageStandaloneML):
    """Document generator for automatic documentation creation"""

    def __init__(self):
        """Initialize document generator"""
        super().__init__()
        self.logger = logging.getLogger("elders.KnowledgeDocGenerator")
        
        # Jinja2 environment for templates
        self.jinja_env = Environment()
        
        # Built-in templates
        self.templates = {}
        
        # Content generators
        self.generators = {}
        
        # Output formatters
        self.formatters = {}
        
        self._doc_initialized = False

    async def initialize(self) -> None:
        """Initialize document generator components"""
        await super().initialize()
        
        # Initialize templates
        self._initialize_templates()
        
        # Initialize generators
        self._initialize_generators()
        
        # Initialize formatters
        self._initialize_formatters()
        
        self._doc_initialized = True
        self.logger.info("Document Generator initialized")

    def is_initialized(self) -> bool:
        """Check if document generator is initialized"""
        return super().is_initialized() and self._doc_initialized

    def _initialize_templates(self) -> None:
        """Initialize built-in document templates"""
        self.templates.update({
            "api_documentation": """
# {{api_name}}

**Version:** {{version}}  
**Generated:** {{date}}

## Overview
{{overview}}

## Endpoints
{% for endpoint in endpoints %}
### {{endpoint.name}}
- **Method:** {{endpoint.method}}
- **URL:** `{{endpoint.url}}`
- **Description:** {{endpoint.description}}

{% if endpoint.parameters %}
**Parameters:**
{% for param in endpoint.parameters %}
- `{{param.name}}` ({{param.type}}): {{param.description}}
{% endfor %}
{% endif %}

{% if endpoint.example %}
**Example:**
```{{endpoint.example.language}}
{{endpoint.example.code}}
```
{% endif %}

{% endfor %}

## Error Codes
{% for error in error_codes %}
- **{{error.code}}**: {{error.description}}
{% endfor %}
            """,
            
            "user_guide": """
# {{title}}

**Generated:** {{date}}  
**Target Audience:** {{target_audience}}

## Table of Contents
{% for section in sections %}
- [{{section.title}}](#{{section.anchor}})
{% endfor %}

{% for section in sections %}
## {{section.title}}

{{section.content}}

{% if section.examples %}
### Examples
{% for example in section.examples %}
#### {{example.title}}
```{{example.language}}
{{example.code}}
```
{{example.description}}

{% endfor %}
{% endif %}

{% endfor %}

## Additional Resources
{% for resource in resources %}
- [{{resource.title}}]({{resource.url}})
{% endfor %}
            """,
            
            "technical_specification": """
# {{system_name}} - Technical Specification

**Version:** {{version}}  
**Date:** {{date}}

## Executive Summary
{{summary}}

## Architecture
{{architecture_description}}

{% if architecture_diagram %}
### Architecture Diagram
{{architecture_diagram}}
{% endif %}

## Technical Requirements

### System Requirements
{% for req in system_requirements %}
- {{req}}
{% endfor %}

### Dependencies
{% for dep in dependencies %}
- **{{dep.name}}** {{dep.version}}: {{dep.description}}
{% endfor %}

## API Specifications
{% if api_specs %}
{{api_specs}}
{% endif %}

## Security Considerations
{% for security_item in security_considerations %}
- {{security_item}}
{% endfor %}

## Performance Requirements
{% for perf_req in performance_requirements %}
- {{perf_req}}
{% endfor %}

## Deployment Guidelines
{{deployment_guidelines}}
            """,
            
            "faq": """
# Frequently Asked Questions

**Last Updated:** {{date}}

{% for category in faq_categories %}
## {{category.name}}

{% for qa in category.questions %}
### {{qa.question}}

{{qa.answer}}

{% if qa.examples %}
**Examples:**
{% for example in qa.examples %}
```{{example.language}}
{{example.code}}
```
{% endfor %}
{% endif %}

{% endfor %}
{% endfor %}
            """,
            
            "changelog": """
# Changelog

All notable changes to this project will be documented in this file.

{% for version in versions %}
## [{{version.number}}] - {{version.date}}

{% if version.changes.added %}
### Added
{% for item in version.changes.added %}
- {{item}}
{% endfor %}
{% endif %}

{% if version.changes.changed %}
### Changed
{% for item in version.changes.changed %}
- {{item}}
{% endfor %}
{% endif %}

{% if version.changes.fixed %}
### Fixed
{% for item in version.changes.fixed %}
- {{item}}
{% endfor %}
{% endif %}

{% if version.changes.removed %}
### Removed
{% for item in version.changes.removed %}
- {{item}}
{% endfor %}
{% endif %}

{% endfor %}
            """
        })

    def _initialize_generators(self) -> None:
        """Initialize content generators"""
        self.generators.update({
            "api_docs": self._generate_api_content,
            "user_guide": self._generate_guide_content,
            "tech_spec": self._generate_spec_content,
            "faq": self._generate_faq_content,
            "tutorial": self._generate_tutorial_content,
            "glossary": self._generate_glossary_content
        })

    def _initialize_formatters(self) -> None:
        """Initialize output formatters"""
        self.formatters.update({
            "markdown": self._format_markdown,
            "html": self._format_html,
            "rst": self._format_rst,
            "pdf": self._format_pdf
        })

    async def generate_api_documentation(
        self,
        knowledge_entries: List[Dict[str, Any]],
        api_name: str,
        version: str = "1.0",
        output_format: str = "markdown"
    ) -> Dict[str, Any]:
        """Generate API documentation"""
        try:
            # Extract API-related content
            api_content = await self._generate_api_content(knowledge_entries)
            
            # Prepare template context
            context = {
                "api_name": api_name,
                "version": version,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "overview": api_content.get("overview", "API Overview"),
                "endpoints": api_content.get("endpoints", []),
                "error_codes": api_content.get("error_codes", [])
            }
            
            # Render template
            template = self.jinja_env.from_string(self.templates["api_documentation"])
            documentation = template.render(**context)
            
            # Format output
            formatted_doc = await self._apply_formatter(documentation, output_format)
            
            return {
                "success": True,
                "documentation": formatted_doc,
                "metadata": {
                    "type": "api_documentation",
                    "format": output_format,
                    "generated_at": datetime.now().isoformat(),
                    "word_count": len(formatted_doc.split())
                }
            }
            
        except Exception as e:
            self.logger.error(f"API documentation generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_user_guide(
        self,
        knowledge_entries: List[Dict[str, Any]],
        title: str,
        target_audience: str = "users",
        include_examples: bool = True,
        output_format: str = "markdown",
        language: str = "en",
        localize_content: bool = False
    ) -> Dict[str, Any]:
        """Generate user guide documentation"""
        try:
            # Generate guide content
            guide_content = await self._generate_guide_content(
                knowledge_entries, 
                include_examples=include_examples
            )
            
            # Prepare template context
            context = {
                "title": title,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "target_audience": target_audience,
                "sections": guide_content.get("sections", []),
                "resources": guide_content.get("resources", [])
            }
            
            # Render template
            template = self.jinja_env.from_string(self.templates["user_guide"])
            documentation = template.render(**context)
            
            # Format output
            formatted_doc = await self._apply_formatter(documentation, output_format)
            
            return {
                "success": True,
                "documentation": formatted_doc,
                "metadata": {
                    "type": "user_guide",
                    "format": output_format,
                    "generated_at": datetime.now().isoformat(),
                    "sections_count": len(guide_content.get("sections", [])),
                    "word_count": len(formatted_doc.split())
                }
            }
            
        except Exception as e:
            self.logger.error(f"User guide generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_technical_specification(
        self,
        knowledge_entries: List[Dict[str, Any]],
        system_name: str,
        include_architecture: bool = True,
        include_api_specs: bool = True,
        output_format: str = "markdown"
    ) -> Dict[str, Any]:
        """Generate technical specification"""
        try:
            # Generate specification content
            spec_content = await self._generate_spec_content(
                knowledge_entries,
                include_architecture=include_architecture,
                include_api_specs=include_api_specs
            )
            
            # Prepare template context
            context = {
                "system_name": system_name,
                "version": "1.0",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "summary": spec_content.get("summary", "System overview"),
                "architecture_description": spec_content.get("architecture", ""),
                "system_requirements": spec_content.get("requirements", []),
                "dependencies": spec_content.get("dependencies", []),
                "api_specs": spec_content.get("api_specs", ""),
                "security_considerations": spec_content.get("security", []),
                "performance_requirements": spec_content.get("performance", []),
                "deployment_guidelines": spec_content.get("deployment", "")
            }
            
            # Render template
            template = self.jinja_env.from_string(self.templates["technical_specification"])
            documentation = template.render(**context)
            
            # Format output
            formatted_doc = await self._apply_formatter(documentation, output_format)
            
            return {
                "success": True,
                "documentation": formatted_doc,
                "metadata": {
                    "type": "technical_specification",
                    "format": output_format,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Technical specification generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def synthesize_knowledge(
        self,
        knowledge_entries: List[Dict[str, Any]],
        synthesis_type: str = "summary",
        max_length: int = 1000,
        include_citations: bool = True
    ) -> Dict[str, Any]:
        """Synthesize knowledge from multiple sources"""
        try:
            if not knowledge_entries:
                return {
                    "success": False,
                    "error": "No knowledge entries provided"
                }
            
            # Sort by quality score if available
            sorted_entries = sorted(
                knowledge_entries,
                key=lambda x: x.get("quality_score", 0.5),
                reverse=True
            )
            
            # Extract key information
            contents = [entry["content"] for entry in sorted_entries]
            
            if synthesis_type == "summary":
                synthesized = await self._create_summary(contents, max_length)
            elif synthesis_type == "comparison":
                synthesized = await self._create_comparison(contents, max_length)
            elif synthesis_type == "analysis":
                synthesized = await self._create_analysis(contents, max_length)
            else:
                synthesized = await self._create_overview(contents, max_length)
            
            # Generate citations
            citations = []
            if include_citations:
                for i, entry in enumerate(sorted_entries[:5]):  # Top 5 sources
                    citations.append({
                        "id": i + 1,
                        "title": entry.get("title", f"Source {i + 1}"),
                        "content_preview": entry["content"][:100] + "...",
                        "quality_score": entry.get("quality_score", 0.5)
                    })
            
            # Calculate confidence score
            avg_quality = sum(e.get("quality_score", 0.5) for e in sorted_entries) / len(sorted_entries)
            confidence_score = min(1.0, avg_quality * len(sorted_entries) / 10)
            
            return {
                "success": True,
                "synthesized_content": synthesized,
                "citations": citations,
                "confidence_score": confidence_score,
                "source_count": len(knowledge_entries),
                "synthesis_type": synthesis_type
            }
            
        except Exception as e:
            self.logger.error(f"Knowledge synthesis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_tutorial(
        self,
        knowledge_entries: List[Dict[str, Any]],
        tutorial_title: str,
        difficulty_level: str = "beginner",
        include_code_examples: bool = True
    ) -> Dict[str, Any]:
        """Generate step-by-step tutorial"""
        try:
            tutorial_content = await self._generate_tutorial_content(
                knowledge_entries,
                difficulty_level=difficulty_level,
                include_code_examples=include_code_examples
            )
            
            # Build tutorial structure
            tutorial_doc = f"# {tutorial_title}\n\n"
            tutorial_doc += f"**Difficulty Level:** {difficulty_level.title()}\n\n"
            
            if tutorial_content.get("prerequisites"):
                tutorial_doc += "## Prerequisites\n"
                for prereq in tutorial_content["prerequisites"]:
                    tutorial_doc += f"- {prereq}\n"
                tutorial_doc += "\n"
            
            if tutorial_content.get("steps"):
                tutorial_doc += "## Tutorial Steps\n\n"
                for i, step in enumerate(tutorial_content["steps"], 1):
                    tutorial_doc += f"### Step {i}: {step['title']}\n\n"
                    tutorial_doc += f"{step['description']}\n\n"
                    
                    if step.get("code_example"):
                        tutorial_doc += f"```{step['code_example'].get('language', 'text')}\n"
                        tutorial_doc += f"{step['code_example']['code']}\n"
                        tutorial_doc += "```\n\n"
            
            return {
                "success": True,
                "documentation": tutorial_doc,
                "metadata": {
                    "type": "tutorial",
                    "difficulty": difficulty_level,
                    "steps_count": len(tutorial_content.get("steps", [])),
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Tutorial generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_faq(
        self,
        knowledge_entries: List[Dict[str, Any]],
        category_filter: Optional[str] = None,
        max_questions: int = 20
    ) -> Dict[str, Any]:
        """Generate FAQ from knowledge base"""
        try:
            # Filter by category if specified
            if category_filter:
                filtered_entries = [
                    e for e in knowledge_entries 
                    if e.get("category") == category_filter
                ]
            else:
                filtered_entries = knowledge_entries
            
            # Generate FAQ content
            faq_content = await self._generate_faq_content(filtered_entries, max_questions)
            
            # Prepare template context
            context = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "faq_categories": faq_content.get("categories", [])
            }
            
            # Render template
            template = self.jinja_env.from_string(self.templates["faq"])
            documentation = template.render(**context)
            
            return {
                "success": True,
                "documentation": documentation,
                "metadata": {
                    "type": "faq",
                    "questions_count": sum(
                        len(cat.get("questions", [])) 
                        for cat in faq_content.get("categories", [])
                    ),
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"FAQ generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_glossary(
        self,
        knowledge_entries: List[Dict[str, Any]],
        extract_technical_terms: bool = True,
        alphabetical_order: bool = True
    ) -> Dict[str, Any]:
        """Generate glossary of terms"""
        try:
            glossary_content = await self._generate_glossary_content(
                knowledge_entries,
                extract_technical_terms=extract_technical_terms
            )
            
            terms = glossary_content.get("terms", [])
            
            if alphabetical_order:
                terms.sort(key=lambda x: x["term"].lower())
            
            # Build glossary document
            glossary_doc = "# Glossary\n\n"
            
            for term_entry in terms:
                glossary_doc += f"**{term_entry['term']}**\n"
                glossary_doc += f": {term_entry['definition']}\n\n"
            
            return {
                "success": True,
                "documentation": glossary_doc,
                "metadata": {
                    "type": "glossary",
                    "terms_count": len(terms),
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Glossary generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_changelog(
        self,
        version_history: List[Dict[str, Any]],
        format: str = "markdown"
    ) -> Dict[str, Any]:
        """Generate changelog from version history"""
        try:
            # Prepare changelog data
            versions = []
            for version in version_history:
                version_data = {
                    "number": version["version"],
                    "date": version["date"],
                    "changes": self._categorize_changes(version.get("changes", []))
                }
                versions.append(version_data)
            
            # Sort by version (newest first)
            versions.sort(key=lambda x: x["number"], reverse=True)
            
            # Render template
            template = self.jinja_env.from_string(self.templates["changelog"])
            documentation = template.render(versions=versions)
            
            return {
                "success": True,
                "documentation": documentation,
                "metadata": {
                    "type": "changelog",
                    "versions_count": len(versions),
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Changelog generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _categorize_changes(self, changes: List[str]) -> Dict[str, List[str]]:
        """Categorize changes into added, changed, fixed, removed"""
        categories = {
            "added": [],
            "changed": [], 
            "fixed": [],
            "removed": []
        }
        
        for change in changes:
            change_lower = change.lower()
            if any(word in change_lower for word in ["add", "new", "implement"]):
                categories["added"].append(change)
            elif any(word in change_lower for word in ["fix", "bug", "issue"]):
                categories["fixed"].append(change)
            elif any(word in change_lower for word in ["remove", "delete", "deprecat"]):
                categories["removed"].append(change)
            else:
                categories["changed"].append(change)
        
        return categories

    async def generate_from_template(
        self,
        template: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate documentation from custom template"""
        try:
            template_obj = self.jinja_env.from_string(template)
            documentation = template_obj.render(**context)
            
            return {
                "success": True,
                "documentation": documentation,
                "metadata": {
                    "type": "custom_template",
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Template generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_batch(
        self,
        generation_jobs: List[Dict[str, Any]],
        output_directory: str
    ) -> Dict[str, Any]:
        """Generate multiple documents in batch"""
        try:
            os.makedirs(output_directory, exist_ok=True)
            generated_files = []
            
            for job in generation_jobs:
                job_type = job.get("type")
                
                if job_type == "user_guide":
                    result = await self.generate_user_guide(**{
                        k: v for k, v in job.items() if k != "type"
                    })
                elif job_type == "api_docs":
                    result = await self.generate_api_documentation(**{
                        k: v for k, v in job.items() if k != "type"
                    })
                elif job_type == "faq":
                    result = await self.generate_faq(**{
                        k: v for k, v in job.items() if k != "type"
                    })
                else:
                    continue
                
                if result.get("success"):
                    # Save to file
                    filename = f"{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    filepath = os.path.join(output_directory, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(result["documentation"])
                    
                    generated_files.append(filepath)
            
            return {
                "success": True,
                "generated_files": generated_files,
                "output_directory": output_directory
            }
            
        except Exception as e:
            self.logger.error(f"Batch generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def validate_documentation(
        self,
        content: str,
        check_structure: bool = True,
        check_completeness: bool = True,
        check_readability: bool = True
    ) -> Dict[str, Any]:
        """Validate documentation quality"""
        try:
            issues = []
            validation_score = 1.0
            
            if check_structure:
                structure_issues = self._check_structure(content)
                issues.extend(structure_issues)
                if structure_issues:
                    validation_score -= 0.2
            
            if check_completeness:
                completeness_issues = self._check_completeness(content)
                issues.extend(completeness_issues)
                if completeness_issues:
                    validation_score -= 0.3
            
            if check_readability:
                readability_score = self._check_readability(content)
                if readability_score < 0.7:
                    issues.append("Content may be difficult to read")
                    validation_score -= 0.2
            
            validation_score = max(0.0, validation_score)
            
            return {
                "success": True,
                "validation_score": validation_score,
                "issues": issues,
                "recommendations": self._generate_improvement_recommendations(issues)
            }
            
        except Exception as e:
            self.logger.error(f"Documentation validation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _check_structure(self, content: str) -> List[str]:
        """Check document structure"""
        issues = []
        
        # Check for title
        if not re.search(r'^#\s+.+', content, re.MULTILINE):
            issues.append("Missing main title (H1)")
        
        # Check for sections
        if not re.search(r'^##\s+.+', content, re.MULTILINE):
            issues.append("No sections found (H2)")
        
        # Check for empty sections
        sections = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
        for section in sections:
            section_content = re.search(
                rf'^##\s+{re.escape(section)}$(.*?)(?=^##|\Z)',
                content,
                re.MULTILINE | re.DOTALL
            )
            if section_content and len(section_content.group(1).strip()) < 50:
                issues.append(f"Section '{section}' appears to be too short")
        
        return issues

    def _check_completeness(self, content: str) -> List[str]:
        """Check document completeness"""
        issues = []
        
        # Check minimum length
        if len(content.split()) < 100:
            issues.append("Document appears to be too short")
        
        # Check for introduction
        if not re.search(r'introduction|overview|summary', content, re.IGNORECASE):
            issues.append("Consider adding an introduction or overview")
        
        # Check for examples
        if not re.search(r'```|example', content, re.IGNORECASE):
            issues.append("Consider adding code examples or illustrations")
        
        return issues

    def _check_readability(self, content: str) -> float:
        """Simple readability check"""
        words = content.split()
        sentences = len(re.findall(r'[.!?]+', content))
        
        if sentences == 0:
            return 0.5
        
        avg_sentence_length = len(words) / sentences
        
        # Simple readability score (higher is better)
        if avg_sentence_length > 25:
            return 0.4  # Too long
        elif avg_sentence_length < 8:
            return 0.6  # Too short
        else:
            return 0.9  # Good

    def _generate_improvement_recommendations(self, issues: List[str]) -> List[str]:
        """Generate improvement recommendations based on issues"""
        recommendations = []
        
        for issue in issues:
            if "title" in issue.lower():
                recommendations.append("Add a clear main title using # syntax")
            elif "section" in issue.lower():
                recommendations.append("Add section headers using ## syntax")
            elif "short" in issue.lower():
                recommendations.append("Expand content with more detailed explanations")
            elif "example" in issue.lower():
                recommendations.append("Include code examples or practical illustrations")
        
        return list(set(recommendations))  # Remove duplicates

    # Content generation methods
    async def _generate_api_content(
        self,
        knowledge_entries: List[Dict[str,
        Any]]
    ) -> Dict[str, Any]:
        """Generate API-specific content"""
        api_entries = [e for e in knowledge_entries if "api" in e.get("tags", [])]
        
        endpoints = []
        error_codes = [
            {"code": "400", "description": "Bad Request"},
            {"code": "401", "description": "Unauthorized"},
            {"code": "404", "description": "Not Found"},
            {"code": "500", "description": "Internal Server Error"}
        ]
        
        for entry in api_entries[:10]:  # Limit to 10 endpoints
            endpoint = {
                "name": entry.get("title", "Endpoint"),
                "method": "GET",  # Default, could be extracted from content
                "url": "/api/endpoint",  # Default, could be extracted
                "description": entry.get("content", "")[:200] + "..."
            }
            endpoints.append(endpoint)
        
        return {
            "overview": "API for knowledge management and retrieval",
            "endpoints": endpoints,
            "error_codes": error_codes
        }

    async def _generate_guide_content(
        self, 
        knowledge_entries: List[Dict[str, Any]], 
        include_examples: bool = True
    ) -> Dict[str, Any]:
        """Generate user guide content"""
        # Group by category
        categories = {}
        for entry in knowledge_entries:
            category = entry.get("category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append(entry)
        
        sections = []
        for category, entries in categories.items():
            section = {
                "title": category.title(),
                "anchor": category.lower().replace(" ", "-"),
                "content": self._create_section_content(entries),
                "examples": []
            }
            
            if include_examples:
                section["examples"] = self._extract_examples(entries)
            
            sections.append(section)
        
        return {
            "sections": sections,
            "resources": [
                {"title": "API Documentation", "url": "/api/docs"},
                {"title": "Source Code", "url": "/source"}
            ]
        }

    def _create_section_content(self, entries: List[Dict[str, Any]]) -> str:
        """Create content for a guide section"""
        if not entries:
            return "No content available for this section."
        
        # Combine and summarize entries
        content = "This section covers:\n\n"
        for entry in entries[:5]:  # Limit to 5 entries
            content += f"- **{entry.get('title', 'Item')}**: "
            content += entry.get('content', '')[:150] + "...\n"
        
        return content

    def _extract_examples(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract code examples from entries"""
        examples = []
        for entry in entries:
            content = entry.get("content", "")
            # Look for code blocks
            code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL)
            for language, code in code_blocks[:2]:  # Max 2 examples per entry
                examples.append({
                    "title": f"Example from {entry.get('title', 'Entry')}",
                    "language": language or "text",
                    "code": code.strip(),
                    "description": "Code example"
                })
        
        return examples[:5]  # Max 5 examples total

    async def _generate_spec_content(
        self,
        knowledge_entries: List[Dict[str, Any]],
        include_architecture: bool = True,
        include_api_specs: bool = True
    ) -> Dict[str, Any]:
        """Generate technical specification content"""
        return {
            "summary": "System provides knowledge management and AI-powered features",
            "architecture": "Microservices architecture with PostgreSQL and ML components",
            "requirements": [
                "Python 3.8+",
                "PostgreSQL 12+",
                "Redis 6+",
                "Docker (optional)"
            ],
            "dependencies": [
                {"name": "FastAPI", "version": "0.68+", "description": "Web framework"},
                {"name": "asyncpg", "version": "0.24+", "description": "PostgreSQL driver"},
                {"name": "scikit-learn", "version": "1.0+", "description": "Machine learning"}
            ],
            "api_specs": "RESTful API with JSON responses",
            "security": [
                "OAuth 2.0 authentication",
                "HTTPS encryption",
                "Input validation",
                "Rate limiting"
            ],
            "performance": [
                "Sub-100ms API response time",
                "10,000+ documents supported",
                "Concurrent user handling"
            ],
            "deployment": "Docker containers with Kubernetes orchestration"
        }

    async def _generate_faq_content(
        self, 
        knowledge_entries: List[Dict[str, Any]], 
        max_questions: int = 20
    ) -> Dict[str, Any]:
        """Generate FAQ content"""
        # Generate questions based on content
        questions = []
        
        for entry in knowledge_entries[:max_questions]:
            question = f"How do I use {entry.get('title', 'this feature')}?"
            answer = entry.get('content', '')[:300] + "..."
            
            questions.append({
                "question": question,
                "answer": answer,
                "examples": []
            })
        
        return {
            "categories": [
                {
                    "name": "General",
                    "questions": questions
                }
            ]
        }

    async def _generate_tutorial_content(
        self,
        knowledge_entries: List[Dict[str, Any]],
        difficulty_level: str = "beginner",
        include_code_examples: bool = True
    ) -> Dict[str, Any]:
        """Generate tutorial content"""
        steps = []
        
        for i, entry in enumerate(knowledge_entries[:5], 1):
            step = {
                "title": f"Understanding {entry.get('title', f'Concept {i}')}",
                "description": entry.get('content', '')[:200] + "..."
            }
            
            if include_code_examples:
                step["code_example"] = {
                    "language": "python",
                    "code": "# Example code placeholder\nprint('Hello, World!')"
                }
            
            steps.append(step)
        
        return {
            "prerequisites": ["Basic programming knowledge", "Python installed"],
            "steps": steps
        }

    async def _generate_glossary_content(
        self,
        knowledge_entries: List[Dict[str, Any]],
        extract_technical_terms: bool = True
    ) -> Dict[str, Any]:
        """Generate glossary content"""
        terms = []
        
        # Extract technical terms (simplified)
        tech_terms = {
            "API": "Application Programming Interface - a set of protocols for building software",
            "ML": "Machine Learning - algorithms that learn from data",
            "Vector": "Mathematical representation of data in multi-dimensional space",
            "Embedding": "Dense vector representation of text or data",
            "PostgreSQL": "Open-source relational database system"
        }
        
        for term, definition in tech_terms.items():
            terms.append({
                "term": term,
                "definition": definition
            })
        
        return {"terms": terms}

    # Content synthesis methods
    async def _create_summary(self, contents: List[str], max_length: int) -> str:
        """Create summary of multiple contents"""
        combined = " ".join(contents)
        words = combined.split()
        
        if len(words) <= max_length:
            return combined
        
        # Simple extractive summarization
        sentences = re.split(r'[.!?]+', combined)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Take first few sentences that fit within limit
        summary_words = 0
        summary_sentences = []
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            if summary_words + sentence_words <= max_length:
                summary_sentences.append(sentence)
                summary_words += sentence_words
            else:
                break
        
        return ". ".join(summary_sentences) + "."

    async def _create_comparison(self, contents: List[str], max_length: int) -> str:
        """Create comparison of multiple contents"""
        return await self._create_summary(contents, max_length)

    async def _create_analysis(self, contents: List[str], max_length: int) -> str:
        """Create analysis of multiple contents"""
        return await self._create_summary(contents, max_length)

    async def _create_overview(self, contents: List[str], max_length: int) -> str:
        """Create overview of multiple contents"""
        return await self._create_summary(contents, max_length)

    # Formatting methods
    async def _apply_formatter(self, content: str, format_type: str) -> str:
        """Apply output formatting"""
        if format_type in self.formatters:
            return await self.formatters[format_type](content)
        return content

    async def _format_markdown(self, content: str) -> str:
        """Format as Markdown"""
        return content  # Already in Markdown

    async def _format_html(self, content: str) -> str:
        """Format as HTML"""
        # Simple Markdown to HTML conversion
        html = content
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        html = html.replace('\n\n', '</p><p>')
        html = f"<!DOCTYPE " \
            "html><html><head><title>Document</title></head><body><p>{html}</p></body></html>"
        return html

    async def _format_rst(self, content: str) -> str:
        """Format as reStructuredText"""
        # Simple Markdown to RST conversion
        rst = content
        rst = re.sub(r'^# (.+)$', r'\1\n' + '=' * 50, rst, flags=re.MULTILINE)
        rst = re.sub(r'^## (.+)$', r'\1\n' + '-' * 30, rst, flags=re.MULTILINE)
        rst = re.sub(r'^### (.+)$', r'\1\n' + '~' * 20, rst, flags=re.MULTILINE)
        rst = re.sub(r'\*\*(.+?)\*\*', r'**\1**', rst)
        rst = re.sub(r'`(.+?)`', r'``\1``', rst)
        return rst

    async def _format_pdf(self, content: str) -> str:
        """Format as PDF (placeholder)"""
        return f"PDF content (would require PDF library):\n\n{content}"

    # Additional helper methods
    async def analyze_content_gaps(
        self,
        knowledge_entries: List[Dict[str, Any]],
        required_topics: List[str],
        coverage_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Analyze content gaps"""
        try:
            # Simple topic coverage analysis
            covered_topics = set()
            all_content = " ".join([e.get("content", "") for e in knowledge_entries]).lower()
            
            for topic in required_topics:
                if topic.lower() in all_content:
                    covered_topics.add(topic)
            
            coverage_ratio = len(covered_topics) / len(required_topics)
            missing_topics = [t for t in required_topics if t not in covered_topics]
            
            return {
                "success": True,
                "coverage_analysis": {
                    "coverage_ratio": coverage_ratio,
                    "covered_topics": list(covered_topics),
                    "total_required": len(required_topics)
                },
                "missing_topics": missing_topics,
                "recommendations": [
                    f"Add content about {topic}" for topic in missing_topics
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def calculate_documentation_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate documentation metrics"""
        try:
            words = content.split()
            sentences = len(re.findall(r'[.!?]+', content))
            sections = len(re.findall(r'^#+\s', content, re.MULTILINE))
            
            metrics = {
                "word_count": len(words),
                "sentence_count": sentences,
                "section_count": sections,
                "readability_score": self._check_readability(content),
                "structure_score": 1.0 if sections > 0 else 0.5,
                "estimated_reading_time": max(1, len(words) // 200)  # 200 WPM
            }
            
            return {
                "success": True,
                "metrics": metrics
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_cross_references(
        self,
        knowledge_entries: List[Dict[str, Any]],
        reference_threshold: float = 0.3
    ) -> Dict[str, Any]:
        """Generate cross-references between documents"""
        try:
            references = []
            
            for i, entry1 in enumerate(knowledge_entries):
                for j, entry2 in enumerate(knowledge_entries[i+1:], i+1):
                    # Simple similarity based on shared tags
                    tags1 = set(entry1.get("tags", []))
                    tags2 = set(entry2.get("tags", []))
                    
                    if tags1 and tags2:
                        similarity = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
                        
                        if not (similarity >= reference_threshold):
                            continue  # Early return to reduce nesting
                        # Reduced nesting - original condition satisfied
                        if similarity >= reference_threshold:
                            references.append({
                                "source": entry1.get("title", "Unknown"),
                                "target": entry2.get("title", "Unknown"),
                                "similarity": similarity,
                                "relationship": "related"
                            })
            
            return {
                "success": True,
                "cross_references": references
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def compare_documentation_versions(
        self,
        old_content: str,
        new_content: str,
        highlight_changes: bool = True
    ) -> Dict[str, Any]:
        """Compare two versions of documentation"""
        try:
            # Simple diff analysis
            old_words = set(old_content.split())
            new_words = set(new_content.split())
            
            added_words = new_words - old_words
            removed_words = old_words - new_words
            
            comparison = {
                "words_added": len(added_words),
                "words_removed": len(removed_words),
                "similarity": len(old_words.intersection(new_words)) / len(old_words.union(new_words)) \
                    if old_words.union(new_words) \
                    else 0
            }
            
            changes_summary = []
            if added_words:
                changes_summary.append(f"Added {len(added_words)} new terms")
            if removed_words:
                changes_summary.append(f"Removed {len(removed_words)} terms")
            
            return {
                "success": True,
                "comparison": comparison,
                "changes_summary": changes_summary
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_interactive_documentation(
        self,
        knowledge_entries: List[Dict[str, Any]],
        include_search: bool = True,
        include_navigation: bool = True,
        output_format: str = "html"
    ) -> Dict[str, Any]:
        """Generate interactive documentation"""
        try:
            # Generate basic HTML with interactive features
            html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Interactive Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .search-box { margin-bottom: 20px; }
        .nav-menu { background: #f5f5f5; padding: 10px; margin-bottom: 20px; }
        .content { line-height: 1.6; }
    </style>
</head>
<body>
            """
            
            if include_search:
                html_content += """
    <div class="search-box">
        <input type="text" id="search" placeholder="Search documentation..." style="width: 300px; padding: 5px;">
        <button onclick="searchContent()">Search</button>
    </div>
                """
            
            if include_navigation:
                html_content += """
    <div class="nav-menu">
        <strong>Navigation:</strong>
        """ + " | ".join([f'<a href="#{i}">{entry.get("title", f"Section {i}")}</a>' 
                         for i, entry in enumerate(knowledge_entries)]) + """
    </div>
                """
            
            # Add content
            html_content += '<div class="content">'
            for i, entry in enumerate(knowledge_entries):
                html_content += f"""
    <section id="{i}">
        <h2>{entry.get('title', f'Section {i}')}</h2>
        <p>{entry.get('content', '')}</p>
    </section>
                """
            
            html_content += """
    </div>
    
    <script>
        function searchContent() {
            const query = document.getElementById('search').value.toLowerCase();
            const sections = document.querySelectorAll('section');
            
            sections.forEach(section => {
                const text = section.textContent.toLowerCase();
                if (text.includes(query)) {
                    section.style.display = 'block';
                    section.style.backgroundColor = '#ffffcc';
                } else {
                    section.style.display = query ? 'none' : 'block';
                    section.style.backgroundColor = 'transparent';
                }
            });
        }
    </script>
</body>
</html>
            """
            
            return {
                "success": True,
                "documentation": html_content,
                "metadata": {
                    "type": "interactive_documentation",
                    "format": output_format,
                    "features": ["search" if include_search else None, "navigation" if include_navigation else None]
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def export_documentation(
        self,
        content: str,
        format: str,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Export documentation to different formats"""
        try:
            exported_content = await self._apply_formatter(content, format)
            
            metadata = {}
            if include_metadata:
                metadata = {
                    "format": format,
                    "exported_at": datetime.now().isoformat(),
                    "word_count": len(content.split()),
                    "character_count": len(content)
                }
            
            return {
                "success": True,
                "exported_content": exported_content,
                "metadata": metadata
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cleanup(self) -> None:
        """Cleanup document generator resources"""
        await super().cleanup()
        
        # Clear templates and generators
        self.templates.clear()
        self.generators.clear()
        self.formatters.clear()
        
        self._doc_initialized = False
        self.logger.info("Document Generator cleaned up")