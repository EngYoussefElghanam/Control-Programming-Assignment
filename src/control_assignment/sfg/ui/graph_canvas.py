"""Qt signal-flow drawing: node layout, directed routing, gain labels and zoom."""
from collections import defaultdict
from math import hypot

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QBrush, QPolygonF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from ..algorithms.traversal import format_number
from ..models import SFGInput


class GraphCanvas(QGraphicsView):
    """A scrollable scene with forward branches above and feedback below nodes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph_scene = QGraphicsScene(self)
        self.setScene(self.graph_scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QColor("#f7f9fc"))
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.node_items = {}
        self.branch_items = {}
        self.gain_labels = {}
        self._auto_fit = True
        self.clear_graph()

    def clear_graph(self):
        self.graph_scene.clear()
        self.node_items.clear()
        self.branch_items.clear()
        self.gain_labels.clear()
        self._auto_fit = True
        self._text("Solve or load a graph to see its signal flow here.", QPointF(250, 100), "#475569")
        self._update_bounds()
        self.fit_graph()

    def _text(self, text, center, color, bold=False, background=False):
        item = self.graph_scene.addSimpleText(str(text), QFont("Arial", 11, QFont.Weight.DemiBold if bold else QFont.Weight.Normal))
        item.setBrush(QBrush(QColor(color)))
        rect = item.boundingRect()
        item.setPos(center.x() - rect.width()/2, center.y() - rect.height()/2)
        item.setZValue(4)
        if background:
            bg = self.graph_scene.addRect(item.sceneBoundingRect().adjusted(-5, -2, 5, 2), QPen(Qt.PenStyle.NoPen), QBrush(QColor("#f7f9fc")))
            bg.setZValue(3)
        return item

    @staticmethod
    def _node_order(graph):
        """Keep connected components contiguous; input first and output last within its component."""
        neighbors = {n: set() for n in graph.nodes}
        for b in graph.branches:
            neighbors[b.source].add(b.target)
            neighbors[b.target].add(b.source)
        remaining = set(graph.nodes)
        ordered = []
        for root in [graph.input_node, *graph.nodes]:
            if root not in remaining:
                continue
            component = {root}
            stack = [root]
            while stack:
                for n in neighbors[stack.pop()] - component:
                    component.add(n)
                    stack.append(n)
            remaining -= component
            members = [n for n in graph.nodes if n in component and n not in (graph.input_node, graph.output_node)]
            if graph.input_node in component:
                members.insert(0, graph.input_node)
            if graph.output_node in component:
                members.append(graph.output_node)
            ordered.extend(members)
        return ordered

    @staticmethod
    def _reserve_lane(lanes, left, right):
        """Reuse a lane only if horizontal spans (including endpoints) do not overlap."""
        for i, spans in enumerate(lanes):
            if all(right < a or left > b for a, b in spans):
                spans.append((left, right))
                return i
        lanes.append([(left, right)])
        return len(lanes) - 1

    def set_graph(self, graph: SFGInput):
        self.graph_scene.clear()
        self.node_items.clear()
        self.branch_items.clear()
        self.gain_labels.clear()
        if not graph.nodes:
            self.clear_graph()
            return
        order = self._node_order(graph)
        index = {n: i for i, n in enumerate(order)}
        # Give long names and gains extra space, without changing the graph topology.
        width = max(88, max(len(str(n)) for n in order)*10 + 24)
        spacing = max(width + 105, max((len(f"{b.label} = {format_number(b.gain)}")*9 + 30 for b in graph.branches), default=180))
        centers = {n: QPointF(i*spacing, 0) for i, n in enumerate(order)}
        lanes = {-1: [], 1: []}
        straight_pairs = set()
        routes = []
        ports = defaultdict(list)
        for b in graph.branches:
            a, z = index[b.source], index[b.target]
            if z == a+1 and (a, z) not in straight_pairs:
                straight_pairs.add((a, z))
                routes.append((b, 0, 0))
            else:
                side = -1 if z >= a else 1
                lane = self._reserve_lane(lanes[side], min(a,z), max(a,z))
                routes.append((b, side, lane))
                ports[b.source, side].append((b.label, "start"))
                ports[b.target, side].append((b.label, "end"))
        offsets = {}
        for key, entries in ports.items():
            for i, entry in enumerate(entries):
                offsets[key, entry] = (i+1)*width/(len(entries)+1) - width/2
        half_height = 23
        for b, side, lane in routes:
            p, q = centers[b.source], centers[b.target]
            color = "#2563a7" if side <= 0 and b.source != b.target else "#a14f22"
            path = QPainterPath()
            if side == 0:
                start, end = QPointF(p.x()+width/2, 0), QPointF(q.x()-width/2, 0)
                path.moveTo(start)
                path.lineTo(end)
                label_at = QPointF((start.x()+end.x())/2, -20)
            else:
                start = QPointF(p.x()+offsets[(b.source, side), (b.label, "start")], side*half_height)
                end = QPointF(q.x()+offsets[(b.target, side), (b.label, "end")], side*half_height)
                level = side*(92 + lane*64)
                # Rounded turns, a horizontal lane and vertical entry into the target.
                path.moveTo(start)
                if b.source == b.target:
                    spread = width/2 + 25
                    path.cubicTo(QPointF(p.x()-spread, level), QPointF(p.x()+spread, level), end)
                    label_at = QPointF(p.x(), path.pointAtPercent(0.5).y()-21)
                else:
                    direction = 1 if end.x() > start.x() else -1
                    bend = min(24, abs(end.x()-start.x())/3)
                    path.lineTo(start.x(), level-side*bend)
                    path.quadTo(start.x(), level, start.x()+direction*bend, level)
                    path.lineTo(end.x()-direction*bend, level)
                    path.quadTo(end.x(), level, end.x(), level-side*bend)
                    path.lineTo(end)
                    label_at = QPointF((start.x()+end.x())/2, level+side*20)
            pen = QPen(QColor(color), 2.2)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            line = self.graph_scene.addPath(path, pen)
            line.setToolTip(f"{b.label}: {b.source} → {b.target}, gain {b.gain}")
            self.branch_items[b.label] = line
            self._arrow(path, color)
            self.gain_labels[b.label] = self._text(f"{b.label} = {format_number(b.gain)}", label_at, color, True, True)
        for node, center in centers.items():
            role = "INPUT" if node == graph.input_node else "OUTPUT" if node == graph.output_node else ""
            color = "#087f78" if role else "#334155"
            rect = QRectF(center.x()-width/2, -half_height, width, 2*half_height)
            shape = QPainterPath()
            shape.addRoundedRect(rect, 12, 12)
            item = self.graph_scene.addPath(shape, QPen(QColor(color), 2), QBrush(QColor("#e4f7f3" if role else "#ffffff")))
            item.setZValue(2)
            item.setToolTip(f"{role or 'NODE'}: {node}")
            self.node_items[node] = item
            self._text(node, QPointF(center.x(), -5 if role else 0), color, True)
            if role:
                small = self._text(role, QPointF(center.x(), 13), color)
                small.setFont(QFont("Arial", 8))
                small.setPos(center.x()-small.boundingRect().width()/2, 8)
        self._update_bounds()
        self.fit_graph()

    def _arrow(self, path, color):
        tip = path.pointAtPercent(1.0)
        prev = path.pointAtPercent(0.99)
        dx, dy = tip.x()-prev.x(), tip.y()-prev.y()
        length = hypot(dx, dy)
        if not length:
            return
        ux, uy = dx/length, dy/length
        base = QPointF(tip.x()-13*ux, tip.y()-13*uy)
        arrow = QPolygonF([tip, QPointF(base.x()-6*uy, base.y()+6*ux), QPointF(base.x()+6*uy, base.y()-6*ux)])
        item = self.graph_scene.addPolygon(arrow, QPen(Qt.PenStyle.NoPen), QBrush(QColor(color)))
        item.setZValue(1)

    def _update_bounds(self):
        self.graph_scene.setSceneRect(self.graph_scene.itemsBoundingRect().adjusted(-35,-35,35,35))

    def fit_graph(self):
        self._auto_fit = True
        self.fitInView(self.graph_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        if self.transform().m11() > 1.35:
            self.resetTransform()
            self.scale(1.35, 1.35)
            self.centerOn(self.graph_scene.sceneRect().center())

    def zoom(self, factor):
        current = self.transform().m11()
        if 0.04 <= current*factor <= 8:
            self._auto_fit = False
            self.scale(factor, factor)

    def wheelEvent(self, event):
        if event.angleDelta().y():
            self.zoom(1.2 if event.angleDelta().y() > 0 else 1/1.2)
            event.accept()
        else:
            super().wheelEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, "_auto_fit", False):
            self.fit_graph()
