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

class TextInput(Widget):
	"""Text input field"""
	def __init__(self, x, y, w, **kwargs):
		'''Create a text input control
		
		Keyword arguments:
		name -- unique widget identifier
		text -- intitial value
		action -- callback to be invoked when text is entered
		'''
		Widget.__init__(self, x, y, w, 1, kwargs.get('name'))
		
		self.document = pyglet.text.document.UnformattedDocument(kwargs.get('text', ''))
		self.layout = pyglet.text.layout.IncrementalTextLayout(self.document, w-4, 1, multiline=False)
		
		font = self.document.get_font()
		height = font.ascent - font.descent
		
		self.layout.x, self.layout.y = 2, 2
		self.caret = pyglet.text.caret.Caret(self.layout)
		
		self.elements['layout'] = self.layout
		self.elements['frame'] = Rectangle()
		
		self.action = kwargs.get('action', None)
		self._focused = False
		self.caret.visible = False
	
	def _get_text(self):
		return self.document.text
	def _set_text(self, text):
		self.document.text = text
	text = property(_get_text, _set_text)
	
	def update_theme(self, theme):
		Widget.update_theme(self, theme)
		
		if theme:
			patch = theme['text_input']['image']
			
			self.elements['frame'].patch = patch
			self.document.set_style(0, len(self.document.text), {'font_size': theme['font_size'], 'color': theme['font_color']})
			
			font = self.document.get_font()
			height = font.ascent - font.descent
			
			self._h = patch.padding_bottom + height + patch.padding_top
			self.elements['layout'].y = patch.padding_bottom
			self.elements['layout'].height = height
			self.elements['frame'].update(patch.padding_left, patch.padding_bottom, self.w - patch.padding_left - patch.padding_right, height)
	
	def update_layout(self):
		Widget.update_layout(self)
		
		if self.theme:
			patch = self.theme['text_input']['image']
			self.elements['layout'].x = patch.padding_left
			self.elements['layout'].width = self.w - patch.padding_left - patch.padding_right
	
	def on_mouse_press(self, x, y, button, modifiers):
		if button == pyglet.window.mouse.LEFT and self.hit_test(x, y) and not self._focused:
			self.elements['frame'].color = (0.65, 0.65, 0.65, 0.65)
			self._focused = True
			self.find_root().focus.append(self)
			self.caret.visible = True
			self.caret.on_mouse_press(x - self._gx - 2, y - self._gy - 2, button, modifiers)
			return pyglet.event.EVENT_HANDLED
		if button == pyglet.window.mouse.LEFT and self._focused:
			if self.hit_test(x, y):
				self.caret.on_mouse_press(x - self._gx - 2, y - self._gy - 2, button, modifiers)
			else:
				self.caret.visible = False
				self.find_root().focus.pop()
				self._focused = False
				self.elements['frame'].color = (0.75, 0.75, 0.75, 0.75)
				if self.action:
					self.action(self)
			return pyglet.event.EVENT_HANDLED
		
		Widget.on_mouse_press(self, x, y, button, modifiers)
		return pyglet.event.EVENT_UNHANDLED
	
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		if self._focused:
			self.caret.on_mouse_drag(x - self._gx - 2, y - self._gy - 2, dx, dy, button, modifiers)
			return pyglet.event.EVENT_HANDLED
				
		Widget.on_mouse_drag(self, x, y, dx, dy, button, modifiers)
		return pyglet.event.EVENT_UNHANDLED
	
	def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
		if self._focused:
			self.caret.on_mouse_scroll(x - self._gx - 2, y - self._gy - 2, scroll_x, scroll_y)
			return pyglet.event.EVENT_HANDLED
		
		Widget.on_mouse_scroll(self, x, y, scroll_x, scroll_y)
		return pyglet.event.EVENT_UNHANDLED
	
	def on_key_press(self, symbol, modifiers):
		from pyglet.window import key
		
		if self._focused and symbol in (key.ENTER, key.TAB):
			self.caret.visible = False
			self.find_root().focus.pop()
			self._focused = False
			self.elements['frame'].color = (0.75, 0.75, 0.75, 0.75)
			if self.action:
				self.action(self)
			return pyglet.event.EVENT_HANDLED
		
		Widget.on_key_press(self, symbol, modifiers)
		return pyglet.event.EVENT_UNHANDLED
	
	def on_text(self, text):
		if self._focused:
			self.caret.on_text(text)
			return pyglet.event.EVENT_HANDLED
		
		Widget.on_text(self, text)
		return pyglet.event.EVENT_UNHANDLED
	
	def on_text_motion(self, motion, select=False):
		if self._focused:
			self.caret.on_text_motion(motion, select)
			return pyglet.event.EVENT_HANDLED
		
		Widget.on_text_motion(self, motion, select)
		return pyglet.event.EVENT_UNHANDLED
