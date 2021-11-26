from abc import ABC, abstractmethod
import os
root = 'C:\\Users\\bashkatovaa\\xml_convertor\\files'
def read_html_template():
    upload_folder = root
    html_template = upload_folder[:upload_folder.rindex(os.path.basename(upload_folder))]+'index_template.html'
    html_str = ''
    with open(html_template) as file_handler:
        for line in file_handler:
            html_str+=line
    return html_str
print(read_html_template())
