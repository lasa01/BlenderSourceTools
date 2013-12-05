import bpy, math, io_scene_valvesource
from bpy.types import Node, NodeTree, NodeSocket, PropertyGroup
from bpy.props import *

from . import nodes_sequence, nodes_mesh, nodes_lod

class QcNodeTree(NodeTree):
	'''Generates a Source Engine QC compile script'''
	bl_idname = 'QcNodeTree'
	bl_label = 'QC'
	bl_icon = 'SCRIPT'
	
	def get_primary_node(self):
		for node in self.nodes:
			if type(node) == QcModelInfo:
				return node

##############################################
################# MODEL INFO #################
##############################################
class QcModelInfo(Node):
	bl_label = "QC"
	bl_width_default = 270
	
	modelname = StringProperty(name="Output Name",description="Where to create compiled model files, relative to <game_root>/models/")
	
	def num_lods_update(self,c):
		for node in self.id_data.nodes:
			if node.bl_idname in ["QcRefMesh", "QcModelInfo"]:
				lods = self.num_lods
				if node.bl_idname == "QcRefMesh":
					lods += 1 # reference is held in the array too
				
				while len(node.lods) > lods:
					node.lods.remove(len(node.lods)-1)
				while len (node.lods) < lods:
					node.lods.add()
	num_lods = IntProperty(min=0,max=8,name="Levels of Detail",description="How many levels of detail this model has",update=num_lods_update)
	
	lods = CollectionProperty(type=nodes_lod.QcLod)
	active_lod = IntProperty()
	
	use_lod_inherit = BoolProperty(default=True,name="LODs inherit settings",description="Whether each LOD inherits settings from those above it")
	lod_tab = EnumProperty(items=( ('BONECOLLAPSE',"Bone Collapse","Collapse or replace bones", 'BONE_DATA', 0), ('REPLACEMATERIAL',"Material Replace","Replace or remove materials", 'MATERIAL', 1)),name="LOD settings")
	
	def get_active_lod(self):
		if not len(self.lods): return None
		return self.lods[self.active_lod]
	
	def init(self,c):
		self.inputs.new("QcRefMeshSocket","Primary Mesh")
		
	@classmethod
	def poll(self,nodetree):
		return type(nodetree) == QcNodeTree and not nodetree.get_primary_node()
		
	def draw_buttons(self, context, l):
		l.prop(self,"modelname")
		l.prop(self,"num_lods")
		
		l.template_list("QcLod_ListItem","",
			self,"lods",
			self,"active_lod",
			rows=3,maxrows=8)
		
		l.prop(self,"use_lod_inherit")
		if (len(self.lods)):
			lod = self.lods[self.active_lod]
			r = l.row()
			r.prop(self,"lod_tab",text="",expand=True)
			if self.lod_tab == 'BONECOLLAPSE':
				r.operator(nodes_lod.QcBoneOp_Add.bl_idname,text="Add",icon="ZOOMIN")
				l.template_list("QcBoneOp_ListItem","",
					lod,"bone_ops",
					lod,"active_bone_op",
					rows=4,maxrows=8)
			elif self.lod_tab == 'REPLACEMATERIAL':
				r.operator(nodes_lod.QcMaterialOp_Add.bl_idname,text="Add",icon="ZOOMIN")
				l.template_list("QcMaterialOp_ListItem","",
					lod,"material_ops",
					lod,"active_material_op",
					rows=4,maxrows=8)
			else:
				r.label("")
			
			l.operator("wm.url_open",text="Help",icon='HELP').url = "https://developer.valvesoftware.com/wiki/$lod"

def header_draw(self,context):
	nodetree = context.space_data.node_tree
	if nodetree.bl_idname == QcNodeTree.bl_idname:
		l = self.layout
		if not nodetree.get_primary_node():
			r = l.row()
			r.alert = True
			op = r.operator("node.add_node",icon='ERROR',text="Add root QC node")
			op.type="QcModelInfo"
			op.use_transform = True
	
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem

class QcNodeCategory(NodeCategory):
	@classmethod
	def poll(cls, context):
		return context.space_data.tree_type == 'QcNodeTree'

node_categories = [
	QcNodeCategory("MESH", "Meshes", items=[
		NodeItem("QcRefMesh"),
        ]),
	QcNodeCategory("ANIM", "Animation", items=[
		NodeItem("QcSequence"),
		NodeItem("QcBlendSequence"),
		]),
    ]

def register():
	try: nodeitems_utils.unregister_node_categories("QcNodes")
	except: pass
	nodeitems_utils.register_node_categories("QcNodes", node_categories)
	bpy.types.NODE_HT_header.append(header_draw)

def unregister():
	nodeitems_utils.unregister_node_categories("QcNodes")
	bpy.utils.unregister_module(__name__)
	bpy.types.NODE_HT_header.remove(header_draw)