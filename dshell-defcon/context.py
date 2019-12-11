#!/usr/bin/env python2

import re
import sys
import struct
import socket
import time


lcontext = 50
rcontext = 30


def enc(s):
    ss = ''
    for i in s:
        if 32 <= ord(i) <= 126 and i != "\\":
            ss += i
        else:
            ss += "\\x" + i.encode('hex')
    return ss

dir2arrow = {
        'c': u"\u2190".encode('utf-8'),
        's': u"\u2192".encode('utf-8'),
        '': ''
        }


def context(fname, offset, len_body):
    ff = open(fname, 'rb')

    ff.seek(-4, 2)
    total_conns = struct.unpack('I', ff.read(4))[0]
    ff.seek(-4 * (1 + total_conns), 2)
    len_conns = list(struct.unpack('I' * total_conns, ff.read(4 * total_conns)))

    current_offset = 0
    for i in len_conns:
        if current_offset <= offset < current_offset + i:
            ff.seek(current_offset, 0)
            len_pkt, cliip, servip, cliport, servport, timestamp = struct.unpack('IIIHHI', ff.read(20))
            cnt_pkt = struct.unpack('I', ff.read(4))[0]
            pkts_id = struct.unpack('I' * cnt_pkt, ff.read(4 * cnt_pkt))
            last_blob = ''
            last_dir = ''
            outputed = -1
            output_data = ""
            for i in xrange(len_pkt):
                direction = ff.read(1)
                len_data = struct.unpack('I', ff.read(4))[0]
                data_begin = ff.tell()
                data = ff.read(len_data)
                data_end = ff.tell()
                if outputed >= 0 and outputed < rcontext:
                    output_data += dir2arrow[direction] + enc(data[:rcontext - outputed])
                    break
                if data_begin <= offset < data_end:
                    output_data = data[offset - data_begin: offset - data_begin + len_body]
                    blobr = data[offset - data_begin + len_body: ]
                    blobl = data[: offset - data_begin]
                    output_data = dir2arrow[direction] + enc(blobl[-lcontext: ] + output_data + blobr[: rcontext])
                    if len(blobl) < lcontext:
                        output_data = dir2arrow[last_dir] + enc(last_blob[-(lcontext - len(blobl)): ]) + output_data
                    outputed = len(blobr)
                last_blob = data
                last_dir = direction
            ff.close()
            return timestamp, servport, cliport, pkts_id, output_data
        current_offset += i

    ff.close()
    return -1, -1, -1, ''

while True:
    try:
        fname, offset, len_body = raw_input().split('\t')
        timestamp, servport, cliport, pkts_id, ret = context(fname, int(offset), int(len_body))
        print "%s\t%d\t%d\t%d\t%d\t%s\t%s" % (fname, int(offset), timestamp, servport, cliport, pkts_id, ret)
        sys.stdout.flush()
    except EOFError:
        break
