from bpmngen import Diagram

d = Diagram('Process_ProjectApproval', 'University Final-Year Project Approval & Allocation', [
    ('Lane_Student', 'Student Team', 220),
    ('Lane_Coord', 'Project Coordinator', 220),
    ('Lane_System', 'Project Management System', 260),
    ('Lane_Guide', 'Faculty Guide', 280),
    ('Lane_Committee', 'Review Committee (HoD)', 380),
])
S, C, Y, G, R = 'Lane_Student', 'Lane_Coord', 'Lane_System', 'Lane_Guide', 'Lane_Committee'
P, X, Yy = d.P, d.X, d.Y

# ---------------- Student ----------------
d.node('Start', 'start', 'Proposal window opens', S, 0)
d.node('Gw_MergeSubmit', 'xor', None, S, 1)
d.node('Task_Submit', 'user', 'Submit project proposal', S, 2,
       doc='Team fills title, abstract, objectives, domain, member roll numbers and preferred guides.')
d.boundary('Ev_Deadline', 'b_timer', 'Deadline passed (F4)', 'Task_Submit', timer='P21D')
d.node('Task_Correct', 'user', 'Correct / modify proposal', S, 3)
d.node('Task_Revise', 'user', 'Revise proposal per comments', S, 11)
d.boundary('Ev_ReviseTimeout', 'b_timer', '7 days (F5)', 'Task_Revise', frac=0.8, timer='P7D')
d.node('End_Lapsed', 'end', 'Proposal lapsed', S, 12, dy=60)
d.node('End_Allocated', 'end', 'Project allocated', S, 18)

# ---------------- Coordinator ----------------
d.node('Task_ReviewLate', 'user', 'Review late-submission request', C, 2)
d.node('Gw_Late', 'xor', 'Late entry allowed?', C, 1, lab=(0, 45))
d.node('End_DeadlineMissed', 'end', 'Deadline missed', C, 0)
d.node('Task_Screen', 'user', 'Screen proposal', C, 6)
d.node('Task_ReviewMatch', 'user', 'Review similarity match (F3)', C, 8)
d.node('Gw_Match', 'xor', 'Outcome?', C, 9, lab=(45, -30))
d.node('End_Duplicate', 'end_error', 'Rejected: duplicate topic', C, 9, dy=75, ref='Duplicate topic')
d.node('Task_ManualAlloc', 'user', 'Allocate guide manually / co-guide / wait-list', C, 13)
d.node('Task_NotifyManual', 'manual', 'Notify team manually (F10)', C, 19)

# ---------------- System ----------------
d.node('Task_Validate', 'service', 'Validate form & team rules', Y, 3)
d.node('Gw_Valid', 'xor', 'Valid?', Y, 4, lab=(-35, -35))
d.node('Gw_Attempts', 'xor', 'Attempts < 2?', Y, 5, lab=(0, 42))
d.node('Task_NotifyTeamRule', 'send', 'Notify team-rule violation', Y, 5, dy=85)
d.node('End_InvalidTeam', 'end_error', 'Invalid team (F2)', Y, 6, dy=85, ref='Invalid team')
d.node('Task_Similarity', 'service', 'Run similarity / duplicate check', Y, 7)
d.node('Gw_Similar', 'xor', 'Similarity > threshold?', Y, 8, lab=(55, 35))
d.node('Task_Rule', 'rule', 'Match guide by domain & workload', Y, 12)
d.node('Gw_GuideFound', 'xor', 'Guide available?', Y, 13, lab=(0, 42))
d.node('Task_SendRequest', 'send', 'Send allocation request to guide', Y, 14)
d.node('Task_Record', 'service', 'Record allocation', Y, 17)
d.boundary('Ev_CompRecord', 'b_comp', None, 'Task_Record')
d.node('Task_Notify', 'send', 'Notify team & coordinator', Y, 18, loop=True,
       doc='Standard loop: retried up to 3 times before the error boundary fires.')
d.boundary('Ev_NotifyError', 'b_error', 'Mail / DB failure (F10)', 'Task_Notify', pos='top', frac=0.85, ref='Notification failure', lab=(62, -10))

