import inspect
from nv_string_set_class import BoundedStringSet
from nv_polar_graph import BasePolarGraph, PolarNode, PGLink, PGMove, End, PGRoute  #
from nv_typing import *


# class AttributeControl:
#     def __init__(self):
#         self._attributes_activity: dict[str, bool] = {}
#         self._stable_states: Optional[BoundedStringSet] = None

class BSSDependency(BoundedStringSet):

    def __init__(self, str_val: str) -> None:
        super().__init__([['dependent'], ['independent']], str_val)


class CsGtDescriptor:
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if not hasattr(instance, '_graph_template'):
            instance._graph_template = BasePolarGraph()
            instance._graph_template.associations.register_association_types(PolarNode,
                                                                             {'attr_tuple': "tuple['str', 'Any']"})
            instance._graph_template.associations.register_association_types(PGMove,
                                                                             {'splitter_value': 'str'})
            g_t = instance._graph_template

            node_rel_cs, _, _ = g_t.insert_node_single_link()
            node_rel_cs.associations['attr_tuple'] = ('Cs_relative_to', CoordSystem)
            node_check_dependence, _, _ = g_t.insert_node_single_link(node_rel_cs.ni_nd)
            node_check_dependence.associations['attr_tuple'] = ('Dependence', BSSDependency)
            node_x, link_up_x, _ = g_t.insert_node_single_link(node_check_dependence.ni_nd)
            node_x.associations['attr_tuple'] = ('x', int)
            move_to_x = node_x.ni_pu.get_move(link_up_x)
            move_to_x.associations['splitter_value'] = 'dependent'
            node_y, _, _ = g_t.insert_node_single_link(node_x.ni_nd)
            node_y.associations['attr_tuple'] = ('y', int)
            node_alpha, link_up_alpha, _ = g_t.insert_node_single_link(node_check_dependence.ni_nd)
            node_alpha.associations['attr_tuple'] = ('alpha', int)
            move_to_alpha = node_alpha.ni_pu.get_move(link_up_alpha)
            move_to_alpha.associations['splitter_value'] = 'independent'
            node_con_polarity, _, _ = g_t.insert_node_single_link(node_alpha.ni_nd)
            node_con_polarity.associations['attr_tuple'] = ('connection_polarity', End)

            route_from_to_: PGRoute = g_t.find_single_route(node_rel_cs, node_con_polarity)
            route_result_ = g_t.associations.extract_route_content({PolarNode: 'attr_tuple', PGMove: 'splitter_value'},
                                                                   route_from_to_, get_as_strings=False)
            print(route_result_)
        return 'all ok'

    def __set__(self, instance, value):
        raise NotImplementedError('{} setter not implemented'.format(self.__class__.__name__))


class CoordSystem:
    graph_template = CsGtDescriptor()

    def __init__(self):
        pass
        # attr_types = {'x': int, 'y': int, 'alpha': int, 'co_X': int, 'co_Y': int}
        
    def switch_splitter(self):
        pass


# , x: int = None, y: int = None, alpha: int = None, co_X: int = None, co_Y: int = None
#         self.x = x
#         self.y = y
#         self.alpha = alpha
#         self.co_X = co_X
#         self.co_Y = co_Y

GCS = CoordSystem()


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
    # arg_spec_DB = inspect.getfullargspec(DependentBasis.__init__)
    arg_spec_CS = inspect.getfullargspec(CoordSystem.__init__)
    # print('arg_spec_DB', arg_spec_DB)
    print('arg_spec_CS', arg_spec_CS)
    # print('mro', DependentBasis.mro())
    # print('annotations', DependentBasis.__init__.__annotations__)
    # print('attributes', inspect.getattr_static(GCS, 'x'))
    print(GCS.graph_template)
