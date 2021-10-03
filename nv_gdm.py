from __future__ import annotations

from nv_typing import *
from nv_polar_graph import (BasePolarGraph,
                            PolarNode)
from nv_attributed_objects import (DynamicAttributeControl,
                                   CoordinateSystem,
                                   Point,
                                   Line,
                                   GroundLine)
from nv_associations import (TreeNodeAssociation,
                             DependenceNodeAssociation,
                             FieldNodeAssociation,
                             FieldLinkAssociation,
                             FieldMoveAssociation)
import nv_global_names


class GlobalDataManager:

    def __init__(self):
        self._tree_graph = BasePolarGraph()
        self._dependence_graph = BasePolarGraph()
        self._field_graph = BasePolarGraph()

        self.init_tree_graph()
        self.init_dependence_graph()
        self.init_field_graph()

        self._class_instances: dict[str, set[DynamicAttributeControl]] = {}
        self._current_edit_object = None

    @property
    def tree_graph(self):
        return self._tree_graph

    @property
    def dependence_graph(self):
        return self._dependence_graph

    @property
    def field_graph(self):
        return self._field_graph

    def init_tree_graph(self):
        a_m = self.tree_graph.am
        a_m.node_assoc_class = TreeNodeAssociation
        a_m.auto_set_curr_context()

    def init_dependence_graph(self):
        a_m = self.dependence_graph.am
        a_m.node_assoc_class = DependenceNodeAssociation
        a_m.auto_set_curr_context()

    def init_field_graph(self):
        a_m = self.field_graph.am
        a_m.node_assoc_class = FieldNodeAssociation
        a_m.link_assoc_class = FieldLinkAssociation
        a_m.move_assoc_class = FieldMoveAssociation
        a_m.auto_set_curr_context()

    def add_to_tree_graph(self, obj: DynamicAttributeControl):
        tg = self.tree_graph
        a_m = tg.am
        node_class = a_m.get_single_elm_by_cell_content(PolarNode, obj.__class__.__name__)
        if node_class is None:
            node_class, _, _ = tg.insert_node_single_link()
            a_m.create_cell(node_class, obj.__class__.__name__)
        node_obj, _, _ = tg.insert_node_single_link(node_class.ni_nd)
        a_m.create_cell(node_obj, obj.name)


GDM = GlobalDataManager()

if __name__ == '__main__':
    cs_1 = CoordinateSystem()
    cs_2 = CoordinateSystem()
    ln_1 = Line()
    ln_2 = Line()
    GDM.add_to_tree_graph(cs_1)
    GDM.add_to_tree_graph(cs_2)
    GDM.add_to_tree_graph(ln_1)
    GDM.add_to_tree_graph(ln_2)

    start_ni = GDM.tree_graph.inf_node_pu.ni_nd
    print(GDM.tree_graph.layered_representation(start_ni))
    print(GDM.field_graph.am.curr_context)
    print(GDM.field_graph)

    # print(GDM.tree_graph.am.curr_context)
    # print(GDM.tree_graph.am.get_single_elm_by_cell_content(PolarNode, 'CoordSystem_1'))
