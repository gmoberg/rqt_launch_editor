import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
import os
import yaml
import io
import roslaunch
from ast import literal_eval
from line_parser import LineParser

"""
How the editor works:
	1. Use XML and YAML libraries to parse files
	   into trees and dicts.
	2. EditorTree makes a connected datatype that is 
	   edited by widget events (underlying dicts and
	   XML trees are edited in the process)
	3. When changes are applied, changes in XML trees
	   and YAML dicts are written to the appropriate 
	   files (user can change these files with configuration)
"""


#data class used to make a dictionary of files and datastructures
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


#underlying datastructure of tree widget
class EditorTree:

	def __init__(self, launch_file):
		self.launch_file = launch_file
		self.xtree = ET.parse(launch_file, parser=LineParser())
		self.xroot = self.xtree.getroot()

		self.editable_root = EditableFile(self.launch_file, False)
		self.file_map = {self.editable_root: self.xtree}
		self.edit_list = []

		self.file_node_map = {}

		#initialize tree structure
		self.struct = self.create()

	#create an Editor tree from an XML file
	def create(self):
		
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

			#rosparam and include need special treatment
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
					if self.in_map(subst_val):
						node.add_child(self.file_node_map[subst_val])

					else:
						tree2 = ET.parse(subst_val, parser=LineParser())
						root2 = tree2.getroot()
						new_node = _create(root2, False)
						node.add_child(new_node)
						#node.add_child(_create(root2, False))
						f = EditableFile(subst_val, False)
						self.file_map[f] = tree2
						self.file_node_map[subst_val] = new_node

			#recursively add child nodes
			for child in xml_root:
				node.add_child(_create(child, False))

			if first_time:
				self.root = node

			return node

		return _create(self.xroot, True) 

	#returns the root of the tree
	def getroot(self):
		return self.root

	#add an element to the tree as a child
	#of a already existing parent element
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
				print "----Invalid Change----"
				return
			elif isinstance(elt.obj, YamlStruct):
				parent.obj[elt.obj.key] = elt.obj.value
			else:
				print "----Invalid Change----"
				return
		else:
			print "----Invalid Change----"
			return
			
		parent.add_child(elt)

	#delete currently selcted item
	def delete_item(self, node, parent_node):
		#deleting top level launch tag deletes whole file
		if parent_node is None:
			if type(node.obj).__name__ == "Element":
				if node.obj.tag == "launch":
					print "-----Launch tag cannot be deleted-----"
				else:
					del node.obj
					del node.children
					del node
			return

		if isinstance(node.obj, YamlStruct):
			parent_node.del_child(node)
			node_key = node.obj.key
			parent_dict = parent_node.obj
			del node.obj.parent[node.obj.key]
			
		elif isinstance(node.obj, dict):
			if isinstance(parent_node.obj, dict):

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
			if node.obj.tag == "launch":
				print "-----Launch tag cannot be deleted-----"
				return
			else:
				parent_node.del_child(node)
				parent_node.obj.remove(node.obj)
		else:
			return
		del node



	# changes written out to file
	def apply_changes(self):

		#make edits to text embedded yaml first(e.g rosparam.text attribute)
		for key, struct in self.file_map.items():
			if key.is_yaml:
				if isinstance(key.path, Element):
					key.path.text = yaml.dump(struct, default_flow_style=False)
				else:
					continue
			else:
				continue

		#use file map to write changes to files
		for key, struct in self.file_map.items():
			if key.is_yaml:
				if isinstance(key.path, Element):
					continue
				else:
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

	#integrate yaml text as part of the editor tree
	def process_yaml(self, yaml_text, is_file, ptr_node = None):
		yaml_dict = {}
		currname = ""
		if is_file:
			with open(yaml_text, 'r') as stream:
				try:
					yaml_dict = yaml.load(stream)
				except yaml.YAMLError as e:
					yaml_dict = {}
		else:
			yaml_dict = yaml.load(yaml_text)
			currname = ""

		#ptr_node only used for yaml embedded in an xml file
		if ptr_node is not None:
			mapper = EditableFile(ptr_node, True)
			self.file_map[mapper] = yaml_dict
		else:
			if self.in_map(yaml_text):
				return [self.file_node_map[yaml_text]]

			mapper = EditableFile(yaml_text, True)
			self.file_map[mapper] = yaml_dict

		fst_node = EditorNode("Yaml Top Level", yaml_dict)

		# create new object to deal with yaml
		def _process_yaml_dict(this_dict, curr):
			node_list = []
			for key, instance in this_dict.items():

				#recursive call to _process_yaml_dict
				#have to add children and increment name

				name = curr + "/" + key
				if isinstance(instance, dict):
					node = EditorNode(name, instance)
					node.add_children(_process_yaml_dict(instance, name))

				else:
					struct = YamlStruct(key, instance, this_dict)
					node = EditorNode(name, struct)

				node_list.append(node)	

			return node_list

		fst_node.add_children(_process_yaml_dict(yaml_dict, currname))
		if ptr_node is None:
			self.file_node_map[yaml_text] = fst_node
		return [fst_node]

	#checks whether a path is already in the file map
	def in_map(self, path):
		for key in self.file_map.keys():
			if key.path == path:
				return True
		return False
		

#object representing a key/value pairing in YAML
class YamlStruct:
	def __init__(self, key, value, parent):
		self.key = key
		self.value = value
		self.data_type = type(self.value).__name__
		self.parent = parent


	# update the value of a YamlStruct
	def update(self, x):

		try:
			if self.data_type == 'int':
				self.value = int(x)
				self.parent[self.key] =  int(x)
			elif self.data_type == 'float':
				self.value = float(x)
				self.parent[self.key] = float(x)
			elif self.data_type == 'bool':
				"""self.value = bool(x)
				self.parent[self.key] = bool(x)"""
				if str(x) == 'true':
					self.value = True
					self.parent[self.key] = True
				elif str(x) == 'false':
					self.value = False
					self.parent[self.key] = False
				else:
					self.value = bool(x)
					self.parent[self.key] =  bool(x)
			elif self.data_type == 'str':
				self.value = str(x)
				self.parent[self.key] = str(x)

			#lists were not being parsed correctly by QT
			elif self.data_type == 'list':
				val = literal_eval(x)
				self.value = val
				self.parent[self.key] = val
			else:
				self.value = x
				self.parent[self.key] =  x
		except:
			self.value = x
			self.parent[self.key] =  x

	
#resolve substitution args of an element
def resolve_arg(arg):
	subst_val = ""
	try:
		subst_val = roslaunch.substitution_args.resolve_args(arg)
	except roslaunch.substitution_args.ArgException:
		subst_val = arg
	return subst_val

