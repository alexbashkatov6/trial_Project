from __future__ import annotations
import re


class CrossroadNotification:
    def __init__(self, cn_route: RailRoute, num: int):
        self.route = cn_route
        self.num = num
        self._crossroad_id = None
        self._crossroad_delay_open = None
        self._crossroad_delay_start_notif = None
        self._crossroad_start_notif = None
        self._crossroad_notif_point = None  # not required
        self._crossroad_before_route_points = None  # not required

    @property
    def crossroad_id(self):
        return self._crossroad_id

    @crossroad_id.setter
    def crossroad_id(self, value):
        if (not value) or value.isspace():
            return
        self._crossroad_id = value

    @property
    def crossroad_delay_open(self):
        return self._crossroad_delay_open

    @crossroad_delay_open.setter
    def crossroad_delay_open(self, value):
        if (not value) or value.isspace():
            return
        self.route.int_checker(value, 'crossroad_delay_open_{}'.format(self.num), 0)
        self._crossroad_delay_open = value

    @property
    def crossroad_delay_start_notif(self):
        return self._crossroad_delay_start_notif

    @crossroad_delay_start_notif.setter
    def crossroad_delay_start_notif(self, value):
        if (not value) or value.isspace():
            return
        self.route.int_checker(value, 'crossroad_delay_start_notif_{}'.format(self.num), 0)
        self._crossroad_delay_start_notif = value

    @property
    def crsrd_start_notif(self):
        return self._crossroad_start_notif

    @crsrd_start_notif.setter
    def crsrd_start_notif(self, value):
        if (not value) or value.isspace():
            return
        # ! implement here check start_notif in list of available values
        self._crossroad_start_notif = value

    @property
    def crsrd_notif_point(self):
        return self._crossroad_notif_point

    @crsrd_notif_point.setter
    def crsrd_notif_point(self, value):
        if (not value) or value.isspace():
            return
        self.route.int_checker(value, 'crossroad_notif_point_{}'.format(self.num))
        self._crossroad_notif_point = value

    @property
    def crsrd_before_route_points(self):
        return self._crossroad_before_route_points

    @crsrd_before_route_points.setter
    def crsrd_before_route_points(self, value):
        if (not value) or value.isspace():
            return
        self.route.route_points_checker(value, 'crossroad_before_route_points_{}'.format(self.num))
        self._crossroad_before_route_points = value

    def check_required_params(self):
        if self.route.signal_type == "PpoTrainSignal":
            if self.crossroad_id is None:
                assert (self.crossroad_delay_open is None) and (self.crossroad_delay_start_notif is None) and \
                       (self.crsrd_start_notif is None) and (self.crsrd_notif_point is None) and \
                       (self.crsrd_before_route_points is None), \
                       "Id expected for Crossroad_{} in line {}".format(self.num, self.route.id)
            else:
                assert not (self.crossroad_delay_open is None), "Expected delay_open for Crossroad_{} in line {}".\
                    format(self.num, self.route.id)
                assert not (self.crossroad_delay_start_notif is None), \
                    "Expected delay_start_notif for Crossroad_{} in line {}".format(self.num, self.route.id)
                assert not (self.crsrd_start_notif is None), "Expected start_notif for Crossroad_{} in line {}".\
                    format(self.num, self.route.id)
        elif self.route.signal_type == "PpoShuntingSignal":
            if self.crossroad_id is None:
                assert (self.crossroad_delay_open is None) and (self.crossroad_delay_start_notif is None) and \
                       (self.crsrd_start_notif is None) and (self.crsrd_notif_point is None) and \
                       (self.crsrd_before_route_points is None), \
                       "Id expected for Crossroad_{} in line {}".format(self.num, self.route.id)
            else:
                assert not (self.crossroad_delay_open is None), "Expected delay_open for Crossroad_{} in line {}".\
                    format(self.num, self.route.id)
        else:
            assert False, "Signal type {} not exists".format(self.route.signal_type)


