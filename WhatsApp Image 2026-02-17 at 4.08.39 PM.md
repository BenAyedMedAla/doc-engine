---
source: WhatsApp Image 2026-02-17 at 4.08.39 PM.jpeg
parser: vlm
model: Qwen/Qwen3.6-27B-FP8
pages: 1
---

This image displays a detailed architecture diagram for a system called **"P-SAST Architecture"**, version 0.1.0, which appears to be an AI-enhanced Static Application Security Testing (SAST) pipeline. The diagram is organized into logical sections and shows data flow, services, and integrations.

---

### 🧩 **Overall Structure**

The architecture is divided into several key sections:

1. **External Data Sources**
2. **Docker Compose Services**
3. **Scan Pipeline (AI-SAST Container)**
4. **Output Formatting**
5. **Connection Types Legend**
6. **Tooltip: NIST NVD API**

---

## 🔍 Section-by-Section Analysis

---

### 1. **External Data Sources**

These are external APIs or databases that feed threat intelligence and vulnerability data into the system.

- **MITRE CWE API**  
  - ~1400 weaknesses  
  - Weekly sync, Free API

- **NIST NVD** *(highlighted with blue border)*  
  - CVE database  
  - Daily sync, Rate limited  
  - Tooltip explains: External API at `https://services.nvd.nist.gov/rest/json/cves/2.0`, free key available (50 req/30s vs 5 req/30s without), provides CVE records linked to CWEs with CVSS scores, severity, affected products. Synced daily by sync worker. Paginated (2000 results/page).

- **OWASP Top 10**  
  - Web + LLM + Agentic  
  - Saved data, 3 files

- **EU AI Act**  
  - Annex III categories  
  - Saved data, 17 categories

- **ENISA Threats**  
  - AI threat landscape  
  - Saved data, 15 categories

> All these sources feed into downstream services via dotted lines (likely async or scheduled syncs).

---

### 2. **Docker Compose Services**

Core infrastructure components running in containers.

- **Sync Worker**  
  - Schedules: CWE Sunday 2 AM, NVD Daily 3 AM  
  - ~250MB, schedule 1h

- **PostgreSQL 16**  
  - 13 tables, named volume  
  - Tables: scans, findings, cve_database, nvd_cve, owasp, eu_aiact, enisa, audit_log

- **MCP Server :8080**  
  - 19 tools, Starlette/Uvicorn  
  - 4 scan, 7 auth, 3 verify, 3 AI, 2 audit

- **Verifier Service :8081**  
  - Z3 SMT solver microservice  
  - ~400MB, HTTP API, 11 strategies

> These services form the backend engine — storing data, exposing APIs, and performing verification.

---

### 3. **Scan Pipeline (AI-SAST Container — 1.5GB)**

This is the core scanning and analysis engine, likely running as a single container or orchestrated set of processes.

#### Input & Detection:
- **CLI Entry**  
  - Click, Rich console  
  - Flags: `--path`, `--output`, `--severity`, `--verbose`

- **Language Detect**  
  - 6 languages supported: Python, JS/TS, Java, C#, PHP

#### Scanning Engines:
- **Semgrep Scanner**  
  - 382 rules, 32 YAML files  
  - 12 traditional, 10 AI/LLM, 70 agentic

- **Semgrep Rules**  
  - Traditional: SQLi, XSS, CmdInj, SSRF, CSRF, PathTrav, Crypto, XXE, Deser, MiscConfig, ErrHandle  
  - AI/LLM: OWASP LLM 2023 10/10

#### Post-Processing:
- **Deduplication**  
  - Key: (file, line, type, id)  
  - Set-based O(1) lookup

- **Severity Filter**  
  - Threshold: --min-severity  
  - Levels: critical, high, medium, low

- **Claude AI Analysis**  
  - False positive reduction  
  - Max 300 findings limit  
  - Webhook MCP, single-shot API  
  - With MCP, agentic stateful loop  
  - Confidence 0.0–1.0, max 3 seconds

- **False Positive Filter**  
  - Threshold: --ai-confidence (default 0.7)  
  - FP + high confidence → filtered out  
  - Severity adjustment on remaining

#### Verification & Enrichment:
- **Z3 Result Cache**  
  - Hash-based dedup  
  - hit/miss tracking  
  - verification_cache

