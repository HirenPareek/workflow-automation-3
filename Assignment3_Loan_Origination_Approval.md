# Assignment 3: Loan Origination & Approval System

![Loan Origination BPMN Workflow](Loan%20Origination%20BPMN%20Workflow.png)

## Scenario
A retail bank processes personal and secured loan applications. Each application goes through a document check, a set of verifications run in parallel (identity, credit bureau, income, fraud/AML), risk scoring, underwriting where required, offer and acceptance, e-signature and finally disbursement. The model shows the normal route to disbursement and every point where an application can stall, be rejected, expire or be withdrawn.

## Participants
**Pool: Bank – Loan Origination & Approval** (six lanes)

| Lane | Role in the process |
|------|---------------------|
| Applicant | Submits the application, uploads missing documents, accepts the offer, e-signs |
| Core Banking System | Rule checks, fees, KYC, bureau requests, scoring, offer generation, signature validation |
| Loan Officer | Income verification, manual identity and credit checks, restructuring proposals |
| Fraud & Compliance | Fraud/AML screening, investigations, suspicious activity reporting |
| Underwriter / Credit Committee | Manual underwriting, collateral review, senior committee approval |
| Operations / Disbursement | Loan account creation, beneficiary verification, payout |

**Pool: Credit Bureau (external, black box)** – receives the credit report request and returns the report through message flows.

## Process Boundaries
- **Starts when:** an applicant decides to apply and submits the application with documents.
- **Ends when:** the loan is disbursed (**Loan disbursed**), or the application ends as *Application lapsed*, *Rejected: identity*, *Rejected: fraud* (terminate), *Rejected: credit*, *Rejected: underwriting*, *Offer expired*, *Offer cancelled*, *Disbursement failed* or *Application withdrawn*.

---

## Happy Path (10 steps)

| # | Step | Lane | BPMN element |
|---|------|------|--------------|
| 1 | Applicant submits the application and documents | Applicant | User task |
| 2 | System checks document completeness → *Complete?* = Yes | System | Business rule task + XOR |
| 3 | System charges the processing fee | System | Service task (compensable) |
| 4 | Four checks run at the same time: KYC/identity (service), credit report request to the bureau (send task → event-based gateway → *Report received*), income & employment (user, Loan Officer), fraud & AML screening (service, Fraud & Compliance); all four must finish | Several | Parallel split / join, event-based gateway, message flows |
| 5 | *Identity verified?* = Yes and *AML / fraud alert?* = No | System | XOR gateways |
| 6 | System scores eligibility and risk → *Risk band?* = Low (auto-approve) or Medium → underwriter reviews, extra checks run if needed, *Underwriting decision?* = Approve | System / Underwriter | Business rule task, XOR, user task, inclusive split/join |
| 7 | System generates the loan offer and sends the offer letter | System | Script task + send task |
| 8 | Applicant reviews and accepts the offer | Applicant | User task |
| 9 | Applicant e-signs; system validates the signature → *Signature valid?* = Valid | Applicant / System | User task, service task, XOR |
| 10 | Operations creates the loan account, verifies the beneficiary account, disburses funds and notifies the applicant → **End: Loan disbursed** | Operations | Service tasks, send task, end event |

---

## Failure Path Register

| ID | Failure point | Cause / trigger | Resolution in the model | BPMN constructs |
|----|---------------|-----------------|-------------------------|-----------------|
| **L1** | Document check | Missing, expired or unreadable documents | Applicant is asked to upload the missing items and the check re-runs; no upload within 7 days ends the case | XOR *Complete?*, loop, **timer boundary** (P7D) → *Application lapsed* |
| **L2** | KYC / identity | Details do not match official records | Loan officer verifies identity manually; if unresolved the application is rejected | XOR *Identity verified?* → user task → XOR *Resolved?* |
| **L3** | Fraud / AML screening | Forged documents, sanctions or AML watch-list hit | Case is escalated to Fraud & Compliance and investigated; if fraud is confirmed a suspicious activity report is filed and the **whole process is terminated** | **Escalation throw event**, collapsed sub-process, send task, **terminate end event** |
| **L4** | Credit bureau call | Bureau API timeout or outage | Event-based gateway waits for the report or a 60 s timer; retried up to 3 times, then the loan officer runs a manual credit check | **Event-based gateway**, message catch, timer catch, XOR *Retries < 3?*, message flows to external pool |
| **L5** | Credit score | Score below the cut-off | Officer looks for a restructure (guarantor, collateral, smaller amount); if feasible the application is re-scored once, otherwise rejected | XOR *Risk band?* → user task → XOR *Feasible & first re-score?* |
| **L6** | Income / debt-to-income | Income too low or DTI too high | Same restructure loop as L5 (reduced amount or longer tenure), one re-score only | Shared loop with L5 |
| **L7** | High-value / borderline case | Amount above the underwriter's authority or borderline score | Senior credit committee review is added; if it overruns its 3-day SLA the case is escalated to the CRO without stopping the review | **Inclusive gateway** branch, **non-interrupting timer**, escalation end event |
| **L8** | Collateral (secured loans) | Valuation lower than expected, unclear title | Collateral valuation & title check runs as an inclusive branch; underwriter can reduce the amount / LTV and re-underwrite, or reject if title is unclear | Inclusive gateway branch, XOR *Underwriting decision?* loop |
| **L9** | Offer acceptance | Applicant does not respond within the offer validity | Offer expires after 15 days | **Timer boundary** (P15D) → *Offer expired* |
| **L10** | Withdrawal at any stage | Applicant cancels | Interrupting event sub-process broadcasts compensation (fee refunded, loan account reversed if created), closes the application | **Event sub-process** (message start), **compensation throw**, compensation boundaries + associations |
| **L11** | E-signature | Not signed within 48 h, or signature invalid | Signing link resent; after 2 failed attempts the offer is cancelled and the applicant notified | **Timer boundary** (PT48H), XOR *Attempts < 2?*, **message end event** |
| **L12** | Disbursement | Invalid beneficiary account or payment gateway error | Payment retried automatically (loop marker); persistent failure is caught, funds are held and the applicant contacted; if the account cannot be fixed the loan account is reversed through compensation | Loop marker, **error boundary**, XOR *Account corrected?*, compensation throw → *Reverse loan account* |

