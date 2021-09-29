from __future__ import annotations

from nv_typing import *
from nv_names_control import names_control
from nv_string_set_class import bounded_string_set, BoundedStringSet
from nv_polar_graph import (BasePolarGraph,
                            PolarNode,
                            PGLink,
                            PGMove,
                            End,
                            PGRoute)  #
from nv_attribute_format import BSSAttributeType, AttributeFormat
from nv_associations import AttribNodeAssociation, AttribMoveAssociation

BSSDependency = bounded_string_set('BSSDependency', [['dependent'], ['independent']])
BSSBool = bounded_string_set('BSSBool', [['True'], ['False']])

# class VirtualSplitter(BoundedStringSet):
#
#     def __init__(self, str_val: str, condition: bool) -> None:
#         super().__init__([['True'], ['False']], str_val)
#         self.condition = condition


class AttribDescriptor:
    def __get__(self, instance, owner=None) -> Union[list[AttributeFormat], AttribDescriptor]:
        if instance is None:
            return self
        g_t = instance.graph_template
        route_from_to_: PGRoute = g_t.free_roll(g_t.inf_node_pu.ni_nd)
        route_result_ = g_t.am.extract_route_content({PolarNode: 'attr_tuple', PGMove: 'splitter_value'},
                                                     route_from_to_, get_as_strings=False)
        result: list[AttributeFormat] = []
        for i, element in enumerate(route_result_):
            if not(type(element) == tuple):
                continue
            else:
                name, cls = element
                if cls is None:
                    result.append(AttributeFormat(BSSAttributeType('title'), name))
                elif issubclass(cls, BoundedStringSet):
                    str_value = route_result_[i+1]
                    result.append(AttributeFormat(BSSAttributeType('bss_splitter'), name,
                                                  str_value, cls.unique_values))
                else:
                    result.append(AttributeFormat(BSSAttributeType('value'), name,
                                                  'Wow value'))
        print('route_result', len(route_result_), route_result_)
        return result

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class DynamicAttributeControl:
    graph_attr = AttribDescriptor()

    def __init__(self):
        self.init_all_attributes()

    def change_splitter_value(self):
        pass

    def change_value(self):
        pass

    def init_all_attributes(self):
        g_t: BasePolarGraph = self.graph_template
        all_attribute_values = g_t.am.extract_sbg_content({PolarNode: 'attr_tuple'}, g_t,
                                                          get_as_strings=False)
        print('all attributes :', all_attribute_values)


