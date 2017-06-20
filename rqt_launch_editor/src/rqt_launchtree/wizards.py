"""import os
import re
import yaml
import threading
import itertools

from python_qt_binding import loadUi
from python_qt_binding.QtCore import Qt, Signal
from python_qt_binding.QtWidgets import QFileDialog, QWidget, QTreeWidgetItem, QLabel, QLineEdit, QWidgetItem, QInputDialog
from python_qt_binding.QtGui import QIcon, QColor

class CreateDialog(QWidget):

	def __init__(self, parent=None, node):
		super(CreateDialog, self).__init__(parent)"""

import sys
from python_qt_binding.QtCore import *
from python_qt_binding.QtGui import *
from python_qt_binding.QtWidgets import *
import xml.etree.ElementTree as ElementTree
from xml.etree.ElementTree import Element

class YamlPage(QWizardPage):
	def __init__(self):
		super(YamlPage, self).__init__()
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
		return self.field("key").toString()

	def get_val(self):
		return self.field("val").toString()

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

		self.layout.addWidget(key_label, self.count, 0)
		self.layout.addWidget(key_edit, self.count, 1)
		self.layout.addWidget(val_label, self.count, 2)
		self.layout.addWidget(val_edit, self.count, 3)
		self.setLayout(self.layout)

		#register fields?
		
		return

	def get_tag(self):
		pass

	def get_attrib(self):
		pass




class XmlTagPage(QWizardPage):
	def __init__(self):
		super(XmlTagPage, self).__init__()
		self.setTitle("Add Entry")
		self.setSubTitle("Select tag type for a new Launch XML Element:")

		self.combo_label = QLabel("Choose Tag:")
		self.combo = QComboBox()

		tags = ["launch", "node", "machine", "include", 
				"remap", "env", "param", "rosparam",
				"group", "test", "arg"]

		self.combo.addItems(tags)

		layout = QGridLayout()
		layout.addWidget(self.combo_label, 0, 0)
		layout.addWidget(self.combo, 0, 1)
		self.setLayout(layout)

		self.registerField("tag", self.combo)


	def get_tag(self):
		return self.field("tag").toString()


tags = ["launch", "node", "machine", "include", 
		"remap", "env", "param", "rosparam",
		"group", "test", "arg"]

class XmlAttribPage(QWizardPage):
	tags = ["launch", "node", "machine", "include", 
			"remap", "env", "param", "rosparam",
			"group", "test", "arg"]

	def __init__(self):
		super(XmlAttribPage, self).__init__()
		self.setTitle("Add Entry")
		self.setSubTitle("Modify attributes of tag:")
		


	def initializePage(self):
		idx = self.field("tag")
		tag = tags[idx]
		layout = QGridLayout()
		self.label = QLabel(tag)
		layout.addWidget(self.label, 0, 0)
		self.setLayout(layout)

		#if tag == "node":


	

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
			yaml_page = YamlPage()
			self.addPage(yaml_page)
		else:
			print "----Invalid Change----"
			return