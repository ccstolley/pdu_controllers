"""
Module for controlling and checking status of a Server Technologies
CW-2H1-C20 PDU.
"""

import httplib
import base64
from lxml.html.clean import clean_html
from lxml.html import fromstring as parse_html
from pysnmp.entity.rfc3413.oneliner import cmdgen


PDU_PWD = base64.b64encode('admn:admn')
PDU_HOST = 'pdu1.colinstolley.com'
PDU_PORT = '80'


def clean_chars(s):
    return s.encode('ascii', 'ignore').strip()


def parse_value(tree, path):
    """
    Parses text from a path using tree.
    """
    v = tree.xpath(path)[0].text
    return clean_chars(v)


def dispatch_request(url, request='', headers={}):
    """
    Dispatches an HTTP request to PDU with proper auth headers and cookie.
    Returns status and response.
    """
    host = PDU_HOST
    port = PDU_PORT
    if request:
        method = 'POST'
    else:
        method = 'GET'
    cnx = httplib.HTTPConnection(host, port)
    cnx.putrequest(method, url)
    cnx.putheader("Cookie", "C0=03000000000000000000000000000000")
    cnx.putheader("Authorization", "Basic %s" % PDU_PWD)
    cnx.putheader("Content-length", len(request.encode('utf-8')))
    cnx.endheaders()
    cnx.send(request.encode('utf-8'))
    resp = cnx.getresponse()
    return (resp.status, resp.read())


def outlet_off(number):
    """
    Turns off specified outlet.
    """
    control_outlet(number, 2)


def outlet_on(number):
    """
    Turns on specified outlet.
    """
    control_outlet(number, 1)


def control_outlet(outlet_number, action_number):
    """
    General purpose function for controlling outlets. action_number
    should be replaced with a set of defined constants.
    """
    url = '/Forms/outctrl_1'
    outlets = [0, 0]
    outlets[outlet_number-1] = action_number
    request = 'ControlAction%%3F1=%d&ControlAction%%3F2=%d' % tuple(outlets)
    hdrs = {"Cookie": "C0=03000000000000000000000000000000"}
    dispatch_request(url, request, hdrs)


def get_sensor_status():
    """
    Parses PDU status HTML and returns sensor readings.
    """
    url = '/sensors.html'
    res = dispatch_request(url)
    if res[0] != 200:
        raise Exception('Failed to get status')
    data = res[1]
    data = clean_html(data)
    tree = parse_html(data)
    id1 = parse_value(tree, '/html/body/div/div/table[2]/tr[5]/td[2]/font')
    id2 = parse_value(tree, '/html/body/div/div/table[2]/tr[6]/td[2]/font')
    lab1 = parse_value(tree, '/html/body/div/div/table[2]/tr[5]/td[3]/font/b')
    lab2 = parse_value(tree, '/html/body/div/div/table[2]/tr[6]/td[3]/font/b')
    temp1 = parse_value(tree,
                       '/html/body/div/div/table[2]/tr[5]/td[4]/font/b/font/b')
    temp2 = parse_value(tree,
                       '/html/body/div/div/table[2]/tr[6]/td[4]/font/b/font/b')
    hum1 = parse_value(tree,
                       '/html/body/div/div/table[2]/tr[5]/td[5]/font/b/font/b')
    hum2 = parse_value(tree,
                       '/html/body/div/div/table[2]/tr[6]/td[5]/font/b/font/b')
    hum1 = hum1.replace(' %', '')
    hum2 = hum2.replace(' %', '')
    temp1 = temp1.replace(' Deg. F', '')
    temp2 = temp2.replace(' Deg. F', '')
    res = [{'id': id1, 'label': lab1, 'temp': temp1, 'hum': hum1},
           {'id': id2, 'label': lab2, 'temp': temp2, 'hum': hum2}, ]
    return res


