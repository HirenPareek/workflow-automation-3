"""Tiny BPMN 2.0 generator: compact Python spec -> BPMN XML with full DI (opens in bpmn.io / Camunda)."""
from xml.sax.saxutils import escape

SIZES = {'task': (100, 80), 'gw': (50, 50), 'ev': (36, 36)}
TASKS = {'user': 'userTask', 'service': 'serviceTask', 'rule': 'businessRuleTask', 'script': 'scriptTask',
         'send': 'sendTask', 'receive': 'receiveTask', 'manual': 'manualTask', 'task': 'task',
         'sub': 'subProcess', 'comp': 'serviceTask'}
GWS = {'xor': 'exclusiveGateway', 'and': 'parallelGateway', 'or': 'inclusiveGateway', 'evt': 'eventBasedGateway'}
EVENTS = {  # kind: (tag, definition)
    'start': ('startEvent', None), 'start_msg': ('startEvent', 'message'), 'start_timer': ('startEvent', 'timer'),
    'end': ('endEvent', None), 'end_error': ('endEvent', 'error'), 'end_term': ('endEvent', 'terminate'),
    'end_esc': ('endEvent', 'escalation'), 'end_msg': ('endEvent', 'message'),
    'catch_timer': ('intermediateCatchEvent', 'timer'), 'catch_msg': ('intermediateCatchEvent', 'message'),
    'throw_comp': ('intermediateThrowEvent', 'compensate'), 'throw_esc': ('intermediateThrowEvent', 'escalation'),
    'throw_msg': ('intermediateThrowEvent', 'message'),
    'b_timer': ('boundaryEvent', 'timer'), 'b_timer_ni': ('boundaryEvent', 'timer'), 'b_error': ('boundaryEvent', 'error'),
    'b_msg': ('boundaryEvent', 'message'), 'b_msg_ni': ('boundaryEvent', 'message'), 'b_comp': ('boundaryEvent', 'compensate'),
    'b_esc': ('boundaryEvent', 'escalation'), 'b_esc_ni': ('boundaryEvent', 'escalation'),
}