# ---------------- Guide ----------------
d.node('Task_GuideReview', 'user', 'Review allocation request', G, 15, dy=-55)
d.boundary('Ev_GuideTimeout', 'b_timer', 'No reply in 3 days (F9)', 'Task_GuideReview', timer='P3D', lab=(-62, 12))
d.node('Gw_Accept', 'xor', 'Accepted?', G, 16, dy=-55, lab=(0, -40))
d.node('Gw_GuideAttempts', 'xor', 'Attempts < 3?', G, 15, dy=60, lab=(62, 18))
d.node('Task_ReleaseSlot', 'comp', 'Release guide slot', G, 17, dy=10)

# ---------------- Committee ----------------
d.node('Task_Evaluate', 'user', 'Evaluate proposal', R, 10)
d.boundary('Ev_ReviewSLA', 'b_timer_ni', 'SLA breached (F7)', 'Task_Evaluate', timer='R2/P5D', lab=(-58, 14))
d.node('Task_Remind', 'send', 'Remind members / escalate to HoD', R, 10, dy=125)
d.node('End_Reminded', 'end', 'Reminder sent', R, 9, dy=125)
d.node('Gw_Decision', 'xor', 'Committee decision?', R, 11, lab=(62, 18))
d.node('Gw_RevCycles', 'xor', 'Revision cycles < 2?', R, 11, dy=-125, lab=(-75, -30))
d.node('Task_SendReasons', 'send', 'Send rejection reasons', R, 11, dy=125)
d.node('Gw_NewTopic', 'xor', 'New topic already used?', R, 12, dy=125)
d.node('End_Rejected', 'end', 'Proposal rejected', R, 13, dy=125)

# Event sub-process: withdrawal after approval (F11)
ex, ey = X(14.4), Yy(R, -130)
d.expanded('Sub_Withdrawal', 'Withdrawal after allocation (F11)', R, ex, ey, 640, 250, event=True)
d.nodes['Sub_Withdrawal']['parent'] = None
for nid, kind, name, c, dy in [('Ev_WithdrawStart', 'start_msg', 'Team dissolves / guide on leave', 15, 0),
                               ('Ev_Compensate', 'throw_comp', 'Undo allocation', 16, 0),
                               ('Task_Requeue', 'user', 'Return team to allocation queue', 17, 0),
                               ('End_Requeued', 'end', 'Team re-queued', 18, 0)]:
    d.node(nid, kind, name, R, c, dy=dy - 5, parent='Sub_Withdrawal', **({'ni': False, 'ref': 'Withdrawal notice'} if kind == 'start_msg' else {}))
d.flow('Ev_WithdrawStart', 'Ev_Compensate')
d.flow('Ev_Compensate', 'Task_Requeue')
d.flow('Task_Requeue', 'End_Requeued')

# ---------------- Flows: happy path ----------------
d.flow('Start', 'Gw_MergeSubmit')
d.flow('Gw_MergeSubmit', 'Task_Submit')
d.flow('Task_Submit', 'Task_Validate')
d.flow('Task_Validate', 'Gw_Valid')
d.flow('Gw_Valid', 'Task_Screen', 'Valid')
d.flow('Task_Screen', 'Task_Similarity')
d.flow('Task_Similarity', 'Gw_Similar')
d.flow('Gw_Similar', 'Task_Evaluate', 'No')
d.flow('Task_Evaluate', 'Gw_Decision')
d.flow('Gw_Decision', 'Task_Rule', 'Approved', via=[P(11.5, R), P(11.5, Y)])
d.flow('Task_Rule', 'Gw_GuideFound')
d.flow('Gw_GuideFound', 'Task_SendRequest', 'Yes')
d.flow('Task_SendRequest', 'Task_GuideReview')
d.flow('Task_GuideReview', 'Gw_Accept')
d.flow('Gw_Accept', 'Task_Record', 'Accepted')
d.flow('Task_Record', 'Task_Notify')
d.flow('Task_Notify', 'End_Allocated', via=[P(18, S)][:0] or None)

