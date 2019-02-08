# -*- coding: utf-8 -*-
import re

ui_re_params = {
    'remote_addr': r'\S+',
    'remote_user': r'\S+',
    'http_x_real_ip': r'\S+',
    'time_local': r'\d{2}\/\w{3}\/\d{4}:\d{2}:\d{2}:\d{2} \S\d{4}',
    'request': r'\w{3,7} (?P<url>\S+) \S+',
    'status': r'\d{3}',
    'body_bytes_sent': r'\d+',
    'http_referer': r'.*(?=")',
    'http_user_agent': r'.*(?=")',
    'http_x_forwarded_for': r'.*(?=")',
    'http_X_REQUEST_ID': r'.*(?=")',
    'http_X_RB_USER': r'.*(?=")',
    'request_time': r'(?P<request_time>\d+\.\d+)'
}

ui_log_string_re = re.compile(
    r'{remote_addr} {remote_user}  {http_x_real_ip} \[{time_local}\] "{request}" '
    r'{status} {body_bytes_sent} "{http_referer}" '
    r'"{http_user_agent}" "{http_x_forwarded_for}" "{http_X_REQUEST_ID}" "{http_X_RB_USER}" '
    r'{request_time}'.format(**ui_re_params)
)

ui_log_file_name_re = r'nginx-access-ui.log-(?P<date>\d{8})(?P<extension>\.gz|$)'
