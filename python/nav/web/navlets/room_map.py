#
# Copyright (C) 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Room map navlet"""

from nav.web.navlets import Navlet


class RoomMapNavlet(Navlet):
    """View class for the room map navlet"""
    title = 'Room map'
    description = 'Display a map marking the location of rooms'
    event = 'room-map'

    def get_template_basename(self):
        return 'room_map'