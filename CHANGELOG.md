# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Core: Pydantic data models for pipeline data flow (T-03)
- Core: Unified LLM client with multi-model support via OpenAI-compatible API (T-04)
- Core: Agent base class with prompt loading and LLM calling (T-05)
- Core: Pipeline engine orchestrating Parse → Analyze → Synthesize → Generate → Review (T-10)
- Parsers: PDF parser using PyMuPDF (T-06), PPT parser using python-pptx (T-13), Note parser for MD/TXT/DOCX (T-14)
- Agents: Parser, Analyzer, Generator, Reviewer, Synthesizer (T-07/T-08/T-09/T-15/T-17)
- Pipeline: Reviewer feedback loop with configurable max retries (T-18)
- Store: SQLite + FTS5 knowledge base with tag system (T-19)
- Outputs: Markdown, DOCX, PPTX report writers (T-20)
- CLI: analyze, search, list commands via Typer (T-11/T-21)
- Config: settings.yaml with per-agent model assignment, 4 prompt templates (T-12/T-21)

### Testing
- 124 unit tests covering all modules (models, LLM client, engine, parsers, agents, knowledge base)
- All tests passing, 0 lint errors (ruff)

## [0.0.1] - 2026-02-21

### Added
- Initial project structure
- Project scaffolding and base configuration
