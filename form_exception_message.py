from typing import Union

from attribute_data import AttributeData

# def form_message_from_error(e: Exception) -> str:
#     cls_name = ""
#     obj_name = ""
#     attr_name = ""
#     message = ""
#     assert (len(e.args) == 4) or (len(e.args) == 3)
#     if len(e.args) == 4:
#         cls_name = e.args[0]
#         obj_name = e.args[1]
#         attr_name = e.args[2]
#         message = e.args[3]
#     elif len(e.args) == 3:
#         cls_name = e.args[0]
#         obj_name = e.args[1]
#         message = e.args[2]
#     if cls_name.endswith("SOI"):
#         cls_name = cls_name.replace("SOI", "")
#     result_text = "Error occurred: {}".format(message)
#     if cls_name or obj_name or attr_name:
#         result_text += " ("
#         if cls_name:
#             result_text += "class: {}".format(cls_name)
#         if obj_name:
#             if cls_name:
#                 result_text += "; "
#             result_text += "object: {}".format(obj_name)
#         if attr_name:
#             if cls_name or obj_name:
#                 result_text += "; "
#             result_text += "attribute: {}".format(attr_name)
#         result_text += ")"
#     return result_text

def form_message_from_error(e: Exception) -> str:
    message = e.args[0]
    attr_data: Union[AttributeData, list[AttributeData]] = e.args[1]
    result_text = "Error occurred: {}".format(message)
    result_text += "\nObjects:"
    if not isinstance(attr_data, list):
        attr_data = [attr_data]
    for ad in attr_data:
        cls_name = ad.cls_name
        obj_name = ad.obj_name
        attr_name = ad.attr_name
        index = ad.index
        result_text += "\n ("
        if cls_name:
            result_text += "class: {}".format(cls_name)
        if obj_name:
            if cls_name:
                result_text += "; "
            result_text += "object: {}".format(obj_name)
        if attr_name:
            if cls_name or obj_name:
                result_text += "; "
            result_text += "attribute: {}".format(attr_name)
        if index != -1:
            if cls_name or obj_name or attr_name:
                result_text += "; "
            result_text += "index: {}".format(index)
        result_text += ")"
    return result_text
