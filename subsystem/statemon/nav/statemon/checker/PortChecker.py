# -*- coding: utf-8 -*-
#
# Copyright (C) 2003,2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import select
import socket

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import  Event

class PortChecker(AbstractChecker):
    def __init__(self,service, **kwargs):
        AbstractChecker.__init__(self,'port', service, port=23, **kwargs)
    def execute(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.getTimeout())
        s.connect(self.getAddress())
        f = s.makefile('r')
        r,w,x = select.select([s],[],[],self.getTimeout())
        if r:
            f.readline()
        status = Event.UP
        txt = 'Alive'
        s.close()

        return status,txt

def getRequiredArgs():
    """
    Returns a list of required arguments
    """
    requiredArgs = []
    return requiredArgs

