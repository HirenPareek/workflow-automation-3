from bpmngen import Diagram

d = Diagram('Process_LoanOrigination', 'Bank: Loan Origination & Approval', [
    ('Lane_Applicant', 'Applicant', 220),
    ('Lane_System', 'Core Banking System', 360),
    ('Lane_Officer', 'Loan Officer', 300),
    ('Lane_Fraud', 'Fraud & Compliance', 220),
    ('Lane_UW', 'Underwriter / Credit Committee', 460),
    ('Lane_Ops', 'Operations / Disbursement', 340),
])
A, Y, O, F, U, Q = 'Lane_Applicant', 'Lane_System', 'Lane_Officer', 'Lane_Fraud', 'Lane_UW', 'Lane_Ops'
P, X, Yy = d.P, d.X, d.Y

# ---------------- Applicant ----------------
d.node('Start', 'start', 'Loan needed', A, 0)
d.node('Task_Apply', 'user', 'Submit application & documents', A, 1)
d.node('Task_Upload', 'user', 'Upload missing documents', A, 3, dy=-20)
d.boundary('Ev_DocsTimeout', 'b_timer', '7 days (L1)', 'Task_Upload', frac=0.8, timer='P7D')
d.node('End_Lapsed', 'end', 'Application lapsed', A, 4, dy=60)
d.node('Task_Accept', 'user', 'Review & accept offer', A, 27.5, dy=-20)
d.boundary('Ev_OfferExpiry', 'b_timer', '15 days (L9)', 'Task_Accept', frac=0.8, timer='P15D')
d.node('End_OfferExpired', 'end', 'Offer expired', A, 28.5, dy=60)
d.node('Task_ESign', 'user', 'E-sign loan agreement', A, 29.5, dy=-20)
d.boundary('Ev_SignTimeout', 'b_timer', '48 h (L11)', 'Task_ESign', frac=0.8, timer='PT48H', lab=(52, 14))

# ---------------- Core banking system ----------------
d.node('Task_DocCheck', 'rule', 'Check document completeness', Y, 2)
d.node('Gw_Docs', 'xor', 'Complete?', Y, 3, lab=(-40, 35))
d.node('Task_Fee', 'service', 'Charge processing fee', Y, 4)
d.boundary('Ev_CompFee', 'b_comp', None, 'Task_Fee')
d.node('Task_RefundFee', 'comp', 'Refund processing fee', Y, 4, dy=115)
d.node('Gw_Split', 'and', None, Y, 5)
d.node('Task_KYC', 'service', 'Verify KYC / identity', Y, 6.5, dy=-110)
d.node('Task_BureauReq', 'send', 'Request credit report', Y, 6)
d.node('Gw_BureauWait', 'evt', None, Y, 7)
d.node('Ev_BureauReply', 'catch_msg', 'Report received', Y, 8, ref='Credit report', lab=(0, -32))
d.node('Ev_BureauTimeout', 'catch_timer', '60 s timeout (L4)', Y, 8.6, dy=100, timer='PT60S')
d.node('Gw_BureauRetry', 'xor', 'Retries < 3?', Y, 9.5, dy=100, lab=(0, -40))
d.node('Gw_BureauMerge', 'xor', None, Y, 11.5)
d.node('Gw_Join', 'and', None, Y, 12.5)
d.node('Gw_KYC', 'xor', 'Identity verified?', Y, 13.5, lab=(0, -40))
d.node('Gw_KYCMerge', 'xor', None, Y, 14.5)
d.node('Gw_Alert', 'xor', 'AML / fraud alert?', Y, 15.5, lab=(0, -40))
d.node('Gw_AlertMerge', 'xor', None, Y, 17.5)
d.node('Task_Score', 'rule', 'Score eligibility & risk', Y, 18.5)
d.node('Gw_Risk', 'xor', 'Risk band?', Y, 19.5, lab=(45, -32))
d.node('Task_Offer', 'script', 'Generate loan offer', Y, 25.5)
d.node('Task_SendOffer', 'send', 'Send offer letter', Y, 26.5)
d.node('Task_ValidateSig', 'service', 'Validate e-signature', Y, 30.5)
d.node('Gw_SigOK', 'xor', 'Signature valid?', Y, 31.5, lab=(0, -40))
d.node('Gw_SigAttempts', 'xor', 'Attempts < 2?', Y, 31.5, dy=110, lab=(-62, -28))
d.node('End_OfferCancelled', 'end_msg', 'Offer cancelled, applicant notified', Y, 32, dy=110, lab=(0, 40))

