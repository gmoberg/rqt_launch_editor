import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
import os
import yaml
import io
import roslaunch

#need to be able to easily match 
class EditableFile:
	def __init__(self, path, is_yaml):
		self.path = path
		self.is_yaml = is_yaml

#Nodes used to build tree, not to be confused with ROS datatype
class EditorNode:
	
	def __init__(self, name, obj):
		self.name = name
		self.obj = obj
		self.children = []

	def add_child(self, elt):
		self.children.append(elt)

	def add_children(self, lst):
		self.children += lst

	def del_child(self, elt):
		self.children.remove(elt)

class EditorTree:

	def __init__(self, launch_file):
		self.launch_file = launch_file
		self.xtree = ET.parse(launch_file)
		self.xroot = self.xtree.getroot()

		self.editable_root = EditableFile(self.launch_file, False)
		self.file_map = {self.editable_root: self.xtree}
		self.edit_list = []

		#initialize tree structure
		self.struct = self.create()

	#keep track of edits in list
	#tree of lists - possibly too long to make
	def create(self):
		#rosparam and include need special treatment, should I skip launch
		def _create(xml_root, first_time):

			name = ""

			root_tag = xml_root.tag
			if root_tag == "launch":
				name = "launch"
			elif root_tag == "include":
				name = "include" + resolve_arg(xml_root.get("file"))
			elif root_tag == "remap":
				name = "remap"
			elif root_tag == "rosparam":
				name = "rosparam"
			elif root_tag == "group":
				name = "group"
			else: 
				name = xml_root.attrib["name"] if xml_root.attrib.has_key("name") else xml_root.tag

			node = EditorNode(name, xml_root)

			if root_tag == "rosparam":
				yaml_as_string = ""
				is_file = False
				ptr = None
				if xml_root.attrib.has_key("file"):
					path = xml_root.get("file")
					subst_val = resolve_arg(path)
					if os.path.isfile(subst_val):
						yaml_as_string = subst_val
						is_file = True
				else:
					ptr = xml_root
					yaml_as_string = xml_root.text

				node.add_children(self.process_yaml(yaml_as_string, is_file, ptr_node=ptr))

			elif root_tag == "include":
				#update file map
				path = xml_root.get("file")
				subst_val = resolve_arg(path)
				if os.path.isfile(subst_val):
					tree2 = ET.parse(subst_val)
					root2 = tree2.getroot()
					node.add_child(_create(root2, False))
					f = EditableFile(subst_val, False)
					self.file_map[f] = tree2

			for child in xml_root:
				node.add_child(_create(child, False))

			if first_time:
				self.root = node

			return node

		return _create(self.xroot, True) #probably needs recursive definition

	def getroot(self):
		return self.root

	# add and delete need to modify underlying dicts, trees, or structs
	#also needs to be in gui
	#need to call a reset button
	def add_to_tree(self, elt, parent):
		if isinstance(parent.obj, YamlStruct):
			print "----Invalid Change----"
			return 
		elif type(parent.obj).__name__ == 'Element':
			if type(elt.obj).__name__ == 'Element':
				parent.obj.append(elt.obj)
			else:
				print "----Invalid Change----"
				return
		elif isinstance(parent.obj, dict):
			if isinstance(elt.obj, dict):
				return
			elif isinstance(elt.obj, YamlStruct):
				parent.obj[elt.obj.key] = elt.obj.value
			else:
				return
		else:
			print "----Invalid Change----"
			return
		parent.add_child(elt)

	#need to use a reset button
	# have to edit parent_node binding
	def delete_item(self, node, parent_node):
		#test
		if parent_node is None:
			if type(node.obj).__name__ == "Element":
				del node.obj
				del node.children
				del node
			return

		if isinstance(node.obj, YamlStruct):
			parent_node.del_child(node)
			node_key = node.obj.key
			parent_dict = parent_node.obj
			del node.obj.parent[node.obj.key]
			#del parent_dict[node_key]

			#this case of dict with dict child
		elif isinstance(node.obj, dict):
			if isinstance(parent_node.obj, dict):
				#this is probably unsafe 
				for key, instance in parent_node.obj.items():
					if instance is node.obj:
						del parent_node.obj[key]
						break
			elif type(parent_node.obj).__name__ == "Element":
				if parent_node.obj.tag == "rosparam":
					if parent_node.obj.attrib.has_key("file"):
						del parent_node.obj.attrib["file"]
					else:
						parent_node.obj.text = ""
			parent_node.del_child(node)
			del node.obj
		elif type(node.obj).__name__ == 'Element':
			parent_node.del_child(node)
			parent_node.obj.remove(node.obj)
		else:
			return
		del node
		#this works only if an xml elt root.obj is passed
		#xml_root.remove() #deletes allchildren


	# changes written out to file
	def apply_changes(self):
		#make edits to text embedded yaml first
		for key, struct in self.file_map.items():
			if key.is_yaml:
				if isinstance(key.path, Element):
					print "this time"
					print struct
					key.path.text = yaml.dump(struct, default_flow_style=False)
					print key.path.text
				else:
					continue
			else:
				continue

		for key, struct in self.file_map.items():
			if key.is_yaml:
				if isinstance(key.path, Element):
					continue
				else:
					print "normal"
					try:
						stream = file(key.path, "w")
						yaml.dump(struct, stream, default_flow_style=False)
						stream.close()
					except IOError as e:
						print "-------" + str(key.path) + " was not edited-------"
			else:
				try:
					stream = file(key.path, "w")
					struct.write(stream)
					stream.close()
				except IOError as e:
					print "-------" + str(key.path) + " was not edited-------"
		#maps the file and whether it's yaml to the overlying data structure

	#ability to edit file map when/ before applying changes - handle with widget class

	#not currently a priority to figure out when to do this

	#yaml dicts or mapping to be equivalent to xml elt?

	def process_yaml(self, yaml_text, is_file, ptr_node = None):
		yaml_dict = {}
		currname = ""
		if is_file:
			with open(yaml_text, 'r') as stream:
				try:
					yaml_dict = yaml.load(stream)
					#currname = yaml_text
				except yaml.YAMLError as e:
					yaml_dict = {}
		else:
			yaml_dict = yaml.load(yaml_text)
			currname = ""

		#ptr_node only used for yaml embedded in an xml file
		if ptr_node is not None:
			print "worked!"
			mapper = EditableFile(ptr_node, True)
			self.file_map[mapper] = yaml_dict
		else:
			mapper = EditableFile(yaml_text, True)
			self.file_map[mapper] = yaml_dict

		fst_node = EditorNode("Yaml Top Level", yaml_dict)
		# create new object to deal with yaml (possibly including update lambda function)
		def _process_yaml_dict(this_dict, curr):
			node_list = []
			for key, instance in this_dict.items():

				name = curr + "/" + key
				if isinstance(instance, dict):
					node = EditorNode(name, instance)
					node.add_children(_process_yaml_dict(instance, name))

				else:
					struct = YamlStruct(key, instance, this_dict)
					node = EditorNode(name, struct)

				node_list.append(node)	
				#recursive call to _process_yaml_dict
				#have to add children and increment name, possibly paths
			return node_list

		fst_node.add_children(_process_yaml_dict(yaml_dict, currname))
		return [fst_node]
		#return _process_yaml_dict(yaml_dict, currname)
		#pass #returns EditorNode list
	#need to have a try and catch block at some point - probably in widget class