def status_snmp(host='pdu1'):
    (errorIndication, errorStatus, errorIndex, varBinds) = r
    r = cmdgen.CommandGenerator().getCmd(
      cmdgen.CommunityData('test-agent', 'public'),
      cmdgen.UdpTransportTarget(('pdu1', 161)),
      # Outlet 1
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 3, 1, 2, 1, 1, 1),
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 3, 1, 3, 1, 1, 1),
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 3, 1, 5, 1, 1, 1),
      # Outlet 2
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 3, 1, 2, 1, 1, 2),
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 3, 1, 3, 1, 1, 2),
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 3, 1, 5, 1, 1, 2),
      # Sensor 1
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 5, 1, 2, 1, 1),
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 5, 1, 3, 1, 1),
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 5, 1, 6, 1, 1),
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 5, 1, 10, 1, 1),
      # Sensor 2
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 5, 1, 2, 1, 2),
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 5, 1, 3, 1, 2),
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 5, 1, 6, 1, 2),
      (1, 3, 6, 1, 4, 1, 1718, 3, 2, 5, 1, 10, 1, 2), )

    v = [str(x[1]) for x in varBinds]

    res = {'outlets': [{'id': v[0], 'label': v[1], 'status': v[2]},
                       {'id': v[3], 'label': v[4], 'status': v[5]}, ],
           'sensors': [{'id': v[6], 'label': v[7],
                        'temp': float(v[8])/10.0, 'hum': v[9]},
                       {'id': v[10],
                        'label': v[11],
                        'temp': float(v[12]) / 10.0, 'hum': v[13]}, ]}
    return res


def get_outlet_status():
    """
    Parses PDU status HTML and returns outlet statuses.
    """
    url = '/outctrl.html'
    res = dispatch_request(url)
    if res[0] != 200:
        raise Exception('Failed to get status')
    data = res[1]
    data = clean_html(data)
    tree = parse_html(data)
    id1 = parse_value(tree, '/html/body/div/div/table[2]/tr[6]/td[2]/font')
    id2 = parse_value(tree, '/html/body/div/div/table[2]/tr[7]/td[2]/font')
    lab1 = parse_value(tree, '/html/body/div/div/table[2]/tr[6]/td[3]/font/b')
    lab2 = parse_value(tree, '/html/body/div/div/table[2]/tr[7]/td[3]/font/b')
    stat1 = parse_value(tree, '/html/body/div/div/table[2]/tr[6]/td[5]/font')
    stat2 = parse_value(tree, '/html/body/div/div/table[2]/tr[7]/td[5]/font')
    return [{'id': id1, 'label': lab1, 'status': stat1},
            {'id': id2, 'label': lab2, 'status': stat2}, ]


def get_status(use_snmp=False):
    """
    Returns a dictionary containing all outlet and sensor statues.
    """
    if use_snmp:
        return status_snmp()
    else:
        stat = {}
        stat['outlets'] = get_outlet_status()
        stat['sensors'] = get_sensor_status()
        return stat


def safe_outlet_off(number):
    """
    Switches outlet off and checks status to confirm the switch is
    in the proper state.
    """
    outlet_off(number)
    s = get_outlet_status()
    if s[number-1]['status'] != 'Off':
        raise Exception("Failed to switch outlet %d to ON" % number)


def safe_outlet_on(number):
    """
    Switches outlet on and checks status to confirm the switch is
    in the proper state.
    """
    outlet_on(number)
    s = get_outlet_status()
    if s[number-1]['status'] != 'On':
        raise Exception("Failed to switch outlet %d to ON" % number)


t = ''
if __name__ == '__main__':
    import sys
    import os
    cmd = sys.argv[1]

    if cmd == 'on':
        num = int(sys.argv[2])
        safe_outlet_on(num)
    elif cmd == 'off':
        num = int(sys.argv[2])
        safe_outlet_off(num)
    elif cmd == 'status':
        use_snmp = False
        if len(sys.argv) > 2 and sys.argv[2] == '-s':
            use_snmp = True
        t = get_status(use_snmp=use_snmp)
        for out in t['outlets']:
            print "%s: %s" % (out['label'], out['status'])
        for sen in t['sensors']:
            if sen['temp'] == 'Not Found':
                pass
            else:
                print "%s: %s deg F (%s %%)" % (sen['label'],
                                                sen['temp'],
                                                sen['hum'])
    else:
        print ("usage: %s [status] [on|off <num>]" %
               os.path.basename(sys.argv[0]))

        sys.exit(1)
