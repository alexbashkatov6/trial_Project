from collections import OrderedDict
import os
import xml.dom.minidom
import xml.etree.ElementTree as ElTr

from rail_route import RailRoute


def form_route_element(signal_element_, route_: RailRoute) -> ElTr.Element:
    if route_.route_type == "PpoTrainRoute":
        route_element = ElTr.SubElement(signal_element_, 'TrRoute')
    else:
        route_element = ElTr.SubElement(signal_element_, 'ShRoute')
    route_element.set("Tag", route_.route_tag)
    route_element.set("Type", route_.route_type)
    route_element.set("Id", route_.id)
    if route_.route_pointer_value:
        route_element.set("ValueRoutePointer", route_.route_pointer_value)
    trace_element = ElTr.SubElement(route_element, 'Trace')
    trace_element.set("Start", route_.trace_begin)
    trace_element.set("OnCoursePoints", route_.trace_points)
    trace_element.set("Finish", route_.trace_end)
    if route_.trace_variants:
        trace_element.set("Variants", route_.trace_variants)
    selectors_element = ElTr.SubElement(route_element, 'OperatorSelectors')
    selectors_element.set("Ends", route_.end_selectors)
    if route_.route_type == "PpoTrainRoute":
        dependence_element = ElTr.SubElement(route_element, 'SignalingDependence')
        dependence_element.set("Dark", route_.next_dark)
        dependence_element.set("Stop", route_.next_stop)
        dependence_element.set("OnMain", route_.next_on_main)
        dependence_element.set("OnMainGreen", route_.next_on_main_green)
        dependence_element.set("OnSide", route_.next_on_side)
        dependence_element.set("OnMainALSO", route_.next_also_on_main)
        dependence_element.set("OnMainGrALSO", route_.next_also_on_main_green)
        dependence_element.set("OnSideALSO", route_.next_also_on_side)
        if route_.route_points_before_route:
            before_route_element = ElTr.SubElement(route_element, 'PointsAnDTrack')
            before_route_element.set("Points", route_.route_points_before_route)
    for cn_ in route_.crossroad_notifications:
        if cn_.crossroad_id is None:
            continue
        cn_element = ElTr.SubElement(route_element, 'CrossroadNotification')
        cn_element.set("RailCrossing", cn_.crossroad_id)
        cn_element.set("DelayOpenSignal", cn_.crossroad_delay_open)
        if route_.signal_type == "PpoTrainSignal":
            cn_element.set("DelayStartNotification", cn_.crossroad_delay_start_notif)
            cn_element.set("StartNotification", cn_.crsrd_start_notif)
        if not (cn_.crsrd_notif_point is None):
            cn_element.set("NotificationPoint", cn_.crsrd_notif_point)
        if not (cn_.crsrd_before_route_points is None):
            cn_element.set("Point", cn_.crsrd_before_route_points)
    return route_element


def form_rail_routes_xml(train_light_routes_dict: OrderedDict[str, tuple[list[RailRoute], list[RailRoute]]],
                         shunting_light_routes_dict: OrderedDict[str, list[RailRoute]],
                         sub_folder: str, train_routes_file_name: str, shunting_routes_file_name: str):
    train_routes_file_full_name = os.path.join(os.getcwd(), sub_folder, train_routes_file_name)
    shunting_routes_file_full_name = os.path.join(os.getcwd(), sub_folder, shunting_routes_file_name)

    train_route_element = ElTr.Element('Routes')
    shunting_route_element = ElTr.Element('Routes')

    for light_name in train_light_routes_dict:
        train_routes, shunting_routes = train_light_routes_dict[light_name]
        signal_element = ElTr.SubElement(train_route_element, 'TrainSignal')
        signal_element.set("Tag", light_name)
        signal_element.set("Type", "PpoTrainSignal")
        for route in train_routes:
            form_route_element(signal_element, route)
        for route in shunting_routes:
            form_route_element(signal_element, route)

    for light_name in shunting_light_routes_dict:
        shunting_routes = shunting_light_routes_dict[light_name]
        signal_element = ElTr.SubElement(shunting_route_element, 'ShuntingSignal')
        signal_element.set("Tag", light_name)
        signal_element.set("Type", "PpoShuntingSignal")
        for route in shunting_routes:
            form_route_element(signal_element, route)

    xml_str_train = xml.dom.minidom.parseString(ElTr.tostring(train_route_element)).toprettyxml()
    with open(train_routes_file_full_name, 'w', encoding='utf-8') as out:
        out.write(xml_str_train)
    xml_str_shunt = xml.dom.minidom.parseString(ElTr.tostring(shunting_route_element)).toprettyxml()
    with open(shunting_routes_file_full_name, 'w', encoding='utf-8') as out:
        out.write(xml_str_shunt)