class RailRoute:
    def __init__(self, id_):
        self.id = str(id_)
        self.route_tag = None
        self._route_type = None
        self._signal_tag = None
        self._signal_type = None
        self._route_pointer_value = None
        self._trace_begin = None
        self.trace_points = ""
        self._trace_variants = None
        self._trace_end = None
        self._end_selectors = None
        self._route_points_before_route = None
        self.next_dark = "K"
        self.next_stop = "K"
        self.next_on_main = "K"
        self.next_on_main_green = "K"
        self.next_on_side = "K"
        self.next_also_on_main = "K"
        self.next_also_on_main_green = "K"
        self.next_also_on_side = "K"
        self.crossroad_notifications: list[CrossroadNotification] = []

    def signal_light_checker(self, value, column_name):
        if self.route_type == "PpoShuntingRoute":
            return
        assert value in ["K", "ZH", "Z", "ZHM_Z", "ZHM_ZH", "ZM", "DZH", "DZHM"], \
            "Not supported light value {} in line {} column {}".format(value, self.id, column_name)

    def int_checker(self, value, column_name, min_possible_value: int = 1):
        if value == "":
            return
        assert int(value) >= min_possible_value, "Value should be int >= {}, given value is {} in line {} column {}" \
            .format(min_possible_value, value, self.id, column_name)

    def route_points_checker(self, value, column_name):
        points_found = re.findall(r"[+-]\d{1,3}S?[OB]?", value)
        val_copy = value
        for point in points_found:
            val_copy = val_copy.replace(point, "", 1)
        assert (not val_copy) or val_copy.isspace(), \
            "Pointers list {} is not valid in line {} column {}".format(value, self.id, column_name)

    @property
    def route_type(self):
        return self._route_type

    @route_type.setter
    def route_type(self, value):
        assert value in ["PpoTrainRoute", "PpoShuntingRoute"], "Not valid route type {} in line {}" \
            .format(value, self.id)
        self._route_type = value

    @property
    def signal_tag(self):
        return self._signal_tag

    @signal_tag.setter
    def signal_tag(self, value):
        # ! implement here check signal in list of available values
        self._signal_tag = value

    @property
    def signal_type(self):
        return self._signal_type

    @signal_type.setter
    def signal_type(self, value):
        assert value in ["PpoTrainSignal", "PpoShuntingSignal"], "Not valid signal type {} in line {}" \
            .format(value, self.id)
        self._signal_type = value

    @property
    def route_pointer_value(self):
        return self._route_pointer_value

    @route_pointer_value.setter
    def route_pointer_value(self, value):
        self.int_checker(value, 'route_pointer_value')
        self._route_pointer_value = value

    @property
    def trace_begin(self):
        return self._trace_begin

    @trace_begin.setter
    def trace_begin(self, value):
        # ! implement here check trace_begin in list of available values
        self._trace_begin = value

    @property
    def trace_variants(self):
        return self._trace_variants

    @trace_variants.setter
    def trace_variants(self, value):
        if value == "":
            self._trace_variants = None
            return
        # ! implement here check trace_variants in list of available values
        self._trace_variants = value

    @property
    def trace_points(self):
        return self._trace_points

    @trace_points.setter
    def trace_points(self, value: str):
        self.route_points_checker(value, 'trace_points')
        if value:
            value += " "
        self._trace_points = value

    @property
    def trace_end(self):
        return self._trace_end

    @trace_end.setter
    def trace_end(self, value):
        # ! implement here check trace_end in list of available values
        self._trace_end = value

    @property
    def end_selectors(self):
        return self._end_selectors

    @end_selectors.setter
    def end_selectors(self, value):
        # ! implement here check end_selectors in list of available values
        self._end_selectors = value

    @property
    def route_points_before_route(self):
        return self._route_points_before_route

    @route_points_before_route.setter
    def route_points_before_route(self, value):
        if value == "":
            self._route_points_before_route = None
            return
        # ! implement here check route_points_before_route in list of available values
        self._route_points_before_route = value + " "

    @property
    def next_dark(self):
        return self._next_dark

    @next_dark.setter
    def next_dark(self, value):
        self.signal_light_checker(value, "next_dark")
        self._next_dark = value

    @property
    def next_stop(self):
        return self._next_stop

    @next_stop.setter
    def next_stop(self, value):
        self.signal_light_checker(value, "next_stop")
        self._next_stop = value

    @property
    def next_on_main(self):
        return self._next_on_main

    @next_on_main.setter
    def next_on_main(self, value):
        self.signal_light_checker(value, "next_on_main")
        self._next_on_main = value

    @property
    def next_on_main_green(self):
        return self._next_on_main_green

    @next_on_main_green.setter
    def next_on_main_green(self, value):
        self.signal_light_checker(value, "next_on_main_green")
        self._next_on_main_green = value

    @property
    def next_on_side(self):
        return self._next_on_side

    @next_on_side.setter
    def next_on_side(self, value):
        self.signal_light_checker(value, "next_on_side")
        self._next_on_side = value

    @property
    def next_also_on_main(self):
        return self._next_also_on_main

    @next_also_on_main.setter
    def next_also_on_main(self, value):
        self.signal_light_checker(value, "next_also_on_main")
        self._next_also_on_main = value

    @property
    def next_also_on_main_green(self):
        return self._next_also_on_main_green

    @next_also_on_main_green.setter
    def next_also_on_main_green(self, value):
        self.signal_light_checker(value, "next_also_on_main_green")
        self._next_also_on_main_green = value

    @property
    def next_also_on_side(self):
        return self._next_also_on_side

    @next_also_on_side.setter
    def next_also_on_side(self, value):
        self.signal_light_checker(value, "next_also_on_side")
        self._next_also_on_side = value

    def count_crossroad_notification(self):
        return len(self.crossroad_notifications)

    def add_crossroad_notification(self):
        cn = CrossroadNotification(self, self.count_crossroad_notification() + 1)
        self.crossroad_notifications.append(cn)
