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
from pyglet.gl import *

from shape import Rectangle

from rect import Rect

class Widget(object):
	"""Base class for all GUI elements"""
	def __init__(self, x, y, w, h, name):
		'''Initialise a Widget
		
		Keyword arguments:
		name -- unique widget identifier
		'''
		self._x, self._y, self._w, self._h = x, y, w, h
		self._gx, self._gy = self._x, self._y
		
		self._name = name
		self.parent = None
		self._theme = None
		
		self.elements = {}
	
	def _get_x(self):
		return self._x
	def _set_x(self, x):
		self._x = x
		self.update_layout()
	x = property(_get_x, _set_x)
	
	def _get_y(self):
		return self._y
	def _set_y(self, y):
		self._y = y
		self.update_layout()
	y = property(_get_y, _set_y)

	def _get_w(self):
		return self._w
	def _set_w(self, w):
		self._w = w
		self.update_layout()
	w = property(_get_w, _set_w)
	
	def _get_h(self):
		return self._h
	def _set_h(self, h):
		self._h = h
		self.update_layout()
	h = property(_get_h, _set_h)
	
	def _get_name(self):
		return self._name
	def _set_name(self, name):
		_name = self._name
		self._name = name
		self.update_names(_name)
	name = property(_get_name, _set_name)
	
	def _get_theme(self):
		return self._theme
	theme = property(_get_theme)
	
	def remove_from_parent(self):
		self.parent.remove(self)
	
	def find_root(self):
		root = self
		
		while root.parent:
			root = root.parent
		
		return root
	
	def update_names(self, oldname=None):
		from frame import Frame
		r = self.find_root()
		if isinstance(r, Frame):
			if oldname:
				del r.names[oldname]
			if self.name:
				r.names[self.name] = self
	
	def remove_names(self):
		from frame import Frame
		r = self.find_root()
		if isinstance(r, Frame):
			if self.name:
				del r.names[self.name]
	
	def update_global_coords(self):
		if self.parent:
			self._gx, self._gy = self.parent._gx + self._x, self.parent._gy + self._y
		else:
			self._gx, self._gy = self._x, self._y
	
	def update_layout(self):
		pass
	
	def update_theme(self, theme):
		self._theme = theme
	
	def on_mouse_press(self, x, y, button, modifiers):
		pass
	
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		pass
	
	def on_mouse_release(self, x, y, button, modifiers):
		pass
	
	def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
		pass
	
	def on_key_press(self, symbol, modifiers):
		pass
	
	def on_text(self, text):
		pass
	
	def on_text_motion(self, motion, select=False):
		pass
	
	def hit_test(self, x, y):
		return (x >= self._gx and x <= self._gx + self.w) and (y >= self._gy and y <= self._gy + self.h)
	
	def bounds(self):
		return Rect(self._gx, self._gy, self.w, self.h)
	
	def draw(self, clip=None):
		self.update_global_coords()
		
		glTranslatef(self.x, self.y, 0)
		
		for k, e in self.elements.iteritems():
			e.draw()
		
		glTranslatef(-self.x, -self.y, 0)
