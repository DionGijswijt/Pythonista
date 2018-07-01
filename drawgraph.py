# A simple app to draw undirected graphs and export to the clipboard as TiKZ or Python code
# Everything happens inside a Scene with vertices and edges as Nodes
from scene import *
import sound
from math import atan2
from ui import Path
import clipboard

A = Action

# A vertex of the graph. It keeps a list of outgoing edges
# A vertex that is pressed becomes selected (by the corresponding touch) and turns red
# Selecting two (or more) vertices allows adding edges later on.
class Vertex(SpriteNode):
	def __init__(self,x,y,**kwargs):
		SpriteNode.__init__(self,'iow:record_32',**kwargs)
		self.selected=None
		self.edges=[]
		self.position=(x,y)
		self.color=	'#d3d3d3'
		self.scale=0.5
		self.z_position=2

# An edge of the graph. If keeps track of its two end vertices a and b.
# update takes care of transforming the sprite to represent a line 
# between a and b.
class Edge(SpriteNode):
	def __init__(self, a, b, **kwargs):
		self.a=a
		self.b=b
		SpriteNode.__init__(self,'pzl:Green4',**kwargs)
		self.y_scale=0.08
		self.anchor_point=(0,0.5)
		self.z_position=1
		self.update()

	def update(self):
		a=self.a.position
		b=self.b.position
		d = b-a
		self.x_scale=abs(d)/64
		self.rotation=atan2(d.y,d.x)
		self.position=a
	
	
# We need dialog windows.
# A dialog window has a title and a body
# The window tries to adjust its size to its content
# The window needs to now its `parent' view for positioning
class Dialog (ShapeNode):
	def __init__(self, view):
		# The window is a rectangular ShapeNode
		# Positioning depends on the parent view
		self.view = view
		
		# The window can be visible or hidden
		self.visible = False
		
		# The window itself
		# The shape will be adjusted later based on the content
		ShapeNode.__init__(self,fill_color='#d7d7d7',stroke_color='#ffffff')
		self.alpha=0.9
		self.anchor_point=(0.5,1)
		self.position=(self.view.size.w/2,500)
		self.shadow=('#000000',10,10,20)
		self.z_position=10
		
		# The title is added
		self.title=LabelNode('', font=('Menlo',24))
		self.title.color='#000000'
		self.title.anchor_point=(0.5,1)
		self.title.position=(0,-24)
		self.add_child(self.title)
		
		# The body is added
		self.body=LabelNode('', font=('Menlo',16))
		self.body.color='#000000'
		self.body.anchor_point=(0.5,1)
		self.body.position=(0,-64)
		self.add_child(self.body)
		
		# A closing icon is added
		self.close=SpriteNode('iob:close_round_24')
		self.close.anchor_point=(1,1)
		self.add_child(self.close)
		
		# Now adjust the proper dimensions and position for the window
		# Also the position of the closing icon must be adjusted
		self.adjust()
		
		
	# Compute proper dimensions of the dialog window
	# Redraw the window
	def adjust(self):
		w = min(self.view.size.w-40,max(self.body.size.w+64, self.title.size.w+160, 200))
		h = min(self.view.size.h-100,self.body.size.h + 60)
		p=ui.Path.rounded_rect(0,0,w,h,12)
		p.line_width=2
		self.path=p
		self.close.position=(self.size.w/2-48,-24)
		self.position=(self.view.size.w/2,h+100)
		
	# Change body of the dialog window. Adjust window sizes...	
	def settext(self,t):
		self.body.text=t
		self.adjust()
	
	# Change title of the dialog window	
	def settitle(self,t):
		self.title.text=t
		self.adjust()
		
	# Show the dialog	window by adding it to the view 
	def show(self):
		if not self.visible:
			self.visible = True
			self.view.add_child(self)
	
	# Hide the dialog window
	def hide(self):
		if self.visible:
			self.visible = False
			self.remove_from_parent()
	
			
