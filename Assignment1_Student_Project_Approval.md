# Assignment 1: Student Project Approval & Allocation System

![Student Project Approval BPMN Workflow](Student%20Project%20Approval%20BPMN%20Workflow.png)

## Scenario
Every final-year student team in the department has to get a project proposal approved and a faculty guide assigned before work can begin. A proposal is checked by the system, screened by the project coordinator, tested for duplicate topics, evaluated by a review committee and, once approved, matched to a guide. The guide must formally accept the team before the allocation is final.

## Participants (single pool, five lanes)
| Lane | Role in the process |
|------|---------------------|
| Student Team | Submits, corrects and revises the proposal |
| Project Coordinator | Screens proposals, handles exceptions, allocates guides manually when needed |
| Project Management System | Validation, similarity check, guide matching, records and notifications |
| Faculty Guide | Accepts or declines the allocation request |
| Review Committee (HoD) | Evaluates proposals and decides approve / revise / reject |

## Process Boundaries
- **Starts when:** the proposal submission window opens for a team.
- **Ends when:** a guide has accepted the team and everyone is notified (**Project allocated**), or the proposal is closed as *Deadline missed*, *Invalid team*, *Rejected: duplicate topic*, *Proposal lapsed* or *Proposal rejected*.

---

## Happy Path (10 steps)

| # | Step | Lane | BPMN element |
|---|------|------|--------------|
| 1 | Team submits the project proposal | Student Team | User task |
| 2 | System validates form fields and team rules → *Valid?* = Valid | System | Service task + XOR gateway |
| 3 | Coordinator screens the proposal | Coordinator | User task |
| 4 | System runs the similarity / duplicate-topic check → *Similarity > threshold?* = No | System | Service task + XOR gateway |
| 5 | Committee evaluates the proposal → *Committee decision?* = Approved | Committee | User task + XOR gateway |
| 6 | System matches a guide by domain and current workload → *Guide available?* = Yes | System | Business rule task + XOR gateway |
| 7 | System sends the allocation request to the guide | System | Send task |
| 8 | Guide reviews the request → *Accepted?* = Accepted | Faculty Guide | User task + XOR gateway |
| 9 | System records the allocation | System | Service task (compensable) |
| 10 | System notifies team and coordinator → **End: Project allocated** | System → Student | Send task (loop) + end event |

---

## Failure Path Register

| ID | Failure point | Cause / trigger | Resolution in the model | BPMN constructs |
|----|---------------|-----------------|-------------------------|-----------------|
| **F1** | Form validation | Missing abstract, empty fields, invalid roll numbers | Team corrects and resubmits; after 2 failed attempts the proposal is escalated straight to the coordinator's screening | XOR *Valid?* → XOR *Attempts < 2?* → loop via *Correct / modify proposal* |
| **F2** | Team rules | Team too large, or a member already belongs to another team | Team is told which rule was broken; the instance ends so the team can re-form and start again | Send task + **error end event** *Invalid team* |
| **F3** | Duplicate / plagiarised topic | Similarity score above threshold against past projects | Coordinator reviews the match: accept as original, ask for a modified topic (loop back to correction) or reject | XOR *Similarity > threshold?*, user task, XOR *Outcome?*, **error end event** |
| **F4** | Submission deadline | Team has not submitted when the window closes | Coordinator reviews a late-submission request; if allowed the team re-enters submission, otherwise the case ends | **Interrupting timer boundary** (P21D) on *Submit*, XOR merge before *Submit* |
| **F5** | Committee asks for revision | Scope too wide, weak objectives or novelty | Team revises within 7 days; a maximum of 2 revision cycles, after which the case is treated as rejected; no response in 7 days ends as *Proposal lapsed* | XOR *Revision cycles < 2?*, **timer boundary** (P7D) on *Revise* |
| **F6** | Committee rejects | Infeasible, out of syllabus, no resources | Reasons are sent; the team may submit one new topic (loop to the start), a second rejection is final | Send task, XOR *New topic already used?*, loop to merge gateway |
| **F7** | Review overdue | Committee has not decided within the SLA | Reminder after 5 days and escalation to the HoD after 10 days, without stopping the review | **Non-interrupting timer boundary** (cycle R2/P5D) |
| **F8** | No guide available | No domain match, or every guide at maximum load | Coordinator allocates manually, appoints a co-guide/external guide, or wait-lists the team | XOR *Guide available?* → user task |
| **F9** | Guide declines or does not reply | Workload, conflict of interest, no response in 3 days | Guide is excluded and the matching rule re-runs; after 3 attempts the coordinator allocates manually | **Timer boundary** (P3D) + XOR *Attempts < 3?* loop |
| **F10** | Notification / database failure | Mail server down, write error | Send task retries automatically (loop marker, 3 tries); a persistent failure raises an error caught by the boundary and the coordinator notifies the team manually | Loop marker + **error boundary event** + manual task |
| **F11** | Withdrawal after allocation | Team dissolves or guide goes on leave | Interrupting event sub-process triggers compensation, which releases the guide slot (*Release guide slot*), and the team is returned to the allocation queue | **Event sub-process** (message start), **compensation throw**, compensation boundary + association |

