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

class Label(Widget):
	"""Textual label"""
	def __init__(self, x, y, text, **kwargs):
		'''Create a label
		
		Keyword arguments:
		name -- unique widget identifier
		'''
		content = pyglet.text.Label(text, font_size=8, color=(0,0,0,255), x=0, y=0, anchor_x='left', anchor_y='bottom')
		font = content.document.get_font()
		height = font.ascent - font.descent
		
		Widget.__init__(self, x, y, content.content_width, height, kwargs.get('name'))
		self.elements['content'] = content
	
	def _get_text(self):
		return self.elements['content'].text
	def _set_text(self, text):
		self.elements['content'].text = text
	text = property(_get_text, _set_text)
	
	def update_theme(self, theme):
		Widget.update_theme(self, theme)
		
		if theme:
			content = self.elements['content']
			content.font_name = self.theme['font']
			content.font_size = self.theme['font_size']
			content.color = theme['font_color']
			
			font = content.document.get_font()
			height = font.ascent - font.descent
			
			self._w, self._h = content.content_width, height