- **Z3 Formal Verification**  
  - 11 strategies, ~38% rule coverage  
  - Traditional: SQLi, XSS, CmdInj, PathTrav, SSRF  
  - AI/LLM: PromptInj, Outzilli  
  - Agentic: GoalHack, CodeExec, ToolMisuse, MemPoison  
  - SAT result 0.95, UNSAT ratio 0.95, heuristic 0.70

- **EU Compliance Enrich**  
  - CWE → EU AI Act mapping  
  - CWE → ENISA threats  
  - OWASP category context  
  - VulnerabilityAssessors

- **DB Persistence**  
  - Scan → scans table  
  - Finding → findings table  
  - AI → ai_analyses table  
  - Z3 → verification_proofs  
  - audit_log

> This section shows a sophisticated pipeline combining static analysis (Semgrep), formal methods (Z3), AI filtering (Claude), and compliance enrichment (EU AI Act, ENISA).

---

### 4. **Output Formatting**

Final output generation from processed results.

- **Text (Rich)**  
  - Rich tables + colors  
  - default

- **JSON**  
  - Machine-readable  
  - minimal.json

> Outputs can be human-readable (rich text) or machine-parseable (JSON).

---

### 5. **Connection Types Legend**

Located bottom-left corner:

- **Data Flow** → solid line
- **API call** → dashed line
- **DB read/write** → dotted line
- **External sync** → dash-dot line

> Helps interpret how components interact.

---

### 6. **Tooltip: NIST NVD API**

Appears when hovering over “NIST NVD” box.

- URL: `https://services.nvd.nist.gov/rest/json/cves/2.0`
- Free API key available (rate limits: 50 req/30s with key, 5 req/30s without)
- Provides CVE records linked to CWEs with CVSS scores, severity, affected products
- Synced daily by sync worker
- Paginated (2000 results/page)

---

## 🎯 Key Observations & Insights

- **AI Integration**: Heavy use of AI — Claude for false positive reduction, Semgrep with AI/LLM rules, agentic loops.
- **Formal Methods**: Z3 SMT solver used for formal verification of code properties — advanced technique for proving absence of certain vulnerabilities.
- **Compliance Focus**: Explicit integration with EU AI Act and ENISA threats — suggests target audience includes regulated industries (finance, healthcare, gov).
- **Modular Design**: Clear separation between data ingestion, scanning, filtering, verification, and output.
- **Scalability Considerations**: Rate limiting on NVD, pagination, caching (Z3 Result Cache), deduplication — all indicate design for scale.
- **Containerized**: Entire pipeline runs in Docker Compose — easy deployment and reproducibility.
- **Rich CLI Interface**: Supports verbose mode, severity filtering, multiple output formats — developer-friendly.

---

## ⚠️ Potential Concerns / Questions

- **Rate Limits**: NVD API has strict rate limits — may bottleneck large-scale scans unless properly throttled or cached.
- **AI Confidence Threshold**: Default 0.7 for filtering — could miss true positives if too aggressive; needs tuning per project.
- **Z3 Coverage**: Only ~38% rule coverage — significant portion of vulnerabilities not formally verified.
- **Resource Usage**: AI-SAST container is 1.5GB — may require substantial memory/CPU for large codebases.
- **Dependency on External APIs**: Reliance on MITRE, NVD, OWASP, EU AI Act, ENISA — any downtime affects system functionality.

---

## ✅ Strengths

- Comprehensive threat intelligence integration
- Multi-layered analysis (static + formal + AI)
- Compliance-aware (EU AI Act, ENISA)
- Modular, containerized, scalable design
- Developer-friendly CLI and output options

---

## 📌 Summary

This is a state-of-the-art, AI-augmented SAST platform designed for modern software development teams needing deep security analysis with compliance awareness. It combines traditional static analysis (Semgrep), formal verification (Z3), and AI-driven filtering (Claude) to reduce noise and improve accuracy. The architecture is well-structured, modular, and built for scalability and maintainability.

It’s particularly suited for organizations operating under regulatory frameworks like the EU AI Act, where automated compliance checks are critical.

--- 

✅ **Final Note**: The diagram is visually rich and technically dense — ideal for architects, DevSecOps engineers, and security researchers evaluating or extending such a system.