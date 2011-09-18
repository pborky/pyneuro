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
from rect import Rect
from container import Container, SingleContainer

class Dialogue(SingleContainer):
	"""Moveable window, optionally resizeable"""
	def __init__(self, x, y, w, h, title, **kwargs):
		'''Create a dialogue
		
		Keyword arguments:
		name -- unique widget identifier
		content -- child container
		resizeable -- if true, the dialogue is resizable
		'''
		SingleContainer.__init__(self, x, y, w, h, **kwargs)
		
		self.resizeable = kwargs.get('resizeable', False)
		
		self.elements['frame'] = Rectangle()
		self.elements['title'] = pyglet.text.Label(title, font_size=8, bold=True, color=(0,0,0,255), x=w/2, y=h+7, anchor_x='center', anchor_y='center')
		if self.resizeable:
			self.elements['resize'] = Rectangle(w-15, 0, 15, 15, (0.75, 0.75, 0.75, 0.5))
		
		self.topbar = Rect(0, h, w, 15)
		
		self._in_drag = False
		self._in_resize = False
		
		self.content = kwargs.get('content', Container(0, 0, w, h))
	
	def _get_title(self):
		return self.elements['title'].text
	def _set_title(self, title):
		self.elements['title'].text = title
	title = property(_get_title, _set_title)	
	
	def update_theme(self, theme):
		SingleContainer.update_theme(self, theme)
		
		if theme:
			self.elements['frame'].patch = theme['dialogue']['image']
			self.elements['title'].font_name = theme['font']
			self.elements['title'].font_size = theme['font_size_small']
			self.elements['title'].color = theme['font_color']
	
	def update_layout(self):
		SingleContainer.update_layout(self)
		
		if self.content:
			self._y = self._y + self._h - self.content.h
			self._w, self._h = self.content.w, self.content.h
		
		self.elements['frame'].update(0, 0, self.w, self.h)
		self.elements['title'].x = self.w/2
		if self.resizeable:
			self.elements['resize'].update(self.w-15, 0, 15, 15)
		
		if self.theme:
			patch = self.theme['dialogue']['image']
			self.topbar = Rect(-patch.padding_left, self.h, self.w + patch.padding_right, patch.padding_top)
			self.elements['title'].y = self.h + patch.padding_top/2
	
	def bounds(self):
		return Rect(self._gx, self._gy, self.w, self.h + self.topbar.h)
	
	def on_mouse_press(self, x, y, button, modifiers):
		if button == pyglet.window.mouse.LEFT and \
				self.topbar.hit_test(x - self.x, y - self.y):
			self._in_drag = True
			self._offset_x = x - self.x
			self._offset_y = y - self.y
			return pyglet.event.EVENT_HANDLED
		
		if self.resizeable and button == pyglet.window.mouse.LEFT and \
				self.elements['resize'].hit_test(x - self.x, y - self.y):
			self._in_resize = True
			self._orig_y = self.y
			self._orig_h = self.h
			self._offset_x = x - self.x - self.w
			self._offset_y = y - self.y
			return pyglet.event.EVENT_HANDLED
		
		SingleContainer.on_mouse_press(self, x, y, button, modifiers)
		return pyglet.event.EVENT_UNHANDLED
	
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		if button == pyglet.window.mouse.LEFT and self._in_drag:
			self.x = x - self._offset_x
			self.y = y - self._offset_y
			return pyglet.event.EVENT_HANDLED
		
		if button == pyglet.window.mouse.LEFT and self._in_resize:
			self._w = x - self.x - self._offset_x
			if self.w < 100:
				self._w = 100
			
			self._h = self._orig_h - (y - self._orig_y - self._offset_y)
			self.y = self._orig_y + (y - self._orig_y - self._offset_y)
			if self.h < 50:
				self.y -= 50 - self.h
				self._h = 50
			
			self.content._w, self.content._h = self.w, self.h
			self.update_layout()
			
			return pyglet.event.EVENT_HANDLED
		
		SingleContainer.on_mouse_drag(self, x, y, dx, dy, button, modifiers)
		return pyglet.event.EVENT_UNHANDLED
	
	def on_mouse_release(self, x, y, button, modifiers):
		if button == pyglet.window.mouse.LEFT and self._in_drag:
			self._in_drag = False
			return pyglet.event.EVENT_HANDLED
		
		SingleContainer.on_mouse_release(self, x, y, button, modifiers)
		return pyglet.event.EVENT_UNHANDLED
