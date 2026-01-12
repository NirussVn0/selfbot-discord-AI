# 📐 Technical Architecture & Design Document

**Project**: Self-Bot Discord AI  
**Version**: 0.1.0  
**Author**: NirussVn0

---

## 1. Architectural Overview

This project adopts a **Modular Monolithic** architecture layered with **Clean Architecture** principles. It strictly separates **Core Infrastructure** (Discord connection), **Application Logic** (Services), and **User Interfaces** (Commands/CLI).

### Layers
1.  **Presentation Layer** (`commands/`, `ui/`): Handles input from Discord users and the Console.
2.  **Application Layer** (`core/`, `services/`): Orchestrates business logic, message routing, and automation flows.
3.  **Domain/Model Layer** (`config/models.py`, `services/owo/models.py`): Defines valid data structures and constraints.
4.  **Infrastructure Layer** (`ai/`, `config/loader.py`): Interfaces with external systems (Gemini API, File System).

---

## 2. Directory Structure

The codebase is organized by **Feature/Module** rather than purely by logical type, ensuring related code stays together.

```
src/selfbot_discord/
├── core/                   # 🧠 Application Kernel
│   ├── bot.py              # Main Entry Point (Lifecycle Management)
│   ├── handlers.py         # Message Processing Pipeline
│   └── decider.py          # Response Heuristics & Decision Engine
├── services/               # ⚙️ Business Logic (Pure Python, mostly UI-agnostic)
│   ├── owo/                # Domain: "ClaimOWO" Automation
│   │   ├── game_service.py # Game Loop logic
│   │   ├── models.py       # Data structures
│   │   └── presenter.py    # UI/String formatting
│   ├── cleanup.py          # Message Deletion Logic
│   └── diagnostics.py      # Log retrieval
├── commands/               # 💬 Interface Adapters (Discord Cogs)
├── config/                 # 📝 Configuration & State Management
└── ui/                     # 🖥️ Terminal UI
```

---

## 3. OOP & SOLID Principles Analysis

The refactoring process heavily emphasized **Object-Oriented Programming** and **SOLID** principles to ensure maintainability and testability.

### 🟢 Single Responsibility Principle (SRP)
*Every class should have one, and only one, reason to change.*

*   **`DiscordSelfBot` vs. `MessageHandler`**:
    *   *Before*: `bot.py` handled connection, message parsing, AI generation, and error handling.
    *   *After*: `DiscordSelfBot` only manages the *connection lifecycle*. `MessageHandler` is solely responsible for *processing messages*.
*   **`ClaimOWOCog` vs. `OWOStatsPresenter`**:
    *   The Cog handles *Discord commands*.
    *   The Presenter handles *string formatting*. If we want to change how the stats look, we edit the Presenter, not the Cog logic.

### 🟢 Open-Closed Principle (OCP)
*Software entities should be open for extension, but closed for modification.*

*   **Command System**: New commands are added by creating new Cogs (e.g., `services/owo/cli.py`) without modifying the core `bot.py`.
*   **Strategy Pattern**: The `MartingaleStrategy` class is designed so new betting strategies (e.g., Fibonacci) could be added by extending a base strategy class without breaking existing game logic.

### 🟢 Liskov Substitution Principle (LSP)
*Objects of a superclass shall be replaceable with objects of its subclasses without breaking the application.*

*   **`Cog` Inheritance**: All command modules inherit from the base `Cog` class (`commands/base.py`). The `CommandRegistry` treats them all uniformly, ensuring any valid Cog can be registered and executed without special casing.

### 🟢 Interface Segregation Principle (ISP)
*Clients should not be forced to depend upon interfaces that they do not use.*

*   **Granular Services**: Instead of a giant "BotService", we have specific services:
    *   `MessageCleaner`: Only for deletion.
    *   `DiagnosticsService`: Only for logs.
    *   `WhitelistService`: Only for permissions.
    *   Consumers only import what they need.

### 🟢 Dependency Inversion Principle (DIP)
*Depend upon abstractions, not concretions.*

*   **Dependency Injection**: The `DiscordSelfBot` constructor receives its dependencies (`ConfigManager`, `GeminiAIService`) rather than instantiating them internally. This allows for:
    *   Easier testing (mocking dependencies).
    *   Swapping implementations (e.g., different config loader) without code changes.

---

## 4. Design Patterns Implemented

### 🏭 Facade Pattern
*   **`MessageHandler`**: Acts as a facade for the complex subsystem of Whitelisting, AI generation, Context storage, and Response Decision, providing a simple `handle_message` interface to the Bot.

### 🧠 Strategy Pattern
*   **`MartingaleStrategy`**: Encapsulates the betting algorithm. The `OWOGameService` uses this strategy object to calculate bets, unaware of the specific mathematical progression being used.

### 👁️ Observer Pattern
*   **`ConfigWatcher`**: Monitors the `config.yaml` file for changes and notifies the `Bot` (subscriber) to reload configuration dynamically without restarting.

### 🎨 Presenter Pattern
*   **`OWOStatsPresenter`**: Decouples the *Data* (`OWOStats`) from the *Presentation* (Discord Markdown). This is a step towards Model-View-Presenter (MVP) architecture.

---

## 5. Workflow Example: "ClaimOWO"

1.  **Command**: User types `h!claimowo`.
2.  **Parsing**: `OWOArgParser` (Static Utility) parses flags like `-b 5000 -side heads`.
3.  **Action**: `ClaimOWOCog` triggers `OWOGameService.start_game()`.
4.  **Loop**:
    *   `OWOGameService` consults `MartingaleStrategy` for the next move.
    *   Service sends `owocf` message.
    *   `OWOMessageParser` (Regex Engine) watches for `owobot` responses.
    *   **Result**: Service updates `OWOStatsTracker`.
5.  **Feedback**: User requests info. `OWOStatsPresenter` formats the data into the "Fake Embed" style for display.