---

## Task Type Justifications

| Task type | Tasks | Why this type |
|-----------|-------|---------------|
| **User task** | Submit application, Upload missing documents, Verify income & employment, Manual credit check, Manually verify identity, Assess restructure options, Underwrite application, Collateral valuation, Senior committee review, Review & accept offer, E-sign agreement, Hold funds & contact applicant | A person performs the work in a banking or customer portal and makes a judgement |
| **Service task** | Charge processing fee, Verify KYC, Fraud & AML screening, Validate e-signature, Create loan account, Verify beneficiary account, Disburse funds, Close application | Automated calls to internal or third-party services |
| **Business rule task** | Check document completeness, Score eligibility & risk | Driven by a rules/decision table (document checklist, credit policy) that risk teams update independently of the process |
| **Script task** | Generate loan offer | Calculates EMI, rate and schedule and builds the offer document inside the engine |
| **Send task** | Request credit report, Send offer letter, File suspicious activity report, Notify applicant | Sole purpose is sending a message (to the bureau, applicant or regulator) |
| **Collapsed sub-process** | Investigate case | Investigation has its own detailed procedure that would clutter the main diagram |
| **Compensation tasks** | Refund processing fee, Reverse loan account | Only run to undo a completed step when compensation is triggered |

## Gateway Justifications

| Gateway | Type | Why |
|---------|------|-----|
| Split / join around the four checks | **Parallel (AND)** | The checks are independent and all of them are required, so running them together cuts turnaround time; the join waits for all four |
| Wait for credit report | **Event-based** | The next step depends on whichever happens first: the bureau's reply or the timeout |
| Merge after bureau / manual check | Exclusive (XOR) merge | Only one of the two routes produces the credit data, so the parallel join receives exactly one token from this branch |
| Extra checks? / its join | **Inclusive (OR)** | Zero, one or both extra checks (collateral, senior committee) may apply depending on loan type and amount; the join waits only for the branches that were started |
| Complete?, Identity verified?, Resolved?, AML / fraud alert?, Fraud confirmed?, Risk band?, Feasible & first re-score?, Underwriting decision?, Signature valid?, Attempts < 2?, Retries < 3?, Account corrected? | Exclusive (XOR) | A single outcome is chosen from data or a decision |

## Events Used

| Event | Where | Purpose |
|-------|-------|---------|
| Message catch / timer catch after event-based gateway | Credit bureau (L4) | Wait for reply or timeout |
| Interrupting timer boundary | Upload docs (L1), Accept offer (L9), E-sign (L11) | Stop waiting after a deadline |
| Non-interrupting timer boundary | Senior committee review (L7) | Escalate without cancelling the review |
| Error boundary | Disburse funds (L12) | Catch a payment failure after retries |
| Escalation throw / escalation end | Fraud alert (L3), committee SLA (L7) | Hand the case to a higher authority |
| Terminate end | Rejected: fraud (L3) | Kill every remaining token immediately |
| Message end | Offer cancelled (L11) | End and notify the applicant in one step |
| Event sub-process (message start) + compensation | Withdrawal (L10) | Cancel at any stage and roll back completed work |

## Design Decisions
- **Credit bureau as a separate black-box pool**: it is an outside organisation, so communication is shown with message flows, not sequence flows.
- **Verify in parallel, decide afterwards**: all four checks run together, then their results are evaluated one by one (identity → fraud → score), which keeps the parallel join simple and deadlock-free.
- **Fraud uses a terminate end**: once fraud is confirmed nothing else in the instance may continue.
- **Compensation instead of manual clean-up**: fees and loan accounts are reversed by dedicated compensation tasks, triggered both by withdrawal (L10) and by failed disbursement (L12).
- **Every loop is bounded**: bureau retries (3), restructure re-score (1), e-signature attempts (2), payment retries (loop marker).