# ---------------- Loan officer ----------------
d.node('Task_Income', 'user', 'Verify income & employment', O, 7)
d.node('Task_ManualCredit', 'user', 'Manual credit check (L4)', O, 10.5, dy=-90)
d.node('Task_ManualKYC', 'user', 'Manually verify identity (L2)', O, 13.5)
d.node('Gw_KYCResolved', 'xor', 'Resolved?', O, 14.5, lab=(45, -30))
d.node('End_RejKYC', 'end', 'Rejected: identity', O, 14.5, dy=95)
d.node('Task_Restructure', 'user', 'Assess restructure options (L5, L6)', O, 19.5)
d.node('Gw_Restructure', 'xor', 'Feasible & first re-score?', O, 20.5, lab=(0, -42))
d.node('End_RejCredit', 'end', 'Rejected: credit', O, 21.5)

# ---------------- Fraud & compliance ----------------
d.node('Task_AML', 'service', 'Fraud & AML screening', F, 7)
d.node('Ev_Escalate', 'throw_esc', 'Escalate (L3)', F, 15.5, ref='Fraud alert')
d.node('Task_Investigate', 'sub', 'Investigate case', F, 16.5)
d.node('Gw_Confirmed', 'xor', 'Fraud confirmed?', F, 17.5, lab=(0, 42))
d.node('Task_SAR', 'send', 'File suspicious activity report', F, 18.5)
d.node('End_Fraud', 'end_term', 'Rejected: fraud', F, 19.5)

# ---------------- Underwriting ----------------
d.node('Task_Underwrite', 'user', 'Underwrite application', U, 20.5)
d.node('Gw_ExtraSplit', 'or', 'Extra checks?', U, 21.5, lab=(-45, 35), default='Gw_ExtraJoin')
d.node('Task_Valuation', 'user', 'Collateral valuation & title check (L8)', U, 22.5, dy=-130)
d.node('Task_Committee', 'user', 'Senior credit committee review (L7)', U, 22.5, dy=95)
d.boundary('Ev_CommitteeSLA', 'b_timer_ni', 'SLA 3 days', 'Task_Committee', timer='P3D', lab=(-58, 6))
d.node('End_EscalateCRO', 'end_esc', 'Escalate to CRO', U, 22.5, dy=200, ref='Committee SLA breach')
d.node('Gw_ExtraJoin', 'or', None, U, 23.5)
d.node('Gw_UWDecision', 'xor', 'Underwriting decision?', U, 24.5, lab=(-60, 35))
d.node('End_RejUW', 'end', 'Rejected: underwriting', U, 24.5, dy=110)

# ---------------- Operations ----------------
d.node('Task_CreateAcct', 'service', 'Create loan account', Q, 32.5, dy=-70)
d.boundary('Ev_CompAcct', 'b_comp', None, 'Task_CreateAcct')
d.node('Task_ReverseAcct', 'comp', 'Reverse loan account', Q, 32.5, dy=60)
d.node('Task_VerifyBenef', 'service', 'Verify beneficiary bank account', Q, 33.5, dy=-70)
d.node('Task_Disburse', 'service', 'Disburse funds', Q, 34.5, dy=-70, loop=True,
       doc='Standard loop: payment gateway call retried up to 2 times before the error boundary fires.')
d.boundary('Ev_DisburseError', 'b_error', 'Payment failed (L12)', 'Task_Disburse', frac=0.8, ref='Disbursement failure', lab=(55, 12))
d.node('Task_HoldFunds', 'user', 'Hold funds & contact applicant', Q, 35.5, dy=60)
d.node('Gw_AcctFixed', 'xor', 'Account corrected?', Q, 36.5, dy=60, lab=(0, -40))
d.node('Ev_UndoAcct', 'throw_comp', 'Undo account', Q, 37.5, dy=60)
d.node('End_DisburseFailed', 'end', 'Disbursement failed', Q, 38.5, dy=60)
d.node('Task_NotifyDisbursed', 'send', 'Notify applicant', Q, 35.5, dy=-70)
d.node('End_Disbursed', 'end', 'Loan disbursed', Q, 36.5, dy=-70)

