def form_message_from_error(e: Exception) -> str:
    cls_name = ""
    obj_name = ""
    attr_name = ""
    message = ""
    assert (len(e.args) == 4) or (len(e.args) == 3)
    if len(e.args) == 4:
        cls_name = e.args[0]
        obj_name = e.args[1]
        attr_name = e.args[2]
        message = e.args[3]
    elif len(e.args) == 3:
        cls_name = e.args[0]
        obj_name = e.args[1]
        message = e.args[2]
    if cls_name.endswith("SOI"):
        cls_name = cls_name.replace("SOI", "")
    result_text = "Error occurred: {}".format(message)
    if cls_name or obj_name or attr_name:
        result_text += " ("
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
        result_text += ")"
    return result_text
