from __future__ import annotations

from nv_bounded_string_set_class import bounded_string_set


class Association:
    pass


class NodeAssociation(Association):
    pass


class LinkAssociation(Association):
    pass


class MoveAssociation(Association):
    pass


AttribNodeAssociation = bounded_string_set('AttribNodeAssociation', [['attrib_node']], NodeAssociation)
AttribMoveAssociation = bounded_string_set('AttribMoveAssociation', [['splitter_value_move']], MoveAssociation)
TreeNodeAssociation = bounded_string_set('TreeNodeAssociation', [['class_object_node']], NodeAssociation)
DependenceNodeAssociation = bounded_string_set('DependenceNodeAssociation', [['object_node']], NodeAssociation)
FieldNodeAssociation = bounded_string_set('FieldNodeAssociation', [['railway_point_node'],
                                                                   ['light_node'],
                                                                   ['crossroad_intersection_node'],
                                                                   ['worker_node'],
                                                                   ['ab_border_node'],
                                                                   ['pab_border_node'],
                                                                   ['align_border_node'],
                                                                   ['isolation_zone_node'],
                                                                   ['station_zone_node'],
                                                                   ['velocity_zone_node']], NodeAssociation)
FieldLinkAssociation = bounded_string_set('FieldLinkAssociation', [['isolation_zone_link'],
                                                                   ['station_zone_link'],
                                                                   ['velocity_zone_link']], LinkAssociation)
FieldMoveAssociation = bounded_string_set('FieldMoveAssociation', [['railway_point_position_move']], MoveAssociation)

if __name__ == '__main__':
    print(AttribNodeAssociation.__bases__)
    print(issubclass(AttribNodeAssociation, Association))
    print(issubclass(AttribNodeAssociation, NodeAssociation))
    print(issubclass(AttribNodeAssociation, LinkAssociation))