# Event sub-process: withdrawal at any stage (L10)
d.expanded('Sub_Withdraw', 'Applicant withdraws at any stage (L10)', Q, X(9), Yy(Q, -125), 790, 250, event=True)
for nid, kind, name, c in [('Ev_WithdrawStart', 'start_msg', 'Withdrawal request', 10),
                           ('Ev_CompAll', 'throw_comp', 'Refund fee, release holds', 11.5),
                           ('Task_Close', 'service', 'Close application', 13),
                           ('End_Withdrawn', 'end', 'Application withdrawn', 14.5)]:
    d.node(nid, kind, name, Q, c, parent='Sub_Withdraw', **({'ref': 'Withdrawal request'} if kind == 'start_msg' else {}))
d.flow('Ev_WithdrawStart', 'Ev_CompAll')
d.flow('Ev_CompAll', 'Task_Close')
d.flow('Task_Close', 'End_Withdrawn')

# ---------------- Flows: happy path ----------------
d.flow('Start', 'Task_Apply')
d.flow('Task_Apply', 'Task_DocCheck')
d.flow('Task_DocCheck', 'Gw_Docs')
d.flow('Gw_Docs', 'Task_Fee', 'Yes')
d.flow('Task_Fee', 'Gw_Split')
d.flow('Gw_Split', 'Task_KYC', via=[P(5, Y, -110)])
d.flow('Gw_Split', 'Task_BureauReq')
d.flow('Gw_Split', 'Task_Income', via=[P(5, O)])
d.flow('Gw_Split', 'Task_AML', via=[P(5, F)])
d.flow('Task_BureauReq', 'Gw_BureauWait')
d.flow('Gw_BureauWait', 'Ev_BureauReply')
d.flow('Ev_BureauReply', 'Gw_BureauMerge')
d.flow('Gw_BureauMerge', 'Gw_Join')
d.flow('Task_KYC', 'Gw_Join', via=[P(12.5, Y, -110)])
d.flow('Task_Income', 'Gw_Join', via=[P(12.5, O)])
d.flow('Task_AML', 'Gw_Join', via=[P(12.5, F)])
d.flow('Gw_Join', 'Gw_KYC')
d.flow('Gw_KYC', 'Gw_KYCMerge', 'Yes')
d.flow('Gw_KYCMerge', 'Gw_Alert')
d.flow('Gw_Alert', 'Gw_AlertMerge', 'No')
d.flow('Gw_AlertMerge', 'Task_Score')
d.flow('Task_Score', 'Gw_Risk')
d.flow('Gw_Risk', 'Task_Offer', 'Low: auto-approve', via=[P(19.5, Y, -110), P(25.5, Y, -110)])
d.flow('Gw_Risk', 'Task_Underwrite', 'Medium: manual review', via=[P(20, Y), P(20, U)], lab=(X(20) + 65, Yy(F, -60)))
d.flow('Task_Underwrite', 'Gw_ExtraSplit')
d.flow('Gw_ExtraSplit', 'Task_Valuation', 'Secured loan')
d.flow('Gw_ExtraSplit', 'Task_Committee', 'Above authority / borderline')
d.flow('Gw_ExtraSplit', 'Gw_ExtraJoin', 'None')
d.flow('Task_Valuation', 'Gw_ExtraJoin')
d.flow('Task_Committee', 'Gw_ExtraJoin')
d.flow('Gw_ExtraJoin', 'Gw_UWDecision')
d.flow('Gw_UWDecision', 'Task_Offer', 'Approve', via=[P(25.5, U)])
d.flow('Task_Offer', 'Task_SendOffer')
d.flow('Task_SendOffer', 'Task_Accept')
d.flow('Task_Accept', 'Task_ESign', 'Accepted')
d.flow('Task_ESign', 'Task_ValidateSig', via=[P(30.5, A, -20)])
d.flow('Task_ValidateSig', 'Gw_SigOK')
d.flow('Gw_SigOK', 'Task_CreateAcct', 'Valid', via=[P(32.5, Y)])
d.flow('Task_CreateAcct', 'Task_VerifyBenef')
d.flow('Task_VerifyBenef', 'Task_Disburse')
d.flow('Task_Disburse', 'Task_NotifyDisbursed')
d.flow('Task_NotifyDisbursed', 'End_Disbursed')

