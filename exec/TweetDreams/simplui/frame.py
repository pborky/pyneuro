# ------------------------------------------------------------------------------
# Copyright (c) 2009 Tristam MacDonald
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of DarkCoda nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------

import pyglet

from shape import Rectangle
from container import Container

class Frame(Container):
	"""Root GUI container"""
	def __init__(self, x, y, w, h, theme, **kwargs):
		"""Create a frame
		
		Keyword arguments:
		children -- list of child elements to be added to this container
		"""
		Container.__init__(self, x, y, w, h, **kwargs)
		
		self.theme = theme
		
		self.names = {}
		self.focus = []
	
	def _get_theme(self):
		return self._theme
	def _set_theme(self, theme):
		self._theme = theme
		self.update_theme(theme)
		self.update_layout()
	theme = property(_get_theme, _set_theme)
	
	def get_element_by_name(self, name):
		return self.names[name]
	
	def on_mouse_press(self, x, y, button, modifiers):
		if len(self.focus) > 0:
			return self.focus[-1].on_mouse_press(x, y, button, modifiers)
		return Container.on_mouse_press(self, x, y, button, modifiers)
	
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		if len(self.focus) > 0:
			return self.focus[-1].on_mouse_drag(x, y, dx, dy, button, modifiers)
		return Container.on_mouse_drag(self, x, y, dx, dy, button, modifiers)
	
	def on_mouse_release(self, x, y, button, modifiers):
		if len(self.focus) > 0:
			return self.focus[-1].on_mouse_release(x, y, button, modifiers)
		return Container.on_mouse_release(self, x, y, button, modifiers)
