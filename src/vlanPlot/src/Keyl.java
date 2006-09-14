/*
 * $Id$ 
 *
 * Copyright 2000-2005 Norwegian University of Science and Technology
 * 
 * This file is part of Network Administration Visualized (NAV)
 * 
 * NAV is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * NAV is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with NAV; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 *
 * Authors: Kristian Eide <kreide@gmail.com>
 */

import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;


class Keyl implements KeyListener
{
	Com com;

	public Keyl(Com InCom)
	{
		com = InCom;
	}


	public void keyPressed(KeyEvent evt)
	{}

	public void keyReleased(KeyEvent evt)
	{
		if (evt.getKeyCode() == KeyEvent.VK_ENTER)
		{
			com.d("Trykker 'Enter'", 8);
		}
	}

	public void keyTyped(KeyEvent evt)
	{}
}