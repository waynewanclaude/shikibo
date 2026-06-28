# Documentation Principles & Guidelines

This document defines the rules, standards, and practices for writing, structuring, and maintaining documents shared between humans and AI agents in this project. The primary goal is to **minimize cognitive load for human readers** while ensuring documentation is **precise, structured, and easily parsed or updated by AI tools**.

---

## 1. Core Principles

Documentation serves as the communication bridge and the Single Source of Truth (SSOT) between humans and AI. Good documentation prevents misunderstandings, aligns expectations, and streamlines agent execution.

* **Single Responsibility Principle (SRP)**: Each document must have a single, well-defined purpose.
  * *Example*: `user_intent.md` defines requirements and operational CLI boundaries. It must NOT contain database schemas or implementation details.
  * *Example*: `implementation_plan.md` defines software architecture, dependency layers, and code modifications. It must NOT redefine business requirements.
* **Accuracy over Completeness**: Do not write placeholder text, hypothetical ideas, or speculative future requirements. If a feature or detail is not yet defined, omit it.
* **Low Cognitive Load**: Write for the reader. Avoid dense paragraphs. Use bullet points, bold emphasis, and structured tables to make documents scannable at a glance.
* **Git as the Revision Log**: Do not maintain manual "revision history" tables or author lists inside documents. Let Git handle versioning and history tracking.

---

## 2. Writing & Structuring Rules

To ensure both human readers and AI agents can digest documentation efficiently:

### A. Precise Terminology & Referencing
* **Use Exact Identifiers**: When mentioning CLI options, configuration keys, classes, or file paths, always use their exact, literal names (e.g., `--ignore-missing-pages`, `LayoutAnalyzer`, `config.properties`).
* **Active Hyperlinking**: Create clickable markdown links to referenced code files or specs (e.g., `[builder.py](file:///absolute/path/to/builder.py)`) using absolute paths in workspace files to allow immediate human/AI traversal.

### B. Standardized CLI Option Descriptions
When documenting CLI flags or parameters, always follow a structured, multi-dimensional definition:
* **Type**: The option data type (e.g., `Path`, `int`, `Boolean Flag`).
* **Default**: The default value when the option is omitted.
* **Absent Behavior**: What the system does when the flag/parameter is not provided.
* **Present Behavior**: What the system does when the flag/parameter is provided.

### C. Explicit Action-Oriented Phrasing
* Use active verbs to describe operations (e.g., "crops empty borders," "writes a work log") instead of passive or ambiguous phrasing (e.g., "margins might be trimmed").

---

## 3. Formatting Standards (Gfm)

Documentation must follow standard GitHub Flavored Markdown (GFM) to ensure clean rendering in editors and standard parsers:

* **Heading Hierarchy**: Use a single `#` header for the document title, followed by `##` and `###` headers in logical descending order. Do not skip levels.
* **Fenced Code Blocks**: Always specify the language name for syntax highlighting in code blocks (e.g., ````python ... ```` or ````properties ... ````).
* **Lists**: Use hyphens (`- `) for unordered list items consistently. Maintain uniform indentation (2 or 4 spaces) for nested sub-bullets.
* **Tables**: Use markdown tables to present comparative or multi-dimensional information (such as scope boundaries or data types).
* **Mathematical Notation**: Use standard LaTeX syntax enclosed in single/double dollar signs (e.g., $x_{\text{pdf}} = \text{left} \times 72/\text{DPI}$) for algorithms and calculations.

---

## 4. Collaborative Documentation Workflow

Since both humans and AIs edit these documents, adhere to the following workflow guidelines to prevent conflicts:

* **Incremental Edits**: When updating documents, only modify the specific target sections or lines that have changed. Avoid rewriting entire documents, which increases execution time and risks losing manual human clarifications.
* **Synchronize Specs & Code**: When code changes are made (e.g., removing a flag or adding an argument), immediately update the corresponding section in the documentation files so they remain synchronized.
* **Delineate AI Artifacts**: Keep developer-specific AI workflow tracking files (like plans, tasks, and walkthroughs) in the designated artifacts directory, leaving the project workspace files focused purely on application documentation.