# Given a graph, convert it to Python code	
def ToPython(vertices, edges):
	# We first number the vertices from 0 to n-1
	vnum = {}
	n= len(vertices)
	for i in range(n):
		vnum[vertices[i]] = i
	
	# t is the string containing the Python code
	# First make a list of vertices [[x1,y1], ..., [xn,yn]]	
	t ='GraphNodes = ['
	for a in vertices:
		x,y =a.position
		t = t + '[%.0f, %.0f], ' % (x,y)
	if len(vertices)>0:	#remove the superfluous comma at the end
		t = t[:-2]
	t =t + '];  '
	
	# Make a list of vertices [[u1,v1],... [um,vm]]
	t = t + 'GraphEdges = ['
	for (a,b) in edges:
		na=vnum[a]
		nb=vnum[b]
		if na < nb:
			t = t + '[%d, %d], ' % (na,nb)
			
	if len(edges) > 0 : #remove the superfluous comma at the end
		t =t[:-2]
	t =t + ']'
	return t
	

# Given a graph, convert it to a TiKZ picture	
def ToTikz(vertices, edges):
	# Number the vertices
	vnum = {}
	n= len(vertices)
	for i in range(n):
		vnum[vertices[i]] = i
		
	t ='\\begin{tikzpicture}[x=%fcm, y=%fcm]\r' % (0.01,0.01)
	for (a,b) in edges:
		na=vnum[a]
		nb=vnum[b]
		if na < nb:
			x1, y1 = a.position
			x2, y2 = b.position
			t = t + '\\draw[very thick] (%.0f, %.0f) -- (%.0f, %.0f);\r' % (x1,y1,x2,y2)
			
	for a in vertices:
		x1, y1 =a.position
		t = t + '\\filldraw[fill=white, draw=black] (%.0f, %.0f) circle [radius = 2pt];\r' % (x1,y1)
		
	t = t + '\\end{tikzpicture}\n'
	return t
		

