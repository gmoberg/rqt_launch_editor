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

class YamlPage(QWizardPage):
	def __init__(self):
		super.__init__()
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

class XmlTagPage(QWizardPage):
	def __init__(self):
		super.__init__()
		page.setTitle("Add Entry")
		page.setSubTitle("Select tag type for a new Launch XML Element:")



		self.combo_label = QLabel("Choose Tag:")
		self.combo = QComboBox()

		tags = ["launch", "node", "machine", "include", 
				"remap", "env", "param", "rosparam",
				"group", "test", "arg"]

		self.combo.addItems(tags)

		layout = QGridLayout()
		layout.addWidget(combo_label, 0, 0)
		layout.addWidget(combo, 0, 1)
		page.setLayout(layout)

		page.registerField("tag", self.combo)

		return page

	










	def add_dialog(self):
		#view = QQuickView()
		#container = QWidget.createWindowContainer(view)
		#min and max size with container.setMinimumSize(...)
		#container.setFocusPolicy(Qt.TabFocus)

		wizard = QWizard()
		
		#can be None
		if hasattr(self, 'curr_entry'):
			parent_obj = self.curr_entry.instance.obj
		else:
			return

		#gather data on submit 
		if isinstance(parent_obj, Element):
			#wizard.addPage(self.mk_tag_page())
			#wizard.addPage(self.mk_attrib_page())
			wizard = self.mk_xml_wiz()
		elif isinstance(parent_obj, YamlStruct):
			#is this invalid
			print "----Invalid Change----"
			return
		elif isinstance(parent_obj, dict):
			wizard.addPage(self.mk_yaml_page())

		self.verticalLayout_11.addWidget(wizard)
		wizard.setWindowTitle("Add New Entry")
		wizard.show()

	def mk_yaml_page(self):
		page = QWizardPage()
		page.setTitle("Add Entry")
		page.setSubTitle("Select values for a new YAML pairing:")

		key_label = QLabel("Key:")
		key_edit = QLineEdit()

		val_label = QLabel("Value:")
		val_edit = QLineEdit()

		layout = QGridLayout()
		layout.addWidget(key_label, 0, 0)
		layout.addWidget(key_edit, 0, 1)
		layout.addWidget(val_label, 1, 0)
		layout.addWidget(val_edit, 1, 1)
		page.setLayout(layout)

		return page

	def mk_xml_wiz(self):
		wizard = QWizard()
		page1 = QWizardPage()
		page1.setTitle("Add Entry")
		page1.setSubTitle("Select tag type for a new Launch XML Element:")
		
		combo_label = QLabel("Choose Tag:")
		combo = QComboBox()

		tags = ["launch", "node", "machine", "include", 
				"remap", "env", "param", "rosparam",
				"group", "test", "arg"]

		combo.addItems(tags)

		layout1 = QGridLayout()
		layout1.addWidget(combo_label, 0, 0)
		layout1.addWidget(combo, 0, 1)
		page1.setLayout(layout1)

		page1.registerField("tag", combo)

		page2 = QWizardPage()
		page2.setTitle("Add Entry")
		page2.setSubTitle("Modify attributes of tag:")
		tag = page1.field("tag").toString()
		print tag

		layout2 = QGridLayout()
		label = QLabel(tag)
		layout2.addWidget(label, 0, 0)
		page.setLayout(layou2t)

		wizard.addPage(page1)
		wizard.addPage(page2)
		return wizard


	def mk_tag_page(self):
		page = QWizardPage()
		page.setTitle("Add Entry")
		page.setSubTitle("Select tag type for a new Launch XML Element:")
		
		combo_label = QLabel("Choose Tag:")
		combo = QComboBox()

		tags = ["launch", "node", "machine", "include", 
				"remap", "env", "param", "rosparam",
				"group", "test", "arg"]

		combo.addItems(tags)

		layout = QGridLayout()
		layout.addWidget(combo_label, 0, 0)
		layout.addWidget(combo, 0, 1)
		page.setLayout(layout)

		page.registerField("tag", combo)

		return page

	def mk_attrib_page(self):
		page = QWizardPage()
		page.setTitle("Add Entry")
		page.setSubTitle("Modify attributes of tag:")
		tag = page.field("tag").toString()
		print tag

		layout = QGridLayout()
		label = QLabel(tag)
		layout.addWidget(label, 0, 0)
		page.setLayout(layout)

		return page