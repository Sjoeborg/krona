# krona

[![Release](https://img.shields.io/github/v/release/Sjoeborg/krona)](https://img.shields.io/github/v/release/Sjoeborg/krona)
[![Build status](https://img.shields.io/github/actions/workflow/status/Sjoeborg/krona/master.yml?branch=master)](https://github.com/Sjoeborg/krona/actions/workflows/master.yml?query=branch%3Amaster)
[![codecov](https://codecov.io/gh/Sjoeborg/krona/branch/main/graph/badge.svg)](https://codecov.io/gh/Sjoeborg/krona)
[![Commit activity](https://img.shields.io/github/commit-activity/m/Sjoeborg/krona)](https://img.shields.io/github/commit-activity/m/Sjoeborg/krona)
[![License](https://img.shields.io/github/license/Sjoeborg/krona)](https://img.shields.io/github/license/Sjoeborg/krona)

Transaction tool for Swedish brokers

- **Github repository**: <https://github.com/Sjoeborg/krona/>
- **Documentation** <https://Sjoeborg.github.io/krona/>

## Architecture

The Krona project has been refactored to follow a clean and modular architecture. The key architectural decisions are outlined in `.cursor/rules/architecture.md`. Here is a summary of the key principles:

*   **Separation of Concerns:** The core business logic is separated from the UI, which allows for greater flexibility and easier testing.
*   **Strategy Pattern:** The logic for matching securities is implemented using a strategy pattern, which makes the matching logic more flexible and extensible.
*   **Rich Domain Model:** The `Position` model is a "rich domain model" that is responsible for its own state changes, which simplifies the `TransactionProcessor` and makes the `Position` model more self-contained.

## Modules

The project is divided into the following modules:

*   **`krona.parsers`:** This module is responsible for parsing transaction files from different brokers. Each broker has its own parser that implements the `BaseParser` interface.
*   **`krona.processor`:** This module is the heart of the application and is responsible for processing the transactions and grouping them into positions. It is composed of the following components:
    *   **`TransactionProcessor`:** This is the main component of the processor module. It orchestrates the entire process of fetching transactions, mapping securities, and processing the transactions to create a portfolio of positions.
    *   **`Mapper`:** The `Mapper` is responsible for mapping different notations of the same security to a single, unified symbol. It uses a strategy pattern to apply different matching strategies to the securities.
    *   **`strategies`:** This sub-module contains the different strategies that are used by the `Mapper` to match securities. The following strategies are currently implemented:
        *   **`FuzzyMatchStrategy`:** This strategy uses fuzzy matching to find potential matches between securities.
        *   **`ConflictDetectionStrategy`:** This strategy detects and resolves conflicts in the mapping.
*   **`krona.models`:** This module contains the data models that are used throughout the application. The key models are:
    *   **`Transaction`:** This model represents a single transaction.
    *   **`Position`:** This model represents a position in a single security. It is a "rich domain model" that is responsible for its own state changes.
    *   **`Suggestion`:** This model represents a mapping suggestion that is presented to the user for review.
    *   **`MappingPlan`:** This model represents the entire mapping plan, including all the suggestions and the final symbol mappings.
*   **`krona.ui`:** This module is responsible for the user interface. It is currently implemented as a command-line interface (CLI), but it could be replaced with a graphical user interface (GUI) in the future.
*   **`krona.utils`:** This module contains utility functions that are used throughout the application.

## Todo
- Implement more transaction types (M&A for e.g. SWMA)
- Implement realized gains for non-closed positions?
- What to do with GAV after reopening a closed/moved position?