class Diagram:
    def __init__(self, pid, pool_name, lanes, x0=260, col=150, lane_h=None):
        self.pid, self.pool_name, self.x0, self.col = pid, pool_name, x0, col
        self.lanes = []  # (id, name, top, height)
        y = 80
        for lid, name, h in lanes:
            self.lanes.append((lid, name, y, h))
            y += h
        self.pool_bottom = y
        self.nodes = {}   # id -> dict
        self.order = []
        self.flows = []
        self.assocs = []
        self.extra_pools = []  # (id, name, y, h)
        self.msgflows = []
        self.errors, self.escalations, self.messages = {}, {}, {}

    # ---------- nodes ----------
    def lane(self, lid):
        for l in self.lanes:
            if l[0] == lid:
                return l
        raise KeyError(lid)

    def node(self, nid, kind, name, lane, c, dy=0, parent=None, **o):
        if kind in TASKS:
            w, h = o.get('size', SIZES['task'])
        elif kind in GWS:
            w, h = SIZES['gw']
        else:
            w, h = SIZES['ev']
        _, _, top, lh = self.lane(lane)
        cx = self.x0 + c * self.col
        cy = top + lh / 2 + dy
        n = dict(id=nid, kind=kind, name=name, lane=lane, x=cx - w / 2, y=cy - h / 2, w=w, h=h, parent=parent, **o)
        self.nodes[nid] = n
        self.order.append(nid)
        return n

    def boundary(self, nid, kind, name, host, pos='bottom', frac=0.5, **o):
        hn = self.nodes[host]
        w = h = 36
        if pos == 'bottom':
            cx, cy = hn['x'] + hn['w'] * frac, hn['y'] + hn['h']
        elif pos == 'top':
            cx, cy = hn['x'] + hn['w'] * frac, hn['y']
        elif pos == 'right':
            cx, cy = hn['x'] + hn['w'], hn['y'] + hn['h'] * frac
        n = dict(id=nid, kind=kind, name=name, lane=hn['lane'], x=cx - w / 2, y=cy - h / 2, w=w, h=h,
                 parent=hn['parent'], host=host, bpos=pos, **o)
        self.nodes[nid] = n
        self.order.append(nid)
        return n

    def expanded(self, nid, name, lane, x, y, w, h, event=False, parent=None):
        n = dict(id=nid, kind='expanded', name=name, lane=lane, x=x, y=y, w=w, h=h, parent=parent, event=event)
        self.nodes[nid] = n
        self.order.append(nid)
        return n

    def flow(self, s, t, name=None, via=None, lab=None):
        self.flows.append(dict(id=f'Flow_{len(self.flows) + 1}', s=s, t=t, name=name, via=via, lab=lab))

    def assoc(self, s, t):
        self.assocs.append(dict(id=f'Assoc_{len(self.assocs) + 1}', s=s, t=t))

    def black_box(self, pid, name, y, h=70):
        self.extra_pools.append((pid, name, y, h))

    def msgflow(self, s, t, name=None, via=None):
        self.msgflows.append(dict(id=f'MsgFlow_{len(self.msgflows) + 1}', s=s, t=t, name=name, via=via))

    def X(self, c):
        return self.x0 + c * self.col

    def Y(self, lane, dy=0):
        _, _, top, h = self.lane(lane)
        return top + h / 2 + dy

    def P(self, c, lane, dy=0):
        return (self.X(c), self.Y(lane, dy))

    # ---------- geometry ----------
    def bounds(self, nid):
        if nid in self.nodes:
            n = self.nodes[nid]
            return n['x'], n['y'], n['w'], n['h']
        for pid, name, y, h in self.extra_pools:
            if pid == nid:
                return self.x0 - 200, y, self.width(), h
        raise KeyError(nid)

    def width(self):
        right = max(n['x'] + n['w'] for n in self.nodes.values())
        return right + 80 - (self.x0 - 200)

    @staticmethod
    def dock(b, toward, gateway=False):
        x, y, w, h = b
        cx, cy = x + w / 2, y + h / 2
        tx, ty = toward
        if abs(tx - cx) < 1e-6 and abs(ty - cy) < 1e-6:
            return (cx, cy)
        if abs(tx - cx) < 2:  # vertical
            return (cx, y + h) if ty > cy else (cx, y)
        if abs(ty - cy) < 2:  # horizontal
            return (x + w, cy) if tx > cx else (x, cy)
        # diagonal: pick dominant side
        if abs(tx - cx) * h > abs(ty - cy) * w:
            return (x + w, cy) if tx > cx else (x, cy)
        return (cx, y + h) if ty > cy else (cx, y)

    def route(self, f):
        sb, tb = self.bounds(f['s']), self.bounds(f['t'])
        sn, tn = self.nodes.get(f['s']), self.nodes.get(f['t'])
        scx, scy = sb[0] + sb[2] / 2, sb[1] + sb[3] / 2
        tcx, tcy = tb[0] + tb[2] / 2, tb[1] + tb[3] / 2
        via = f.get('via')
        if via:
            pts = [self.dock(sb, via[0])] + [tuple(p) for p in via] + [self.dock(tb, via[-1])]
            return pts
        # boundary event source: leave from its outer side
        if sn and sn.get('host'):
            pos = sn['bpos']
            if pos == 'bottom':
                start = (scx, sb[1] + sb[3])
                if abs(tcx - scx) < 3:
                    return [start, (tcx, tb[1])]
                end = (tb[0], tcy) if tcx > scx else (tb[0] + tb[2], tcy)
                return [start, (scx, tcy), end]
            if pos == 'top':
                start = (scx, sb[1])
                if abs(tcx - scx) < 3:
                    return [start, (tcx, tb[1] + tb[3])]
                end = (tb[0], tcy) if tcx > scx else (tb[0] + tb[2], tcy)
                return [start, (scx, tcy), end]
        if abs(scy - tcy) < 3:
            if tcx > scx:
                return [(sb[0] + sb[2], scy), (tb[0], tcy)]
            return [(sb[0], scy), (tb[0] + tb[2], tcy)]
        if abs(scx - tcx) < 3:
            return [(scx, sb[1] + sb[3]), (tcx, tb[1])] if tcy > scy else [(scx, sb[1]), (tcx, tb[1] + tb[3])]
        sg = sn and sn['kind'] in GWS
        tg = tn and tn['kind'] in GWS
        if tcx > scx:
            if sg:  # vertical first out of gateway
                return [(scx, sb[1] + sb[3]) if tcy > scy else (scx, sb[1]), (scx, tcy), (tb[0], tcy)]
            if tg:  # horizontal into gateway vertex
                return [(sb[0] + sb[2], scy), (tcx, scy), (tcx, tb[1]) if tcy > scy else (tcx, tb[1] + tb[3])]
            mx = (sb[0] + sb[2] + tb[0]) / 2
            return [(sb[0] + sb[2], scy), (mx, scy), (mx, tcy), (tb[0], tcy)]
        # backward, different rows
        if tcy < scy:
            return [(scx, sb[1]), (scx, tcy), (tb[0] + tb[2], tcy)]
        return [(scx, sb[1] + sb[3]), (scx, tcy), (tb[0] + tb[2], tcy)]

    # ---------- XML ----------
    def _container_of(self, nid):
        return self.nodes[nid]['parent'] if nid in self.nodes else None

    def _node_xml(self, n, ind):
        nid, kind = n['id'], n['kind']
        inc = [f['id'] for f in self.flows if f['t'] == nid]
        out = [f['id'] for f in self.flows if f['s'] == nid]
        io = ''.join(f'{ind}  <bpmn:incoming>{i}</bpmn:incoming>\n' for i in inc) + \
             ''.join(f'{ind}  <bpmn:outgoing>{o}</bpmn:outgoing>\n' for o in out)
        name = f' name="{escape(n["name"], {chr(34): "&quot;"})}"' if n.get('name') else ''
        doc = f'{ind}  <bpmn:documentation>{escape(n["doc"])}</bpmn:documentation>\n' if n.get('doc') else ''
        if kind == 'expanded':
            attrs = ' triggeredByEvent="true"' if n['event'] else ''
            body = self._container_xml(nid, ind + '  ')
            return f'{ind}<bpmn:subProcess id="{nid}"{name}{attrs}>\n{doc}{io}{body}{ind}</bpmn:subProcess>\n'
        if kind in TASKS:
            tag = TASKS[kind]
            attrs = ' isForCompensation="true"' if kind == 'comp' else ''
            if n.get('loop'):
                inner = f'{ind}  <bpmn:standardLoopCharacteristics />\n'
            elif n.get('multi'):
                inner = f'{ind}  <bpmn:multiInstanceLoopCharacteristics isSequential="{str(n["multi"] == "seq").lower()}" />\n'
            else:
                inner = ''
            return f'{ind}<bpmn:{tag} id="{nid}"{name}{attrs}>\n{doc}{io}{inner}{ind}</bpmn:{tag}>\n'
        if kind in GWS:
            tag = GWS[kind]
            dflt = ''
            if n.get('default'):
                for f in self.flows:
                    if f['s'] == nid and f['t'] == n['default']:
                        dflt = f' default="{f["id"]}"'
            return f'{ind}<bpmn:{tag} id="{nid}"{name}{dflt}>\n{doc}{io}{ind}</bpmn:{tag}>\n'
        tag, d = EVENTS[kind]
        attrs = ''
        if tag == 'boundaryEvent':
            attrs = f' attachedToRef="{n["host"]}"'
            if kind.endswith('_ni'):
                attrs += ' cancelActivity="false"'
        if tag == 'startEvent' and n.get('ni'):
            attrs += ' isInterrupting="false"'
        defn = ''
        if d == 'timer':
            t = n.get('timer')
            defn = (f'{ind}  <bpmn:timerEventDefinition id="{nid}_def">\n'
                    f'{ind}    <bpmn:{"timeCycle" if t.startswith("R") else "timeDuration"} xsi:type="bpmn:tFormalExpression">{t}</bpmn:{"timeCycle" if t.startswith("R") else "timeDuration"}>\n'
                    f'{ind}  </bpmn:timerEventDefinition>\n') if t else f'{ind}  <bpmn:timerEventDefinition id="{nid}_def" />\n'
        elif d == 'error':
            ref = n.get('ref')
            r = ''
            if ref:
                self.errors.setdefault(ref, f'Error_{len(self.errors) + 1}')
                r = f' errorRef="{self.errors[ref]}"'
            defn = f'{ind}  <bpmn:errorEventDefinition id="{nid}_def"{r} />\n'
        elif d == 'escalation':
            ref = n.get('ref')
            r = ''
            if ref:
                self.escalations.setdefault(ref, f'Escalation_{len(self.escalations) + 1}')
                r = f' escalationRef="{self.escalations[ref]}"'
            defn = f'{ind}  <bpmn:escalationEventDefinition id="{nid}_def"{r} />\n'
        elif d == 'message':
            ref = n.get('ref')
            r = ''
            if ref:
                self.messages.setdefault(ref, f'Message_{len(self.messages) + 1}')
                r = f' messageRef="{self.messages[ref]}"'
            defn = f'{ind}  <bpmn:messageEventDefinition id="{nid}_def"{r} />\n'
        elif d == 'terminate':
            defn = f'{ind}  <bpmn:terminateEventDefinition id="{nid}_def" />\n'
        elif d == 'compensate':
            defn = f'{ind}  <bpmn:compensateEventDefinition id="{nid}_def" />\n'
        return f'{ind}<bpmn:{tag} id="{nid}"{name}{attrs}>\n{doc}{io}{defn}{ind}</bpmn:{tag}>\n'

    def _container_xml(self, cid, ind):
        out = ''
        for nid in self.order:
            n = self.nodes[nid]
            if n['parent'] == cid:
                out += self._node_xml(n, ind)
        for f in self.flows:
            if self._container_of(f['s']) == cid:
                name = f' name="{escape(f["name"], {chr(34): "&quot;"})}"' if f['name'] else ''
                out += f'{ind}<bpmn:sequenceFlow id="{f["id"]}"{name} sourceRef="{f["s"]}" targetRef="{f["t"]}" />\n'
        for a in self.assocs:
            if self._container_of(a['s']) == cid:
                out += f'{ind}<bpmn:association id="{a["id"]}" associationDirection="One" sourceRef="{a["s"]}" targetRef="{a["t"]}" />\n'
        return out

    def to_xml(self):
        pool_x = self.x0 - 200
        W = self.width()
        body = self._container_xml(None, '    ')
        lanes = ''
        for lid, name, top, h in self.lanes:
            refs = ''.join(f'        <bpmn:flowNodeRef>{nid}</bpmn:flowNodeRef>\n'
                           for nid in self.order if self.nodes[nid]['lane'] == lid and self.nodes[nid]['parent'] is None)
            lanes += f'      <bpmn:lane id="{lid}" name="{escape(name)}">\n{refs}      </bpmn:lane>\n'
        coll = f'  <bpmn:collaboration id="Collaboration_{self.pid}">\n'
        coll += f'    <bpmn:participant id="Participant_{self.pid}" name="{escape(self.pool_name)}" processRef="{self.pid}" />\n'
        for pid, name, y, h in self.extra_pools:
            coll += f'    <bpmn:participant id="{pid}" name="{escape(name)}" />\n'
        for m in self.msgflows:
            s = f'Participant_{self.pid}' if m['s'] == '__pool' else m['s']
            t = f'Participant_{self.pid}' if m['t'] == '__pool' else m['t']
            name = f' name="{escape(m["name"])}"' if m['name'] else ''
            coll += f'    <bpmn:messageFlow id="{m["id"]}"{name} sourceRef="{s}" targetRef="{t}" />\n'
        coll += '  </bpmn:collaboration>\n'
        proc = (f'  <bpmn:process id="{self.pid}" isExecutable="false">\n'
                f'    <bpmn:laneSet id="LaneSet_{self.pid}">\n{lanes}    </bpmn:laneSet>\n{body}  </bpmn:process>\n')
        roots = ''.join(f'  <bpmn:error id="{v}" name="{escape(k)}" errorCode="{escape(k.upper().replace(" ", "_"))}" />\n'
                        for k, v in self.errors.items())
        roots += ''.join(f'  <bpmn:escalation id="{v}" name="{escape(k)}" escalationCode="{escape(k.upper().replace(" ", "_"))}" />\n'
                         for k, v in self.escalations.items())
        roots += ''.join(f'  <bpmn:message id="{v}" name="{escape(k)}" />\n' for k, v in self.messages.items())
        # DI
        di = f'  <bpmndi:BPMNDiagram id="Diagram_{self.pid}">\n    <bpmndi:BPMNPlane id="Plane_{self.pid}" bpmnElement="Collaboration_{self.pid}">\n'

        def shape(eid, x, y, w, h, extra='', lab=None):
            lb = ''
            if lab:
                lx, ly = x + w / 2 + lab[0], y + h / 2 + lab[1]
                lb = (f'        <bpmndi:BPMNLabel>\n          <dc:Bounds x="{lx - 50:.0f}" y="{ly - 14:.0f}" width="100" height="27" />\n'
                      f'        </bpmndi:BPMNLabel>\n')
            return (f'      <bpmndi:BPMNShape id="{eid}_di" bpmnElement="{eid}"{extra}>\n'
                    f'        <dc:Bounds x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" />\n{lb}'
                    f'      </bpmndi:BPMNShape>\n')

        def edge(eid, pts, lab=None):
            wp = ''.join(f'        <di:waypoint x="{x:.0f}" y="{y:.0f}" />\n' for x, y in pts)
            lb = ''
            if lab:
                lb = (f'        <bpmndi:BPMNLabel>\n          <dc:Bounds x="{lab[0] - 45:.0f}" y="{lab[1] - 10:.0f}" width="90" height="20" />\n'
                      f'        </bpmndi:BPMNLabel>\n')
            return f'      <bpmndi:BPMNEdge id="{eid}_di" bpmnElement="{eid}">\n{wp}{lb}      </bpmndi:BPMNEdge>\n'

        di += shape(f'Participant_{self.pid}', pool_x, 80, W, self.pool_bottom - 80, ' isHorizontal="true"')
        for lid, name, top, h in self.lanes:
            di += shape(lid, pool_x + 30, top, W - 30, h, ' isHorizontal="true"')
        for pid, name, y, h in self.extra_pools:
            di += shape(pid, pool_x, y, W, h, ' isHorizontal="true"')
        # expanded first so children draw above
        for nid in self.order:
            n = self.nodes[nid]
            extra = ' isExpanded="true"' if n['kind'] == 'expanded' else ''
            if n['kind'] in ('xor',):
                extra = ' isMarkerVisible="true"'
            di += shape(nid, n['x'], n['y'], n['w'], n['h'], extra, n.get('lab'))
        for f in self.flows:
            di += edge(f['id'], self.route(f), f.get('lab'))
        for a in self.assocs:
            sb, tb = self.bounds(a['s']), self.bounds(a['t'])
            scx = sb[0] + sb[2] / 2
            pts = [(scx, sb[1] + sb[3]), (scx, tb[1] + tb[3] / 2), (tb[0], tb[1] + tb[3] / 2)] \
                if abs(scx - (tb[0] + tb[2] / 2)) > 3 else [(scx, sb[1] + sb[3]), (scx, tb[1])]
            if tb[0] < scx < tb[0] + tb[2]:
                pts = [(scx, sb[1] + sb[3]), (scx, tb[1])]
            di += edge(a['id'], pts)
        for m in self.msgflows:
            if m.get('via'):
                pts = m['via']
            else:
                sb = self.bounds(m['s'])
                tb = self.bounds(m['t'])
                x = m.get('x') or (sb[0] + sb[2] / 2)
                if sb[1] < tb[1]:
                    pts = [(x, sb[1] + sb[3]), (x, tb[1])]
                else:
                    pts = [(x, sb[1]), (x, tb[1] + tb[3])]
            di += edge(m['id'], pts)
        di += '    </bpmndi:BPMNPlane>\n  </bpmndi:BPMNDiagram>\n'
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
                'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                f'id="Definitions_{self.pid}" targetNamespace="http://bpmn.io/schema/bpmn" exporter="Python BPMN generator" exporterVersion="1.0">\n'
                + coll + proc + roots + di + '</bpmn:definitions>\n')
