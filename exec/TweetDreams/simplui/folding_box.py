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

class FoldingBox(SingleContainer):
	"""Collapsible container"""
	def __init__(self, x, y, w, h, title, **kwargs):
		'''Create a folding box
		
		Keyword arguments:
		name -- unique widget identifier
		content -- child container
		collapsed -- if true, container folded initially
		'''
		SingleContainer.__init__(self, x, y, w, h+15, **kwargs)
		
		self.elements['topbar'] = Rectangle()
		self.elements['title'] = pyglet.text.Label(title, font_size=8, color=(0,0,0,255), x=w/2, y=h+7, anchor_x='left', anchor_y='center')
		
		self._last_h = 15
		self._collapsed = kwargs.get('collapsed', False)
		if self._collapsed:
			self._h, self._last_h = self._last_h, self._h
		
		self.content = kwargs.get('content', Container(0, 0, w, h))
	
	def _get_title(self):
		return self.elements['title'].text
	def _set_title(self, title):
		self.elements['title'].text = title
	title = property(_get_title, _set_title)
	
	def update_theme(self, theme):
		SingleContainer.update_theme(self, theme)
		
		if theme:
			patch = self.theme['folding_box'][('image_closed' if self._collapsed else 'image')]
			
			self.elements['topbar'].patch = patch
			self.elements['title'].font_name = theme['font']
			self.elements['title'].font_size = theme['font_size_small']
			self.elements['title'].color = theme['font_color']
			
			if self._collapsed:
				self._h = patch.padding_top
			else:
				self._last_h = patch.padding_top
	
	def update_layout(self):
		SingleContainer.update_layout(self)
		
		if self.theme:
			patch = self.theme['folding_box'][('image_closed' if self._collapsed else 'image')]
			
			if self.content:
				self._w = self.content.w + patch.padding_left + patch.padding_right
				if not self._collapsed:
					self._h = self.content.h + patch.padding_bottom + patch.padding_top
			
			self.elements['topbar'].update(patch.padding_left, self.h - patch.padding_top, self.w - patch.padding_left - patch.padding_right, 1)
			self.elements['title'].x = patch.padding_left
			self.elements['title'].y = self.h - patch.padding_top/2 + 1
			
			self.topbar = Rect(0, self.h-patch.padding_top, self.w, patch.padding_top)
	
	def on_mouse_press(self, x, y, button, modifiers):
		if button == pyglet.window.mouse.LEFT and \
				self.topbar.hit_test(x - self._gx, y - self._gy):
			self._collapsed = not self._collapsed
			self._h, self._last_h = self._last_h, self._h
			self.elements['topbar'].patch = self.theme['folding_box'][('image_closed' if self._collapsed else 'image')]
			self.find_root().update_layout()
			return pyglet.event.EVENT_HANDLED
		
		SingleContainer.on_mouse_press(self, x, y, button, modifiers)
		return pyglet.event.EVENT_UNHANDLED
	
	def clip_rect(self):
		return Rect(self._gx, self._gy, self.w, self.h-15)