# The main loop containing all the action...							
class MyScene(Scene):
	# Add a vertex at position (x,y) and display it
	def addVertex(self,x,y):
		v=Vertex(x,y)
		self.vertices.append(v)
		self.add_child(v)
	
	# Remove a vertex and all adjacent edges	
	def delVertex(self,v):
		w = list(v.edges)
		for e in w:
			self.delEdge(e)
		self.vertices.remove(v)
		v.remove_from_parent()
	
	# Remove all vertices of the graph		
	def clearAll(self):
		for v in list(self.vertices):
			self.delVertex(v)
		if self.sound:
			sound.play_effect('rpg:MetalPot3')
	
	# Add an edge between a and b
	# Note that we add both opposite pairs (a,b) and (b,a)
	def addEdge(self,a,b):
		if (a,b) not in self.edges and a!= b:
			e=Edge(a,b)
			self.edges[(a,b)]=e
			self.edges[(b,a)]=e
			
			# Add the edge to the edge lists of the end vertices
			a.edges.append(e)
			b.edges.append(e)
			
			#Display the edge
			self.add_child(e)
	
	# Remove an edge		
	def delEdge(self,e):
		a=e.a
		b=e.b
		a.edges.remove(e)
		b.edges.remove(e)
		self.edges.pop((a,b))
		self.edges.pop((b,a))
		e.remove_from_parent()
		
	# Setup
	# The view is divided into a menu bar and a draw area
	def setup(self):
		self.background_color = '#000000'
	
		# The draw area
		path=ui.Path.rounded_rect(2,2,self.size.w-2,self.size.h-70,12)
		path.line_width=2
		self.drawarea=ShapeNode(path,fill_color='#004f83',stroke_color='#ffffff')
		self.drawarea.anchor_point=(0,0)
		self.drawarea.position=(0,68)
		self.add_child(self.drawarea)
		
		# The menu bar
		# It contains several icons etc.
		path=ui.Path.rounded_rect(2,2,self.size.w-2,62,12)
		path.line_width=2
		self.menu=ShapeNode(path,'#d7d7d7',stroke_color='#ffffff')
		self.menu.anchor_point=(0,0)
		self.menu.position=(0,0)
		self.add_child(self.menu)
		
		# The trash can
		# It knows if it is currently pressed
		self.trash=SpriteNode('iob:ios7_trash_256')
		self.trash.scale=0.25
		self.trash.anchor_point=(0,0)
		self.trash.position=(8,0)
		self.add_child(self.trash)
		self.trash.pressed = False
		
		# magnification factor
		self.mag=1.0
		self.maglabel=LabelNode('100%',font=('Menlo',28))
		self.maglabel.anchor_point=(1,0.5)
		self.maglabel.position=(230,32)
		self.maglabel.color='#000000'
		self.add_child(self.maglabel)
		
		# increase magnification
		self.magplus=SpriteNode('typb:Plus')
		self.magplus.anchor_point=(0,0)
		self.magplus.position=(226,8)
		self.add_child(self.magplus)
		
		# decrease magnification
		self.magmin=SpriteNode('typb:Minus')
		self.magmin.anchor_point=(0,0)
		self.magmin.position=(100,8)
		self.add_child(self.magmin)

		# Sound can be on or off(default)
		self.sound=False
		self.volume=SpriteNode('iob:ios7_volume_low_256')
		self.volume.scale=0.25
		self.volume.anchor_point=(0,0)
		self.volume.position=(self.size.w-64,0)
		self.add_child(self.volume)
		
		# Export icon
		# keeps track of export type (tiks or python)
		self.export=SpriteNode('typb:Export')
		self.export.anchor_point=(0,0)
		self.export.position=(320,8)
		self.add_child(self.export)
		self.export.type='tikz'
		
		# Export label indicates the export type
		self.exportlabel=LabelNode('TiKZ',font=('Menlo',28))
		self.exportlabel.anchor_point=(0,0.5)
		self.exportlabel.position=(370,32)
		self.exportlabel.color='#000000'
		self.add_child(self.exportlabel)
		
		# The dialog window. Hidden until shown.
		self.dia = Dialog(self)
		
		# A list of all vertices
		self.vertices=[]
		
		# A dictionary of edges. The keys are the vertex pairs
		self.edges={}

		
	# The view changed size. We have to adjust sizes and positions of elements....
	def did_change_size(self):
		# Redraw the menu bar
		path=ui.Path.rounded_rect(2,2,self.size.w-2,62,12)
		path.line_width=2
		self.menu.path=path
		
		# Reposition the volume icon
		self.volume.position=(self.size.w-64,0)
		
		# Redraw the draw area
		path=ui.Path.rounded_rect(2,2,self.size.w-2,self.size.h-70,12)
		path.line_width=2
		self.drawarea.path=path
		
		# Redraw the dialog window	
		self.dia.adjust()
			
		if self.sound:
			sound.play_effect('rpg:BookFlip1')
	
	# After zooming in or out, recalculate vertex positions (and redraw edges)
	# Scaling is with respect to center of the view
	def rescale(self,factor):
		self.mag=self.mag*factor
		self.maglabel.text='%d' % int(self.mag*100) + '%'
		
		for v in self.vertices:
			v.position=v.position*factor+self.size*(1-factor)*0.5
		for pair in self.edges:
			self.edges[pair].update()
			
		if self.sound:
			sound.play_effect('rpg:MetalLatch')
			
		
	# Someone has touched the screen !
	def touch_began(self, touch):
		pos = touch.location
		id = touch.touch_id
		
		# First handle touches in the menu bar
		if pos in self.menu.bbox:
			# Toggle sound
			if pos in self.volume.bbox:
				if self.sound:
					self.sound=False
					self.volume.texture=Texture('iob:ios7_volume_low_256')
				else:
					self.sound=True
					self.volume.texture=Texture('iob:ios7_volume_high_256')
					sound.play_effect('8ve:8ve-beep-warmguitar')
			
			# Magnify. Touching the magnification factor returns you to 100%
			elif pos in self.magplus.bbox:
				self.rescale(1.2)
			elif pos in self.magmin.bbox:
				self.rescale(1/1.2)
			elif pos in self.maglabel.bbox:
				self.rescale(1/self.mag)
				
			# Pressing the trash for 0.8 sec deletes the whole graph	
			elif pos in self.trash.bbox:
				self.trash.pressed=True
				self.trash.texture=Texture('iob:ios7_trash_outline_256')
				action=A.sequence(A.scale_to(4,0.6),A.wait(0.2),A.scale_to(0.25,0),A.call(self.clearAll,0))
				self.trash.run_action(action)
			
			# Export the graph
			# Toggle the export type	
			elif pos in self.exportlabel.bbox:
				if self.export.type=='tikz':
					self.export.type='python'
					self.exportlabel.text='Python'
				else:
					self.export.type='tikz'
					self.exportlabel.text='TiKZ'
					
			# Export and shows dialog	
			elif pos in self.export.bbox:
				if self.export.type == 'tikz':
					t=ToTikz(self.vertices, self.edges)
					self.dia.settext('A TiKZ code of your graph has been copied to the clipboard!')
					self.dia.settitle('Export to TiKZ')
					self.dia.show()
					clipboard.set(t)
				else:
					t=ToPython(self.vertices, self.edges)
					self.dia.settext('Your graph has been copied to the clipboard\rin the form of Python lists:\n\nGraphNodes=[[x1,y1],...,[xn,yn]]\rGraphEdges=[[u1,v1],...,[um,vm]]\n')
					self.dia.settitle('Export to Python')
					self.dia.show()
					clipboard.set(t)
		# Allow closing the dialog window	
		elif self.dia.visible:
			if pos - self.dia.position in self.dia.close.bbox:
				self.dia.hide()
		
		# Finally, we consider touches in the draw area	
		# We keep track of the vertices that are currently pressed and the corresponding touch id's
		# Pressing multiple vertices results in toggling all edges among them
		# Typically, only 0,1 or 2 vertices are pressed simultaneously
		elif pos in self.drawarea.bbox and pos.y >=80:
			
			# Determine the closest unselected vertex
			v = None
			d = 1000
			for vc in self.vertices:
				if not vc.selected:
					dd = abs(pos - vc.position)
					if dd < d:
						d = dd
						v = vc
			# We have found an unselected vertex close by
			# We toggle edges between it and the other selected vertices
			if v and d < 40:
				v.texture = Texture('iow:record_32')
				v.color='#d40c0c'
				v.scale=0.8
				v.selected = id
				for v2 in self.vertices:
					if v2 != v and v2.selected:
						if self.sound:
							sound.play_effect('rpg:MetalClick')
						if (v,v2) in self.edges:
							self.delEdge(self.edges[(v,v2)])
						else:
							self.addEdge(v,v2)
			elif d > 40:
				self.addVertex(pos.x,pos.y)
				if self.sound:
					sound.play_effect('rpg:Footstep00')
			
	# if a touch connected to a vertex is moved, then move the vertex
	def touch_moved(self, touch):
		x,y = touch.location
		id=touch.touch_id
		for v in self.vertices:
			if v.selected == id:
				v.position=(x,y)
				for e in v.edges:
					e.update()
			
				
	# A touch ended...
	def touch_ended(self, touch):
		id = touch.touch_id
		
		# If the trash is released in time, deletion of graph is cancelled
		if self.trash.pressed:
			self.trash.pressed=False
				
			self.trash.texture=Texture('iob:ios7_trash_256')
			self.trash.remove_all_actions()
			self.trash.scale=0.25
			
		else:
			for v in self.vertices:
				if v.selected == id:
					
					# If a vertex is released in the trash, remove it
					if v.position in self.trash.bbox:
						self.delVertex(v)
						if self.sound:
							sound.play_effect('game:Woosh_1')
					else:
						# If a verted is released, it returns to normal (unselected).
						# Take care that it remains in the drawing area!
						v.selected = None
						v.scale=0.5
						v.color='#d3d3d3'
						x=v.position.x
						y=v.position.y
						if y < 80:
							y=80
						if y > self.size.h-20:
							y = self.size.h-20
						if x < 20:
							x=20
						if x > self.size.w-20:
							x= self.size.w-20
						v.position=(x,y)
						for e in v.edges:
							e.update()
			

if __name__ == '__main__':
	run(MyScene(), show_fps=False)
