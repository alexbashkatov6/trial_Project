from collections import OrderedDict

from cell_object import CellObject
from soi_objects import StationObjectImage, CoordinateSystemSOI
from two_sided_graph import OneComponentTwoSidedPG, PolarNode
from extended_itertools import flatten
from cell_access_functions import find_cell_name, element_cell_by_type


class DependenciesBuildError(Exception):
    pass


class DBNoNameError(DependenciesBuildError):
    pass


class DBExistingNameError(DependenciesBuildError):
    pass


class DBCycleError(DependenciesBuildError):
    pass


class DBIsolatedNodesError(DependenciesBuildError):
    pass


class ImageNameCell(CellObject):
    def __init__(self, name: str):
        self.name = name


class SOIRectifier:
    def __init__(self):
        self.names_soi: OrderedDict[str, StationObjectImage] = OrderedDict()
        self.rect_so: list[str] = []
        self.dg = OneComponentTwoSidedPG()
        self.load_config_mode = False

        self.reset_storages()

    def reset_storages(self):
        self.names_soi: OrderedDict[str, StationObjectImage] = OrderedDict()
        self.rect_so: list[str] = []
        self.dg = OneComponentTwoSidedPG()

    def build_dg(self, images: list[StationObjectImage]) -> None:
        self.reset_storages()
        gcs = images[0]
        gcs_node = self.dg.insert_node()
        gcs_node.append_cell_obj(ImageNameCell(gcs.name))
        self.names_soi[gcs.name] = gcs
        for image in images[1:]:
            cls_name = image.__class__.__name__
            if not hasattr(image, "_name") or (not image.name) or image.name.isspace():
                raise DBNoNameError(cls_name, "", "name", "No-name-object in class")
            obj_name = image.name
            if image.name in self.names_soi:
                raise DBExistingNameError(cls_name, obj_name, "name", "Name {} already exist".format(image.name))
            node = self.dg.insert_node()
            node.append_cell_obj(ImageNameCell(image.name))
            self.names_soi[image.name] = image
        for image in images[1:]:
            cls_name = image.__class__.__name__
            obj_name = image.name
            for attr_name in image.active_attrs:
                if not getattr(image.__class__, attr_name).enum:
                    attr_value: str = getattr(image, "_str_{}".format(attr_name))
                    for name in self.names_soi:
                        if name.isdigit():  # for rail points
                            continue
                        if " " in attr_value:
                            split_names = attr_value.split(" ")
                        else:
                            split_names = [attr_value]
                        for split_name in split_names:
                            if name == split_name:

                                node_self: PolarNode = find_cell_name(self.dg.not_inf_nodes,
                                                                      ImageNameCell, image.name)[1]
                                node_parent: PolarNode = find_cell_name(self.dg.not_inf_nodes,
                                                                        ImageNameCell, name)[1]
                                self.dg.connect_inf_handling(node_self.ni_pu, node_parent.ni_nd)
                    # check cycles and isolated nodes
                    if not self.load_config_mode:
                        self.check_cycle_dg(cls_name, obj_name, attr_name)
        if self.load_config_mode:
            self.check_cycle_dg()

    def check_cycle_dg(self, cls_name: str = "", obj_name: str = "", attr_name: str = ""):
        routes = self.dg.walk(self.dg.inf_pu.ni_nd)
        route_nodes = set()
        for route in routes:
            route_nodes |= set(route.nodes)
        if len(route_nodes) < len(self.dg.nodes):
            nodes = self.dg.nodes - route_nodes
            obj_names: list[str] = [node.cell_objs[0].name for node in nodes]
            if attr_name:
                raise DBIsolatedNodesError(cls_name, obj_name, attr_name, "Isolated nodes was found")
            else:
                # print("len", len(obj_names))
                raise DBIsolatedNodesError("", ", ".join(obj_names), "", "Isolated nodes was found")
        for route_ in routes:
            if route_.is_cycle:
                if attr_name:
                    raise DBCycleError(cls_name, obj_name, attr_name, "Cycle in dependencies was found")
                else:
                    end_node = route_.nodes[-1]
                    obj_name = end_node.cell_objs[0].name
                    raise DBCycleError("", obj_name, "", "Cycle in dependencies was found")

    def rectify_dg(self):
        nodes: list[PolarNode] = list(flatten(self.dg.longest_coverage()))[1:]  # without Global CS
        self.rect_so = [element_cell_by_type(node, ImageNameCell).name for node in nodes]

    def rectification_results(self, images: list[StationObjectImage]) -> tuple[OrderedDict[str, StationObjectImage],
                                                                               list[str]]:
        self.build_dg(images)
        # self.check_cycle_dg()
        self.rectify_dg()
        return self.names_soi, self.rect_so
