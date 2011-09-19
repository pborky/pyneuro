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

class Rect(object):
	'''Fast and simple rectangular collision structure'''
	
	def __init__(self, x, y, w, h):
		'''Create a rectangle'''
		self.x, self.y = x, y
		self.w, self.h = w, h
	
	def intersect(self, r):
		'''Compute the intersection of two rectangles'''
		if not self.collides(r):
			return Rect(0, 0, 0, 0)
		x, y = max(self.x, r.x), max(self.y, r.y)
		x2, y2 = min(self.x+self.w, r.x+r.w), min(self.y+self.h, r.y+r.h)
		n = Rect( x, y, x2 - x, y2 - y )
		return n
		
	def collides(self, r):
		'''Determine whether two rectangles collide'''
		if self.x+self.w < r.x or self.y+self.h < r.y or \
				self.x > r.x + r.w or self.y > r.y + r.h:
			return False
		return True
	
	def hit_test(self, x, y):
		return (x >= self.x and x <= self.x + self.w) and (y >= self.y and y <= self.y + self.h)
	
	@property
	def min(self):
		return (self.x, self.y)
	
	@property
	def max(self):
		return (self.x + self.w, self.y + self.h)
	
	def __iter__(self):
		return iter((self.x, self.y, self.w, self.h))
	
	def __repr__(self):
		return '[%d %d %d %d]' % (self.x, self.y, self.w, self.h)
