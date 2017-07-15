import sys
from python_qt_binding.QtCore import *
from python_qt_binding.QtGui import *
from python_qt_binding.QtWidgets import *
import xml.etree.ElementTree as ElementTree
from xml.etree.ElementTree import Element
from editor_tree import YamlStruct, EditorNode

#parent is node
class YamlPage(QWizardPage):

	def __init__(self, parent):
		super(YamlPage, self).__init__()
		self.parent = parent
		self.setTitle("Add Entry")
		self.setSubTitle("Select values for a new YAML pairing:")

		self.key_label = QLabel("Key:")
		self.key_edit = QLineEdit()

		self.val_label = QLabel("Value:")
		self.val_edit = QLineEdit()

		self.registerField("key", self.key_edit)
		self.registerField("val", self.val_edit)

		layout = QGridLayout()
		layout.addWidget(self.key_label, 0, 0)
		layout.addWidget(self.key_edit, 0, 1)
		layout.addWidget(self.val_label, 1, 0)
		layout.addWidget(self.val_edit, 1, 1)
		self.setLayout(layout)

	def get_key(self):
		return str(self.field("key"))

	def get_val(self):
		return str(self.field("val"))

	def get_node(self):
		obj = YamlStruct(self.get_key(), self.get_val(), self.parent.obj)
		node = EditorNode(self.get_key(), obj)
		self.wizard().node = node
		return node

	def validatePage(self):
		self.get_node()
		return True

tags = ["launch", "node", "machine", "include", 
		"remap", "env", "param", "rosparam",
		"group", "test", "arg"]

class XmlPage(QWizardPage):
	def __init__(self):
		super(XmlPage, self).__init__()
		self.setTitle("Add Entry")
		self.setSubTitle("Create a new launch XML tag:")

		tags = ["launch", "node", "machine", "include", 
				"remap", "env", "param", "rosparam",
				"group", "test", "arg"]

		self.combo_label = QLabel("Choose Tag:")
		self.combo = QComboBox()
		self.combo.addItems(tags)

		self.count = 0

		self.button = QPushButton("Add Entry")

		self.registerField("tag", self.combo)

		self.layout = QGridLayout()
		self.layout.addWidget(self.combo_label, 0, 0)
		self.layout.addWidget(self.combo, 0, 1)
		self.layout.addWidget(self.button, 0, 2)
		self.setLayout(self.layout)

		self.button.clicked.connect(self.add_entry)

	def add_entry(self):
		self.count += 1
		key_label = QLabel("Key " + str(self.count) + ":")
		key_edit = QLineEdit()
		val_label = QLabel("Value " + str(self.count) + ":")
		val_edit = QLineEdit()

		self.registerField("key" + str(self.count), key_edit)
		self.registerField("val" + str(self.count), val_edit)

		self.layout.addWidget(key_label, self.count, 0)
		self.layout.addWidget(key_edit, self.count, 1)
		self.layout.addWidget(val_label, self.count, 2)
		self.layout.addWidget(val_edit, self.count, 3)
		self.setLayout(self.layout)
		
		return

	def get_tag(self):
		idx = self.field('tag')
		tag = str(tags[idx])
		return tag

	#return attrib dict
	def get_attrib(self):
		attrib = {}
		for i in range(self.count):
			num = i + 1
			key_str = "key" + str(num)
			val_str = "val" + str(num)
			key = str(self.field(key_str))
			val = str(self.field(val_str))
			attrib[key] = val
		return attrib

	def get_node(self):
		tag = self.get_tag()
		attrib = self.get_attrib()
		elt = Element(tag, attrib)

		name = ""

		if tag == 'launch':
			name = 'launch'
		elif tag == 'include':
			if attrib.has_key('file'):
				name = "include/" + editor_tree.resolve_arg(attrib.get("file"))
			else:
				name = 'include'
		elif tag == 'remap':
			name = 'remap'
		elif tag == 'rosparam':
			name = 'rosparam'
		elif tag == 'group':
			name = 'group'
		else:
			name = attrib['name'] if attrib.has_key('name') else tag

		node = EditorNode(name, elt)
		self.wizard().node = node
		return node


	def validatePage(self):
		self.get_node()
		print "validate"
		print self.wizard().node
		return True


class AddWizard(QWizard):

	def __init__(self, entry):
		super(AddWizard, self).__init__()
		self.entry = entry

		parent_obj = entry.instance.obj

		if isinstance(parent_obj, Element):
			"""tag_page = XmlTagPage()
			attrib_page = XmlAttribPage()
			self.addPage(tag_page)
			self.addPage(attrib_page)"""
			xml_page = XmlPage()
			self.addPage(xml_page)
		elif isinstance(parent_obj, dict):
			yaml_page = YamlPage(entry.instance)
			self.addPage(yaml_page)
		else:
			print "----Invalid Change----"
			return

		self.node = None

	def get_node(self):
		if self.node is not None:
			return self.node



		
	

