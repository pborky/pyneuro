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

from widget import Widget

from rect import Rect

class Container(Widget):
	"""Base class for all GUI containers, also usable by itself"""
	def __init__(self, x, y, w, h, **kwargs):
		"""Create a container
		
		Keyword arguments:
		name -- unique widget identifier
		children -- list of child elements to be added to this container
		"""
		Widget.__init__(self, x, y, w, h, kwargs.get('name'))
		
		self.children = []
		
		children = kwargs.get('children', [])
		for c in children:
			self.add(c)
	
	def update_global_coords(self):
		Widget.update_global_coords(self)
		
		for c in self.children:
			c.update_global_coords()
	
	def update_layout(self):
		Widget.update_layout(self)
		
		for c in self.children:
			c.update_layout()
	
	def update_theme(self, theme):
		Widget.update_theme(self, theme)
		
		for c in self.children:
			c.update_theme(theme)
	
	def update_names(self, oldname=None):
		Widget.update_names(self, oldname)
		
		for c in self.children:
			c.update_names(oldname)
	
	def remove_names(self):
		Widget.remove_names(self)
		
		for c in self.children:
			c.remove_names()
	
	def add(self, child):
		self.children.append(child)
		child.parent = self
		
		child.update_theme(self.theme)
		self.find_root().update_layout()
		
		child.update_names()
	
	def remove(self, child):
		child.remove_names()
		
		self.children.remove(child)
		child.parent = None
		
		self.find_root().update_layout()
	
	def on_mouse_press(self, x, y, button, modifiers):
		Widget.on_mouse_press(self, x, y, button, modifiers)
		
		r = self.clip_rect()
		for c in self.children:
			if r.intersect(c.bounds()).hit_test(x, y):
				c.on_mouse_press(x, y, button, modifiers)
	
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		Widget.on_mouse_drag(self, x, y, dx, dy, button, modifiers)
		
		for c in self.children:
			c.on_mouse_drag(x, y, dx, dy, button, modifiers)
	
	def on_mouse_release(self, x, y, button, modifiers):
		Widget.on_mouse_release(self, x, y, button, modifiers)
		
		r = self.clip_rect()
		for c in self.children:
			if r.intersect(c.bounds()).hit_test(x, y):
				c.on_mouse_release(x, y, button, modifiers)
	
	def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
		Widget.on_mouse_scroll(self, x, y, scroll_x, scroll_y)
		
		r = self.clip_rect()
		for c in self.children:
			if r.intersect(c.bounds()).hit_test(x, y):
				c.on_mouse_scroll(x, y, scroll_x, scroll_y)
	
	def on_key_press(self, symbol, modifiers):
		Widget.on_key_press(self, symbol, modifiers)
		
		for c in self.children:
			c.on_key_press(symbol, modifiers)
	
	def on_text(self, text):
		Widget.on_text(self, text)
		
		for c in self.children:
			c.on_text(text)
	
	def on_text_motion(self, motion, select=False):
		Widget.on_text_motion(self, motion, select)
		
		for c in self.children:
			c.on_text_motion(motion, select)
	
	def clip_rect(self):
		return Rect(self._gx, self._gy, self.w, self.h)
	
	def draw(self, clip=None):
		self.update_global_coords()
		
		glTranslatef(self.x, self.y, 0)
		
		for k, e in self.elements.iteritems():
			e.draw()
		
		r = self.clip_rect()
		if clip:
			r = r.intersect(clip)
		
		for c in self.children:
			glEnable(GL_SCISSOR_TEST)
			glScissor(*r)
			c.draw(r)
			glDisable(GL_SCISSOR_TEST)
		
		glTranslatef(-self.x, -self.y, 0)

class SingleContainer(Container):
	"""Utility base class for containers restricted to a single child"""
	def __init__(self, x, y, w, h, **kwargs):
		if 'children' in kwargs:
			del kwargs['children']
		Container.__init__(self, x, y, w, h, **kwargs)
		
		self._content = None
	
	def _get_content(self):
		return self._content
	def _set_content(self, content):
		if self._content:
			Container.remove(self, self._content)
		self._content = content
		Container.add(self, self._content)
		self.find_root().update_layout()
	content = property(_get_content, _set_content)
	
	def add(self, other):
		raise UserWarning('add to the content element')
	def remove(self, other):
		raise UserWarning('remove from the content element')