---

## Task Type Justifications

| Task type | Tasks | Why this type |
|-----------|-------|---------------|
| **User task** | Submit proposal, Correct/modify, Revise, Screen, Review similarity match, Evaluate, Review allocation request, Allocate manually, Review late request, Return team to queue | A person works on it through the project portal and makes a decision |
| **Service task** | Validate form & team rules, Run similarity check, Record allocation | Fully automated system operations with no human input |
| **Business rule task** | Match guide by domain & workload | The outcome comes from a rule table (domain match, max load per guide), so it can change without changing the process |
| **Send task** | Notify team-rule violation, Send allocation request, Notify team & coordinator, Send rejection reasons, Remind / escalate | The task's only job is to deliver a message to a participant |
| **Manual task** | Notify team manually | Done outside the system (phone call / notice board) when automation has failed |
| **Compensation task** | Release guide slot | Only runs to undo *Record allocation* when compensation is triggered |

## Gateway Justifications

| Gateway | Type | Why |
|---------|------|-----|
| Valid?, Similarity > threshold?, Outcome?, Committee decision?, Guide available?, Accepted? | Exclusive (XOR) | Exactly one outcome is possible for each decision |
| Attempts < 2?, Revision cycles < 2?, Attempts < 3?, New topic already used? | Exclusive (XOR) | Loop counters that cap retries so no loop runs forever |
| Late entry allowed? | Exclusive (XOR) | Coordinator gives a single yes/no ruling |
| Merge before *Submit proposal* | Exclusive (XOR) merge | Re-joins the normal start, the late-entry path and the new-topic path without waiting for all of them |

Parallel and inclusive gateways were deliberately **not** used here: every check depends on the result of the previous one (no point in matching a guide before approval), so the flow is sequential by nature.

## Events Used

| Event | Where | Purpose |
|-------|-------|---------|
| Interrupting timer boundary | Submit (F4), Revise (F5), Review allocation request (F9) | Stop waiting after a deadline |
| Non-interrupting timer boundary | Evaluate proposal (F7) | Chase the committee without cancelling the review |
| Error boundary | Notify team & coordinator (F10) | Catch a technical failure after automatic retries |
| Error end events | Invalid team, Rejected: duplicate topic | Business errors that end the case abnormally |
| Message start (event sub-process) | Withdrawal after allocation (F11) | Can interrupt the process at any time once triggered |
| Compensation throw + boundary | Undo allocation / Record allocation | Roll back a completed step |

## Design Decisions
- **One pool, five lanes**: all participants belong to the same department, so they share one process and hand work over with sequence flows instead of message flows.
- **Retry limits everywhere**: every loop (F1, F5, F6, F9, F10) has a counter, so the process always terminates.
- **Escalation over silent failure**: when automation or people fail to respond, the case moves to the coordinator rather than stalling.
- **Compensation for F11**: an allocation that has already been recorded is undone explicitly, so guide workload figures stay correct.
