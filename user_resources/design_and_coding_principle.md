# Design and Coding Principles

This document defines the industry standards, rules of thumb, and design patterns adopted in this project. The primary goal is to **minimize cognitive load for human readers** and ensure the codebase remains maintainable, testable, and extensible.

These principles draw heavily from Robert C. Martin's ("Uncle Bob") *Clean Code* philosophy and SOLID design guidelines.

---

## 1. Core Goal: Lowering Cognitive Load
Code is read far more often than it is written. Every line of code should be optimized for the human reader. Lowering cognitive load means making the code's behavior, intent, and structure obvious at a glance.

### Key Rules to Reduce Cognitive Load:
* **Prefer Linear Flow**: Avoid deeply nested branches. Use early exits (guard clauses) to handle error conditions or boundary cases up front, leaving the happy path unindented.
* **Descriptive Intermediate Variables**: Instead of writing complex, multi-clause logical conditions, assign components to descriptive boolean variables.
  * *Bad*: `if (arg.status == 2 and not arg.is_skipped) or (arg.retry_count > 3 and arg.is_active):`
  * *Good*:
    ```python
    is_valid_success = (arg.status == 2 and not arg.is_skipped)
    has_exceeded_retries = (arg.retry_count > 3 and arg.is_active)
    if is_valid_success or has_exceeded_retries:
    ```
* **Avoid Magic Numbers**: Never hardcode numerical values or string literals. Declare them as named constants with clear purposes.
* **Keep Data & Behavior Asymmetric**:
  * **Data Structures** should expose data and have no meaningful behavior (e.g., dataclasses, DTOs).
  * **Objects/Services** should hide their data behind abstractions and expose behavior (e.g., analyzers, builders). Do not mix them.
* **User-Facing Message Quality**: User messages, questions, warnings, and errors must be readable, practical, and useful to the person using the application. Avoid raw dumps, unexplained internal state, or unbounded lists except as a last resort for unrecoverable exceptions or diagnostic stack traces.

---

## 2. Uncle Bob's "Clean Code" Rules

### A. Meaningful Names
* **Intention-Revealing**: Names must tell you why it exists, what it does, and how it is used.
* **Pronounceable and Searchable**: Avoid abbreviations like `prc_pg_lst`. Use `process_page_list`.
* **Class Names**: Use noun or noun phrases (e.g., `LayoutAnalyzer`, `ExecutionReporter`). Avoid vague verbs or generic names like `Manager` or `Processor` when possible.
* **Method Names**: Use verb or verb phrases (e.g., `analyze_page_layout`, `record_metric`).

### B. Functions
* **Small**: Functions should rarely exceed 20 lines of code.
* **Do One Thing**: A function should do only one thing, do it well, and do it uniquely. If a function contains sections that can be grouped under a descriptive sub-header, it is doing more than one thing and should be split.
* **Single Level of Abstraction**: All statements within a function must be at the same level of utility/abstraction (e.g., do not mix high-level business logic with low-level raw pixel array slicing).
* **Arguments**: The ideal number of arguments is zero (niladic). Next is one (monadic), followed by two (dyadic). Three arguments (triadic) should be avoided where possible. More than three arguments requires passing a configuration object or dictionary.

### C. Comments
* **Code as Documentation**: Do not write comments to explain poorly written code. Refactor the code so it explains itself.
* **Good Comments**:
  * Explanation of intent (why a specific approach was chosen).
  * Warning of consequences (e.g., `# CPU bound, do not run synchronously in the UI thread`).
  * Legal/Copyright headers.
* **Bad Comments**:
  * Redundant comments that simply restate what the code does (e.g., `i = i + 1  # Increment i`).
  * Commented-out code (delete it; Git will retain the history).
  * Journal comments (historical changes—leave this to Git commit logs).

### D. Error Handling
* **Prefer Exceptions to Return Codes**: Returning error codes forces the caller to handle errors immediately, cluttering flow control.
* **Write Try-Except Blocks First**: Define the boundary of your transaction first. It establishes what the caller should expect, regardless of what goes wrong.
* **Don't Return Null/None**: Returning `None` forces the caller to write endless null check statements. If a query returns no results, return an empty collection or raise a specific exception.
* **Don't Pass Null/None**: Avoid passing `None` into methods if possible. It introduces hidden defensive checks.

---

## 3. SOLID Design Principles

* **Single Responsibility Principle (SRP)**: A class should have one, and only one, reason to change. Separate concerns (e.g., do not mix file searching, OCR processing, and PDF formatting in a single CLI script).
* **Open/Closed Principle (OCP)**: Software entities should be open for extension but closed for modification. Use interfaces or abstract base classes to allow adding new behaviors (e.g., a new OCR engine wrapper) without modifying existing caller logic.
* **Liskov Substitution Principle (LSP)**: Subclasses must be substitutable for their base classes. A subclass should not break the contracts (expectations, inputs, or exception specifications) of its parent.
* **Interface Segregation Principle (ISP)**: Clients should not be forced to depend on methods they do not use. Keep interfaces small, focused, and cohesive.
* **Dependency Inversion Principle (DIP)**: Depend on abstractions, not concretions. High-level modules should not depend on low-level modules; both should depend on abstractions (e.g., depend on `BaseOCREngine`, not `EasyOCREngine` directly).

---

## 4. Practical & Human-Friendly Design Patterns

Design patterns should only be used when they simplify the code structure and make it easier to understand. Avoid academic or highly theoretical patterns that inflate complexity.

### A. Creational Patterns
* **Factory Method**: Useful when you need to instantiate objects whose concrete class is determined dynamically (e.g., choosing between `EasyOCREngine` and another engine based on configuration).
* **Builder**: Simplifies the construction of complex objects, especially when there are many optional configuration arguments (e.g., configuring `PDFBuilder` options).

### B. Structural Patterns
* **Adapter (Wrapper)**: Crucial for wrapping third-party libraries (e.g., wrapping EasyOCR and DocLayout-YOLO behind project-owned adapters). This isolates external API changes from your core codebase and satisfies SOLID's Dependency Inversion Principle.
* **Facade**: Provides a unified, simplified interface to a complex subsystem. Instead of exposing raw coordinate mappings, file searches, and image manipulations directly in your CLI runner, wrap them under a cohesive orchestrator engine.

### C. Behavioral Patterns
* **Strategy**: Defines a family of algorithms, encapsulates each one, and makes them interchangeable (e.g., swapping different layouts or text ordering strategies at runtime).
* **Observer**: A subscription mechanism to delegate events (e.g., progress bar updates, logging handlers, or UI notifications) without tightly coupling components.

---

## 5. Coding Rules of Thumb

* **DRY (Don't Repeat Yourself)**: Avoid duplicating logic. Every piece of knowledge must have a single, unambiguous representation within a system.
* **KISS (Keep It Simple, Stupid)**: Choose the simplest implementation that fulfills the task. Do not pre-optimize or over-engineer.
* **YAGNI (You Aren't Gonna Need It)**: Do not write code or abstractions based on hypothetical future requirements. Only build what is needed *now*.
* **The Boy Scout Rule**: Always leave the codebase cleaner than you found it. If you see a small mess, clean it up as you work, regardless of who wrote it.
* **The Rule of Three**: When you duplicate code for the first time, write it. When you duplicate it a second time, cower. When you duplicate it a third time, refactor it into a shared utility or helper.