class GraphTemplatesDescriptor:
    def __init__(self):
        self.initialised_class_graphs = {}

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        g_t = BasePolarGraph()
        a_m = g_t.am
        a_m.node_assoc_class = AttribNodeAssociation
        a_m.move_assoc_class = AttribMoveAssociation

        splitter_preferences = None

        if owner in self.initialised_class_graphs:
            return self.initialised_class_graphs[owner]

        if owner == CoordSystem:
            node_rel_cs, _, _ = g_t.insert_node_single_link()
            a_m.create_cell(node_rel_cs, 'cs_relative_to', 'CoordSystem')
            node_check_dependence, _, _ = g_t.insert_node_single_link(node_rel_cs.ni_nd)
            a_m.create_cell(node_check_dependence, 'dependence', 'BSSDependency')
            node_x, link_up_x, _ = g_t.insert_node_single_link(node_check_dependence.ni_nd)
            a_m.create_cell(node_x, 'x', 'int')
            move_to_x = node_check_dependence.ni_nd.get_move(link_up_x)
            a_m.create_cell(move_to_x, 'dependent', 'str')
            node_y, _, _ = g_t.insert_node_single_link(node_x.ni_nd)
            a_m.create_cell(node_y, 'y', 'int')
            node_alpha, link_up_alpha, _ = g_t.insert_node_single_link(node_check_dependence.ni_nd)
            a_m.create_cell(node_alpha, 'alpha', 'int')
            move_to_alpha = node_check_dependence.ni_nd.get_move(link_up_alpha)
            a_m.create_cell(move_to_alpha, 'independent', 'str')
            node_connect_polarity, _, _ = g_t.insert_node_single_link(node_alpha.ni_nd)
            a_m.create_cell(node_connect_polarity, 'connection_polarity', 'End')
            node_co_x = g_t.insert_node_neck(g_t.inf_node_nd.ni_pu)
            a_m.create_cell(node_co_x, 'co_x', 'BSSBool')
            node_co_y = g_t.insert_node_neck(g_t.inf_node_nd.ni_pu)
            a_m.create_cell(node_co_y, 'co_y', 'BSSBool')

            splitter_preferences = {'dependence': 'independent',
                                    'connection_polarity': 'negative_down',
                                    'co_x': 'True',
                                    'co_y': 'True'}

        self.expand_splitters(g_t)
        self.apply_preferences(g_t, splitter_preferences)
        self.initialised_class_graphs[owner] = g_t

        return g_t

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))

    @staticmethod
    def expand_splitters(graph_template_: BasePolarGraph):
        for node in graph_template_.nodes:
            assoc_tuple = node.associations['attr_tuple']
            if assoc_tuple is None:
                continue
            name, cls = assoc_tuple
            if issubclass(cls, BoundedStringSet):
                unique_values: list = cls.unique_values
                need_count_of_links = len(unique_values)
                existing_count_of_links = len(node.ni_nd.links)
                if need_count_of_links == existing_count_of_links:
                    continue
                assert existing_count_of_links == 1, 'Found situation not fully expanded splitter with <> 1 count links'
                link = node.ni_nd.links.pop()
                for _ in range(need_count_of_links-existing_count_of_links):
                    graph_template_.connect_nodes(*link.ni_s)
                for link_ in node.ni_nd.links:
                    move_ = node.ni_nd.get_move(link_)
                    move_.associations['splitter_value'] = unique_values.pop()
        return

    @staticmethod
    def apply_preferences(graph_template_: BasePolarGraph, splitter_preferences_: Optional[dict[str, str]] = None):
        if splitter_preferences_ is None:
            return
        for node_str, move_str in splitter_preferences_.items():
            print('node, move = ', node_str, move_str)
            node: PolarNode = graph_template_.am.get_element_by_content_value(PolarNode,
                                                                              {'attr_tuple': node_str})
            move = graph_template_.am.get_element_by_content_value(PGMove, {'splitter_value': node_str},
                                                                   node.ni_nd.moves)
            node.ni_nd.choice_move_activate(move)


@names_control
class CoordSystem(DynamicAttributeControl):
    graph_template = GraphTemplatesDescriptor()

    def __init__(self):
        super(CoordSystem, self).__init__()


# , x: int = None, y: int = None, alpha: int = None, co_X: int = None, co_Y: int = None
#         self.x = x
#         self.y = y
#         self.alpha = alpha
#         self.co_X = co_X
#         self.co_Y = co_Y


# class IndependentBasis(CoordSystem):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.basis = GCS
#
#
# class DependentBasis(CoordSystem):
#     def __init__(self, basis: CoordSystem = None, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.basis = basis


if __name__ == '__main__':

    test = 'test_1'
    if test == 'test_1':
        pass
    GCS = CoordSystem(name='CoordSystem_GCS')
    # arg_spec_DB = inspect.getfullargspec(DependentBasis.__init__)
    # arg_spec_CS = inspect.getfullargspec(CoordSystem.__init__)
    # print('arg_spec_DB', arg_spec_DB)
    # print('arg_spec_CS', arg_spec_CS)
    # print('mro', DependentBasis.mro())
    # print('annotations', DependentBasis.__init__.__annotations__)
    # print('attributes', inspect.getattr_static(GCS, 'x'))

    ga = GCS.graph_attr
    print('graph_attr = ', len(ga), ga)
    print('attr types = ', [elem.attr_type for elem in ga])
    print(GCS.__dict__)
