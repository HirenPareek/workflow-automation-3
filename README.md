# BPMN Workflow Assignments – Business Process Modeling

This repository contains BPMN 2.0 models and written documentation for two business process scenarios. Each model traces the full happy path from start to finish and handles every realistic failure point with the appropriate BPMN construct (boundary events, retry loops, escalation, compensation and event sub-processes).

## 📋 Table of Contents

- [Overview](#-overview)
- [Assignments](#-assignments)
- [Project Structure](#-project-structure)
- [How to Use](#-how-to-use)
- [Tools & Technologies](#️-tools--technologies)
- [Key Features](#-key-features)
- [Assignment Details](#-assignment-details)
- [Evaluation Criteria](#-evaluation-criteria)

## 🎯 Overview

Each process is modelled with:

- **A complete happy path** that can be traced from the start event to the success end event
- **A numbered failure register** (F1–F11, L1–L12), each failure mapped to a concrete element in the diagram
- **Correct BPMN 2.0 constructs**: typed tasks, XOR / AND / OR / event-based gateways, timer, error, message, escalation and compensation events
- **Swim lanes** that make every participant's responsibility explicit
- **Editable `.bpmn` files** with full diagram layout, so they open directly in bpmn.io or Camunda Modeler with zero import warnings

## 📁 Assignments

### 1️⃣ Assignment 1: Student Project Approval & Allocation System
How a university department takes a final-year project proposal from submission to a confirmed faculty guide.

- **Lanes**: Student Team, Project Coordinator, Project Management System, Faculty Guide, Review Committee (HoD)
- **11 failure paths (F1–F11)**: validation errors, team-rule violations, duplicate topics, missed deadline, revision loop, rejection, overdue review, no guide, guide decline/timeout, notification failure, withdrawal after allocation
- **Highlights**: bounded retry loops, interrupting and non-interrupting timers, error events, event sub-process with compensation

### 3️⃣ Assignment 3: Loan Origination & Approval System
How a bank takes a loan application from submission to disbursement.

- **Lanes**: Applicant, Core Banking System, Loan Officer, Fraud & Compliance, Underwriter / Credit Committee, Operations; plus an external **Credit Bureau** pool
- **12 failure paths (L1–L12)**: incomplete documents, KYC mismatch, fraud/AML hit, bureau timeout, low score, high DTI, high-value case, collateral issues, offer expiry, withdrawal, e-signature failure, disbursement error
- **Highlights**: parallel verification, event-based gateway, inclusive gateway, terminate end event, message flows, compensation

## 📂 Project Structure

```
bpmn-workflow-assignments/
│
├── Assignment1_Student_Project_Approval.bpmn   # Editable BPMN 2.0 XML (with diagram layout)
├── Assignment1_Student_Project_Approval.md     # Detailed documentation
├── Assignment1_Student_Project_Approval.svg    # Vector diagram (zoomable)
├── Student Project Approval BPMN Workflow.png  # Rendered diagram
│
├── Assignment3_Loan_Origination_Approval.bpmn
├── Assignment3_Loan_Origination_Approval.md
├── Assignment3_Loan_Origination_Approval.svg
├── Loan Origination BPMN Workflow.png
│
├── tools/                                      # Scripts that generate and render the diagrams
│   ├── bpmngen.py                              # Small BPMN 2.0 + DI generator
│   ├── assignment1.py                          # Assignment 1 model definition
│   ├── assignment3.py                          # Assignment 3 model definition
│   └── render.py                               # Renders .bpmn → PNG/SVG with bpmn-js
│
└── README.md
```

## 🚀 How to Use

### View the diagrams
Open the PNG files, or the SVG files for lossless zoom:
- `Student Project Approval BPMN Workflow.png`
- `Loan Origination BPMN Workflow.png`

### Edit the BPMN files
The `.bpmn` files are standard BPMN 2.0 XML and include diagram interchange (layout) data.

1. **Online**: go to [demo.bpmn.io](https://demo.bpmn.io/), choose *Open*, and select the `.bpmn` file.
2. **Desktop**: install [Camunda Modeler](https://camunda.com/download/modeler/) and open the file directly.

### Read the documentation
Each assignment `.md` file contains:
- Scenario, participants and process boundaries
- Happy path (10 steps) with the lane and BPMN element for each step
- Failure path register with cause, resolution and BPMN construct
- Task type and gateway type justifications
- Events used and design decisions

### Regenerate the diagrams (optional)
```bash
cd tools
npm install bpmn-js@17        # renderer used by render.py
pip install playwright && playwright install chromium
python3 assignment1.py ../Assignment1_Student_Project_Approval.bpmn
python3 render.py ../Assignment1_Student_Project_Approval.bpmn "../Student Project Approval BPMN Workflow.png" ../Assignment1_Student_Project_Approval.svg
```
Do the same with `assignment3.py` for the loan model.

## 🛠️ Tools & Technologies

- **BPMN 2.0** (OMG standard) – modelling notation
- **bpmn-js** – rendering and validation (same engine as bpmn.io / Camunda Modeler)
- **Python** – model generation
- **Markdown** – documentation

## ✨ Key Features

### Exception handling
- **Boundary events**: interrupting timers (deadlines), non-interrupting timers (SLA reminders), error boundaries (technical failures)
- **Bounded loops**: every retry or resubmission has a counter gateway, so no instance can loop forever
- **Escalation**: overdue reviews and fraud alerts move to a higher authority
- **Compensation**: completed work (fees, allocations, loan accounts) is undone explicitly
- **Event sub-processes**: withdrawal can interrupt the process at any stage

### Notation coverage
| Category | Used |
|----------|------|
| Tasks | User, Service, Business Rule, Script, Send, Manual, Compensation, Collapsed sub-process, Loop marker |
| Gateways | Exclusive (XOR), Parallel (AND), Inclusive (OR), Event-based |
| Events | Start, Message start, End, Error end, Terminate end, Message end, Escalation end, Timer / Message catch, Escalation / Compensation throw, Timer / Error / Compensation boundary |
| Structure | Pools, lanes, black-box pool, message flows, associations, event sub-processes |

## 📊 Assignment Details

### Assignment 1: Student Project Approval (11 failure paths)

| ID | Failure | Resolution |
|----|---------|------------|
| F1 | Form validation errors | Correct & resubmit (max 2), then escalate to coordinator |
| F2 | Team-rule violation | Notify team, error end *Invalid team* |
| F3 | Duplicate / plagiarised topic | Coordinator review: accept, modify or reject |
| F4 | Submission deadline missed | Timer boundary → late-submission request |
| F5 | Revision requested | Revise within 7 days, max 2 cycles |
| F6 | Committee rejects | One new topic allowed, then final rejection |
| F7 | Review overdue | Non-interrupting timer: reminder, then HoD escalation |
| F8 | No guide available | Manual allocation / co-guide / wait-list |
| F9 | Guide declines or no reply | Exclude guide, re-match (max 3), then manual |
| F10 | Notification / DB failure | Auto-retry ×3, error boundary → manual notification |
| F11 | Withdrawal after allocation | Event sub-process + compensation releases guide slot |

### Assignment 3: Loan Origination (12 failure paths)

| ID | Failure | Resolution |
|----|---------|------------|
| L1 | Incomplete documents | Upload request, 7-day timer, else *Application lapsed* |
| L2 | KYC mismatch | Manual identity verification, else reject |
| L3 | Fraud / AML hit | Escalate → investigate → SAR + terminate if confirmed |
| L4 | Credit bureau timeout | Event-based wait, retry ×3, then manual credit check |
| L5 | Score below cut-off | Restructure (guarantor/collateral/amount), re-score once |
| L6 | Income / DTI too weak | Same restructure loop (amount/tenure), re-score once |
| L7 | High-value / borderline | Senior committee review with SLA escalation to CRO |
| L8 | Collateral issues | Valuation branch; reduce LTV and re-underwrite, or reject |
| L9 | Offer not accepted | 15-day timer → *Offer expired* |
| L10 | Applicant withdraws | Event sub-process + compensation (refund fee, reverse account) |
| L11 | E-signature fails | Resend link (max 2), then cancel and notify |
| L12 | Disbursement error | Auto-retry, hold funds & contact applicant, else reverse account |

## 📝 Evaluation Criteria

- ✅ **Complete happy paths** – traceable from start to success end
- ✅ **Correct task types** – each type justified in the documentation
- ✅ **Correct gateways** – splits and joins matched (parallel join never waits on an XOR branch)
- ✅ **Comprehensive failure identification** – 23 failure paths across both processes
- ✅ **Sensible resolutions** – each failure ends in recovery, escalation or a named end state
- ✅ **Valid BPMN 2.0** – files import into bpmn-js with zero warnings

## 📄 License

Provided for educational purposes. All scenarios are fictional; a real implementation would need additional security, compliance and organisation-specific rules.
