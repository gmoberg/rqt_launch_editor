#!/usr/bin/env python
import os
import re
import yaml
import threading
import itertools
import sys

import rospy
import rospkg
import roslaunch

from rqt_launchtree.launchtree_config import LaunchtreeConfig, LaunchtreeArg, LaunchtreeRemap, LaunchtreeParam, LaunchtreeRosparam
from rqt_launchtree.launchtree_widget import LaunchtreeEntryItem, LaunchtreeWidget

from python_qt_binding import loadUi
from python_qt_binding.QtCore import Qt, Signal
from python_qt_binding.QtWidgets import QFileDialog, QWidget, QTreeWidgetItem, QLabel, QLineEdit, QWidgetItem
from python_qt_binding.QtWidgets import QInputDialog, QWizard, QWizardPage, QGridLayout, QComboBox
from python_qt_binding.QtGui import QIcon, QColor

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

from editor_tree import EditorTree, YamlStruct, EditorNode
from wizards import YamlPage, XmlTagPage, XmlAttribPage, AddWizard

#store pieces of content in property pane, probably label & value
class PropertyWidget(QWidget):
	def __init__(self, name, value, update_path):
		super(PropertyWidget, self).__init__()

		self.setObjectName('PropertyWidget')

		self.name = name
		self.value = value
		self.update_path = update_path

		# ui file load
		self._rp = rospkg.RosPack()
		self._rp_package_list = self._rp.list()
		res_folder = os.path.join(self._rp.get_path('rqt_launchtree'), 'resource')
		ui_file = os.path.join(res_folder, 'editor_item_widget.ui')
		loadUi(ui_file, self) 

		self._label_name.setText(name)
		self._lineEdit_arg.setText(value)

	def update(self):
		self.update_path(self._lineEdit_arg.text())

	def changed(self):
		return self._lineEdit_arg.text() != self.value

class EditorWidget(LaunchtreeWidget):

	def __init__(self, context):
		super(EditorWidget, self).__init__(context)
		
		"""res_folder = os.path.join(self._rp.get_path('rqt_launchtree'), 'resource')
		ui_file = os.path.join(res_folder, 'editor_widget.ui')
		loadUi(ui_file, self)"""
		
		self.setObjectName('EditorWidget')
		self.curr_entry = None
		
		self._apply.clicked.connect(self.apply_changes)
		self._add_button.clicked.connect(self.add_entry)
		self._del_button.clicked.connect(self.delete_item)

	def ex(self):
		print "ex test"

	def apply_changes(self):
		if hasattr(self, 'editor_tree'):
			self.editor_tree.apply_changes()

	def write_tree_to_file(self):
		pass


	"""def reset(self):
		pass"""

	#should instance be the EditorNode or the object?
	def display_config_tree(self, xml_tree):
		filename = os.path.join(
			self._rp.get_path(self.package_select.currentText()),
			self.launchfile_select.currentText()
		)
		
		self.editor_tree = EditorTree(filename)
		
		def _display_config_tree(root):
			i = LaunchtreeEntryItem()
			i.setText(0, root.name)
			i.instance = root
			for child in root.children:
				i.insertChild(0, _display_config_tree(child))			
			return i

		return [_display_config_tree(self.editor_tree.getroot())]

	
	#deleting layout items may affect range function
	#maybe an if statement to create a list of property widgets 
	def launch_entry_changed(self, current, previous):
		if current is None:
			return
		
		self.curr_entry = current

		if previous is not None:

			prev_data = previous.instance.obj
			del_items = []
			layout = self.gridLayout_2
			for i in range(layout.count()):
				print i
				item = layout.itemAt(i)
				if isinstance(item, QWidgetItem):
					widg = item.widget()
					if isinstance(widg, PropertyWidget):
						del_items.append(widg)
						print i
						if widg.changed():
							print "change"
							widg.update()
			for widg in del_items:
				layout.removeWidget(widg)
				widg.setParent(None)
				widg.deleteLater()
				widg.hide()
				del widg

			
			"""for i in items:
					if i.changed():
						i.update()
			if isinstance(prev_data, YamlStruct):
	
				#check  existing widget
				print prev_data
			elif type(prev_data).__name__ == "Element":
				#iterate through existing widgets
				for key, instance in prev_data.attrib.items():
					x = 5"""


		#self.gridLayout_2.clear()
		data = current.instance.obj

		if isinstance(data, YamlStruct):
			#label = QLabel(root.name)
			"""print data.value
			value = QLineEdit()
			value.setText(str(data.value))"""
			#self.properties_content.addWidget(label)
			n = "Value: "
			v = str(data.value)
			print data.key
			print v
			print str(data.update_path)
			prop_widg = PropertyWidget(n, v, lambda t: data.update(t))
			print prop_widg.update_path
			print data.update_path
			self.gridLayout_2.addWidget(prop_widg)
		elif type(data).__name__ == "Element":
			for key, instance in data.attrib.items():
				"""print key
				print instance
				label = QLabel(str(key) + ":")
				value = QLineEdit()
				value.setText(str(instance))
				self.gridLayout_2.addWidget(label)
				self.gridLayout_2.addWidget(value)"""

				n = str(key)
				v = str(instance)
				prop_widg = PropertyWidget(n, v, lambda t: data.set(key, t))
				self.gridLayout_2.addWidget(prop_widg)


	#adding child to current selected item
	#do this for the treeWidget and the editor tree
	#use QWizard for xml elts
	#maybe the mk methods should return full wizards
	def add_dialog(self):
		#view = QQuickView()
		#container = QWidget.createWindowContainer(view)
		#min and max size with container.setMinimumSize(...)
		#container.setFocusPolicy(Qt.TabFocus)

		
		
		#can be None
		if self.curr_entry is not None:
			wizard = AddWizard(self.curr_entry)
		else:
			return

		

		#gather data on submit 

		self.verticalLayout_11.addWidget(wizard)
		wizard.setWindowTitle("Add New Entry")
		wizard.show()

	"""def mk_yaml_page(self):
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
		#print page.field("tag").toString()

		return page

	def mk_attrib_page(self):
		page = QWizardPage()
		page.setTitle("Add Entry")
		page.setSubTitle("Modify attributes of tag:")

		tag = ""
		if hasattr(page, "field"):
			tag = page.field("tag").toString()
			print tag

		layout = QGridLayout()
		label = QLabel(tag)
		layout.addWidget(label, 0, 0)
		page.setLayout(layout)

		return page"""

	def add_entry(self):
		self.add_dialog()
		"""(text, ok) = QInputDialog.getText(self,
            'Settings for %s' % self.windowTitle(),
            'Command to edit launch files (vim, gedit, ...), can accept args:',
            text = self.editor
        )"""
        """print text
        print ok
        if ok:
        	self.editor = text"""
	#how are items stored in tree
	#keep track of curr item

	#edit so that node is now the .instance
	def delete_item(self):
		curr = self.curr_entry
		parent = curr.parent()
		print parent
		if parent is not None:
			parent.removeChild(curr)
			self.editor_tree.delete_item(curr.instance, parent.instance)
		else:
			self.editor_tree.delete_item(curr.instance, None)
	#	curr.hide()
		del curr



		