# ---------------- Flows: failures ----------------
# L1 documents
d.flow('Gw_Docs', 'Task_Upload', 'No (L1)')
d.flow('Task_Upload', 'Task_DocCheck', 'Resubmit', via=[P(2, A, -20)])
d.flow('Ev_DocsTimeout', 'End_Lapsed')
# L4 credit bureau
d.flow('Gw_BureauWait', 'Ev_BureauTimeout')
d.flow('Ev_BureauTimeout', 'Gw_BureauRetry')
d.flow('Gw_BureauRetry', 'Task_BureauReq', 'Yes: retry', via=[P(9.5, Y, 150), P(6, Y, 150)], lab=(X(7.8), Yy(Y, 162)))
d.flow('Gw_BureauRetry', 'Task_ManualCredit', 'No', via=[P(10.5, Y, 100)])
d.flow('Task_ManualCredit', 'Gw_BureauMerge', via=[P(11.5, O, -90)])
# L2 KYC
d.flow('Gw_KYC', 'Task_ManualKYC', 'No (L2)')
d.flow('Task_ManualKYC', 'Gw_KYCResolved')
d.flow('Gw_KYCResolved', 'Gw_KYCMerge', 'Yes')
d.flow('Gw_KYCResolved', 'End_RejKYC', 'No')
# L3 fraud
d.flow('Gw_Alert', 'Ev_Escalate', 'Yes')
d.flow('Ev_Escalate', 'Task_Investigate')
d.flow('Task_Investigate', 'Gw_Confirmed')
d.flow('Gw_Confirmed', 'Task_SAR', 'Yes')
d.flow('Gw_Confirmed', 'Gw_AlertMerge', 'Cleared')
d.flow('Task_SAR', 'End_Fraud')
# L5 / L6 credit
d.flow('Gw_Risk', 'Task_Restructure', 'Below cut-off')
d.flow('Task_Restructure', 'Gw_Restructure')
d.flow('Gw_Restructure', 'Task_Score', 'Yes: re-score', via=[P(20.5, O, 110), P(18.5, O, 110)], lab=(X(19.5), Yy(O, 122)))
d.flow('Gw_Restructure', 'End_RejCredit', 'No')
# L7 / L8 underwriting
d.flow('Ev_CommitteeSLA', 'End_EscalateCRO')
d.flow('Gw_UWDecision', 'Task_Underwrite', 'Reduce amount / LTV', via=[P(24.5, U, -200), P(20.5, U, -200)], lab=(X(22.5), Yy(U, -212)))
d.flow('Gw_UWDecision', 'End_RejUW', 'Reject')
# L9 offer expiry
d.flow('Ev_OfferExpiry', 'End_OfferExpired')
# L11 e-signature
d.flow('Gw_SigOK', 'Gw_SigAttempts', 'Invalid')
d.flow('Ev_SignTimeout', 'Gw_SigAttempts')
d.flow('Gw_SigAttempts', 'Task_ESign', 'Yes: resend link', via=[P(31.5, Y, 160), P(29.5, Y, 160)], lab=(X(30.5), Yy(Y, 172)))
d.flow('Gw_SigAttempts', 'End_OfferCancelled', 'No')
# L12 disbursement
d.flow('Ev_DisburseError', 'Task_HoldFunds')
d.flow('Task_HoldFunds', 'Gw_AcctFixed')
d.flow('Gw_AcctFixed', 'Task_Disburse', 'Yes: retry', via=[P(36.5, Q, 135), P(34.5, Q, 135)], lab=(X(35.5), Yy(Q, 148)))
d.flow('Gw_AcctFixed', 'Ev_UndoAcct', 'No')
d.flow('Ev_UndoAcct', 'End_DisburseFailed')
# compensation associations
d.assoc('Ev_CompFee', 'Task_RefundFee')
d.assoc('Ev_CompAcct', 'Task_ReverseAcct')

# ---------------- External pool: credit bureau ----------------
by = d.pool_bottom + 50
d.black_box('Participant_CreditBureau', 'Credit Bureau (external)', by, 70)
d.msgflow('Task_BureauReq', 'Participant_CreditBureau', 'Credit report request',
          via=[(X(6) - 25, Yy(Y) + 40), (X(6) - 25, by)])
d.msgflow('Participant_CreditBureau', 'Ev_BureauReply', 'Credit report',
          via=[(X(8), by), (X(8), Yy(Y) + 18)])

if __name__ == '__main__':
    import sys
    open(sys.argv[1], 'w').write(d.to_xml())
