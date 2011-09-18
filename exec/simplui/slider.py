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

class Slider(Widget):
	"""Value slider"""
	def __init__(self, x, y, w, **kwargs):
		'''Create a slider control
		
		Keyword arguments:
		name -- unique widget identifier
		min -- minimum value
		max -- maximum value
		value -- initial value
		action -- callback to be invoked when the slider is moved
		continuous -- if true, invoke action on every movement, else
			invoke action only when the user releases the mouse button
		'''
		Widget.__init__(self, x, y, w, 10, kwargs.get('name'))
		
		self._min = kwargs.get('min', 0.0)
		self._max = kwargs.get('max', 1.0)
		
		self._value = kwargs.get('value', 0.5)
		
		self.elements['track'] = Rectangle()
		self.elements['knob'] = Rectangle()
		
		self.action = kwargs.get('action', None)
		self._continuous = kwargs.get('continuous', True)
		
		self._down = False
	
	def _get_min(self):
		return self._min
	def _set_min(self, min):
		self._min = min
		nx = (self.w-8)*self._value/(self._max-self._min)
		self.elements['knob'].update(nx, self.h/2 - 4, 8, 8)
	min = property(_get_min, _set_min)
	
	def _get_max(self):
		return self._max
	def _set_max(self, max):
		self._max = max
		nx = (self.w-8)*self._value/(self._max-self._min)
		self.elements['knob'].update(nx, self.h/2 - 4, 8, 8)
	max = property(_get_max, _set_max)
	
	def _get_value(self):
		return self._value
	def _set_value(self, value):
		self._value = value
		nx = int((self.w-8)*self._value/(self._max-self._min))
		self.elements['knob'].update(nx, self.h/2 - 4, 8, 8)
	value = property(_get_value, _set_value)
	
	def update_theme(self, theme):
		Widget.update_theme(self, theme)
		
		if theme:
			patch = theme['slider']['image_slider']
			patch_knob = theme['slider']['image_knob']
			
			self._h = patch.padding_bottom + patch.padding_top
			
			self.elements['track'].patch = patch
			self.elements['track'].update(patch.padding_left, patch.padding_bottom, self.w - patch.padding_left - patch.padding_right, self.h - patch.padding_bottom - patch.padding_top)
			
			self._xoffset = patch_knob.padding_left
			self._xpad = patch_knob.padding_left + patch_knob.padding_right
			self._yoffset = patch_knob.padding_bottom
			
			nx = int(self._xoffset + (self.w-self._xpad)*self._value/(self._max-self._min))
			
			self.elements['knob'].patch = patch_knob
			self.elements['knob'].update(nx, self._yoffset, 1, 1)
	
	def on_mouse_press(self, x, y, button, modifiers):
		if button == pyglet.window.mouse.LEFT and self.hit_test(x, y):
			nx = min(self._xoffset+self.w-self._xpad, max(self._xoffset, x - self._gx))
			self.elements['knob'].color = (0.65, 0.65, 0.65, 1.0)
			self.elements['knob'].update(nx, self._yoffset, 1, 1)
			self._down = True
			self._value = self._min + nx/float(self.w-8)*(self._max-self._min)
			if self._continuous and self.action:
				self.action(self)
			return pyglet.event.EVENT_HANDLED
		
		Widget.on_mouse_press(self, x, y, button, modifiers)
		return pyglet.event.EVENT_UNHANDLED
	
	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		if button == pyglet.window.mouse.LEFT and self._down:
			nx = min(self._xoffset+self.w-self._xpad, max(self._xoffset, x - self._gx))
			self.elements['knob'].update(nx, self._yoffset, 1, 1)
			self._value = self._min + nx/float(self.w-8)*(self._max-self._min)
			if self._continuous and self.action:
				self.action(self)
			return pyglet.event.EVENT_HANDLED
				
		Widget.on_mouse_drag(self, x, y, dx, dy, button, modifiers)
		return pyglet.event.EVENT_UNHANDLED
	
	def on_mouse_release(self, x, y, button, modifiers):
		if button == pyglet.window.mouse.LEFT and self._down:
			nx = min(self._xoffset+self.w-self._xpad, max(self._xoffset, x - self._gx))
			self.elements['knob'].color = (0.25, 0.25, 0.25, 1.0)
			self.elements['knob'].update(nx, self._yoffset, 1, 1)
			self._value = self._min + nx/float(self.w-8)*(self._max-self._min)
			self._down = False
			if self.action:
				self.action(self)
			return pyglet.event.EVENT_HANDLED
		
		Widget.on_mouse_press(self, x, y, button, modifiers)
		return pyglet.event.EVENT_UNHANDLED