# ---------------- Flows: failures ----------------
# F4 deadline
d.flow('Ev_Deadline', 'Task_ReviewLate')
d.flow('Task_ReviewLate', 'Gw_Late')
d.flow('Gw_Late', 'Gw_MergeSubmit', 'Yes')
d.flow('Gw_Late', 'End_DeadlineMissed', 'No')
# F1 / F2 validation
d.flow('Gw_Valid', 'Gw_Attempts', 'Incomplete (F1)')
d.flow('Gw_Attempts', 'Task_Correct', 'Yes')
d.flow('Gw_Attempts', 'Task_Screen', 'No: escalate', via=[P(6, Y)])
d.flow('Task_Correct', 'Task_Validate', 'Resubmit')
d.flow('Gw_Valid', 'Task_NotifyTeamRule', 'Team rule broken (F2)')
d.flow('Task_NotifyTeamRule', 'End_InvalidTeam')
# F3 similarity
d.flow('Gw_Similar', 'Task_ReviewMatch', 'Yes (F3)')
d.flow('Task_ReviewMatch', 'Gw_Match')
d.flow('Gw_Match', 'Task_Evaluate', 'Acceptable', via=[P(10, C)])
d.flow('Gw_Match', 'Task_Correct', 'Modify topic', via=[P(9, S, -70), P(3, S, -70)])
d.flow('Gw_Match', 'End_Duplicate', 'Reject')
# F7 SLA
d.flow('Ev_ReviewSLA', 'Task_Remind')
d.flow('Task_Remind', 'End_Reminded')
# F5 revise
d.flow('Gw_Decision', 'Gw_RevCycles', 'Revise (F5)', lab=(X(11) - 40, Yy(R, -60)))
d.flow('Gw_RevCycles', 'Task_Revise', 'Yes')
d.flow('Gw_RevCycles', 'Task_SendReasons', 'No', via=[P(10.6, R, -125), P(10.6, R, 125)], lab=(X(10.6) - 18, Yy(R, -95)))
d.flow('Task_Revise', 'Task_Evaluate', 'Resubmitted', via=[P(10, S)])
d.flow('Ev_ReviseTimeout', 'End_Lapsed')
# F6 reject
d.flow('Gw_Decision', 'Task_SendReasons', 'Rejected (F6)', lab=(X(11) - 45, Yy(R, 60)))
d.flow('Task_SendReasons', 'Gw_NewTopic')
d.flow('Gw_NewTopic', 'End_Rejected', 'Yes')
d.flow('Gw_NewTopic', 'Gw_MergeSubmit', 'No: submit new topic', via=[P(12, R, 172), P(12.5, R, 172), P(12.5, S, -90), P(1, S, -90)], lab=(X(12.5) + 70, Yy(R, 160)))
# F8 no guide
d.flow('Gw_GuideFound', 'Task_ManualAlloc', 'No (F8)')
d.flow('Task_ManualAlloc', 'Task_SendRequest', via=[P(14, C)])
# F9 decline / timeout
d.flow('Ev_GuideTimeout', 'Gw_GuideAttempts')
d.flow('Gw_Accept', 'Gw_GuideAttempts', 'Declined (F9)', via=[P(16, G, 60)])
d.flow('Gw_GuideAttempts', 'Task_Rule', 'Yes: exclude guide, rerun',
       via=[P(15, G, 115), P(12, G, 115)], lab=(X(13.3), Yy(G, 103)))
d.flow('Gw_GuideAttempts', 'Task_ManualAlloc', 'No', via=[P(13.5, G, 60), P(13.5, C, 60), P(13, C, 60)])
# F10 notification failure
d.flow('Ev_NotifyError', 'Task_NotifyManual')
d.flow('Task_NotifyManual', 'End_Allocated')
# compensation
d.assoc('Ev_CompRecord', 'Task_ReleaseSlot')

if __name__ == '__main__':
    import sys
    open(sys.argv[1], 'w').write(d.to_xml())