#parsing different datatypes because all are being loaded as a python unicode string!!!!

class YamlStruct:
	def __init__(self, key, value, parent):
		self.key = key
		self.value = value
		self.data_type = type(self.value).__name__
		self.parent = parent


	#parsing for different data types
	#or is better to write just a string?
	def update(self, x):

		try:
			if self.data_type == 'int':
				self.value = int(x)
				self.parent[self.key] =  int(x)
			elif self.data_type == 'float':
				self.value = float(x)
				self.parent[self.key] = float(x)
			elif self.data_type == 'bool':
				self.value = bool(x)
				self.parent[self.key] = bool(x)
			elif self.data_type == 'str':
				self.value = str(x)
				self.parent[self.key] = str(x)
			#not correct results, instead parse to string?
			elif self.data_type == 'list':
				self.value = str(x)
				self.parent[self.key] = str(x)
			else:
				self.value = x
				self.parent[self.key] =  x
		except:
			self.value = x
			self.parent[self.key] =  x

	

def resolve_arg(arg):
	subst_val = ""
	try:
		subst_val = roslaunch.substitution_args.resolve_args(arg)
	except roslaunch.substitution_args.ArgException:
		subst_val = arg
	return subst_val

def yaml_func(this_dict, key, x):
	this_dict[key] = x

