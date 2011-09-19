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
from widget import Widget

class Button(Widget):
	"""Clickable button"""
	def __init__(self, x, y, w, h, text, **kwargs):
		'''Create a button control
		
		Keyword arguments:
		action -- callback to be invoked when the button is clicked
		'''
		Widget.__init__(self, x, y, w, h, kwargs.get('name'))
		
		self.elements['label'] = pyglet.text.Label(text, font_size=8, color=(0,0,0,255), x=w/2, y=h/2, anchor_x='center', anchor_y='center')
		self.elements['frame'] = Rectangle()
		
		self.action = kwargs.get('action', None)
		self._down = False
	
	def _get_text(self):
		return self.elements['label'].text
	def _set_text(self, text):
		self.elements['label'].text = text
	text = property(_get_text, _set_text)
	
	def update_theme(self, theme):
		Widget.update_theme(self, theme)
		
		if theme:
			patch = theme['button'][('image_down' if self._down else 'image_up')]
			
			label = self.elements['label']
			label.font_name = self.theme['font']
			label.font_size = self.theme['font_size']
			label.color = theme['font_color']
			
			font = label.document.get_font()
			height = font.ascent - font.descent
			
			self._w = patch.padding_left + label.content_width + patch.padding_right
			self._h = patch.padding_bottom + height + patch.padding_top
			
			label.x = patch.padding_left + label.content_width/2
			label.y = patch.padding_bottom + height/2 - font.descent
			
			self.elements['frame'].patch = patch
			self.elements['frame'].update(patch.padding_left, patch.padding_bottom, self.w - patch.padding_left, self.h - patch.padding_top)
	
	def on_mouse_press(self, x, y, button, modifiers):
		if button == pyglet.window.mouse.LEFT and self.hit_test(x, y):
			self.elements['frame'].patch = self.theme['button']['image_down']
			self._down = True
			return pyglet.event.EVENT_HANDLED
		
		Widget.on_mouse_press(self, x, y, button, modifiers)
		return pyglet.event.EVENT_UNHANDLED
	
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		if button == pyglet.window.mouse.LEFT and self._down:
			if self.hit_test(x, y):
				self.elements['frame'].patch = self.theme['button']['image_down']
			else:
				self.elements['frame'].patch = self.theme['button']['image_up']
			
			return pyglet.event.EVENT_HANDLED
				
		Widget.on_mouse_drag(self, x, y, dx, dy, button, modifiers)
		return pyglet.event.EVENT_UNHANDLED
	
	def on_mouse_release(self, x, y, button, modifiers):
		if button == pyglet.window.mouse.LEFT and self._down:
			self.elements['frame'].patch = self.theme['button']['image_up']
			self._down = False
			if self.hit_test(x, y):
				if self.action:
					self.action(self)
				return pyglet.event.EVENT_HANDLED
		
		Widget.on_mouse_press(self, x, y, button, modifiers)
		return pyglet.event.EVENT_UNHANDLED
