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

from launchtree_config import LaunchtreeConfig, LaunchtreeArg, LaunchtreeRemap, LaunchtreeParam, LaunchtreeRosparam
from launchtree_widget import LaunchtreeEntryItem, LaunchtreeWidget

from python_qt_binding import loadUi
from python_qt_binding.QtCore import Qt, Signal
from python_qt_binding.QtWidgets import QFileDialog, QWidget, QTreeWidgetItem, QLabel, QLineEdit, QWidgetItem
from python_qt_binding.QtWidgets import QInputDialog, QWizard, QWizardPage, QGridLayout, QComboBox
from python_qt_binding.QtGui import QIcon, QColor

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

from editor_tree import EditorTree, YamlStruct, EditorNode
from wizards import YamlPage, XmlPage, AddWizard
from config_wizard import ConfigWizard, ConfigPage

#store pieces of content in property pane, probably label & value
class PropertyWidget(QWidget):
	def __init__(self, name, value, update_path, obj, isXml):
		super(PropertyWidget, self).__init__()

		self.setObjectName('PropertyWidget')

		self.name = name
		self.value = value
		self.update_path = update_path
		self.obj = obj
		self.isXml = isXml
	
		# ui file load
		self._rp = rospkg.RosPack()
		self._rp_package_list = self._rp.list()
		res_folder = os.path.join(self._rp.get_path('rqt_launch_editor'), 'resource')
		ui_file = os.path.join(res_folder, 'editor_item_widget.ui')
		loadUi(ui_file, self) 

		self._label_name.setText(name)
		self._lineEdit_arg.setText(value)

	def update(self):
		if self.isXml:
			self.value = self._lineEdit_arg.text()
			self.obj.attrib[self.name] = self.value
		else:
			self.value = self._lineEdit_arg.text()
			self.update_path(self._lineEdit_arg.text())

	def changed(self):
		return str(self._lineEdit_arg.text()) != str(self.value)

class EditorWidget(LaunchtreeWidget):

	def __init__(self, context):
		super(EditorWidget, self).__init__(context)
		
		"""res_folder = os.path.join(self._rp.get_path('rqt_launch_editor'), 'resource')
		ui_file = os.path.join(res_folder, 'editor_widget.ui')
		loadUi(ui_file, self)"""
		
		self.setObjectName('EditorWidget')
		self.curr_entry = None
		
		self.apply.clicked.connect(self.apply_changes)
		self._add_button.clicked.connect(self.add_dialog)
		self._del_button.clicked.connect(self.delete_item)

	def apply_changes(self):
		if hasattr(self, 'editor_tree'):
			layout = self.gridLayout_2
			for i in range(layout.count()):
				item = layout.itemAt(i)
				if isinstance(item, QWidgetItem):
					widg = item.widget()
					if isinstance(widg, PropertyWidget):
						if widg.changed():
							widg.update()

			self.editor_tree.apply_changes()


	#helper function for tree widget icon
	def get_icon(self, prop_widg):
		elt = prop_widg.instance.obj

		if type(elt).__name__ == 'Element':
			tag = elt.tag

			if tag == 'node':
				return self._icon_node
			elif tag == 'param':
				return self._icon_param
			elif tag == 'rosparam':
				return self._icon_rosparam
			elif tag == 'arg':
				return self._icon_arg
			elif tag == 'remap':
				return self._icon_remap
			else:
				return self._icon_default

		elif isinstance(elt, YamlStruct):
			return self._icon_param
		elif isinstance(elt, dict):
			return self._icon_rosparam
		else:
			return self._icon_default

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

			#icon setting
			i.setIcon(0, self.get_icon(i))
			"""if type(i.instance.obj).__name__ == 'Element':
				i.setIcon(0,
					self._icon_node if i.instance.obj.tag == 'node' else
					self._icon_param if i.instance.obj.tag == 'param' else
					self._icon_rosparam if i.instance.obj.tag == 'rosparam' else
					self._icon_arg if i.instance.obj.tag == 'arg' else
					self._icon_remap if i.instance.obj.tag == 'remamp' else
					self._icon_default)
			elif isinstance(i.instance.obj, YamlStruct):
				i.setIcon(0, self._icon_param)
			elif isinstance(i.instance.obj, dict):
				i.setIcon(0, self._icon_rosparam)
			else:
				i.setIcon(0, self._icon_default)"""

			# recursivelt add children to tree
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
				item = layout.itemAt(i)
				if isinstance(item, QWidgetItem):
					widg = item.widget()
					if isinstance(widg, PropertyWidget):
						del_items.append(widg)
						if widg.changed():
							widg.update()
							print widg.name + " was updated"
							print "with val: " + widg.value
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

		data = current.instance.obj

		if isinstance(data, YamlStruct):
			n = "Value: "
			v = str(data.value)
			prop_widg = PropertyWidget(n, v, lambda t: data.update(t), data, False)

			self.gridLayout_2.addWidget(prop_widg)
		elif type(data).__name__ == "Element":
			for key, instance in data.attrib.items():
				n = str(key)
				v = str(instance)
				print "name:" + n + "val:" + v
				#prop_widg = PropertyWidget(n, v, lambda t: data.attrib[n] = t)
				prop_widg = PropertyWidget(n, v, lambda t: data.set(n, t), data, True)
				self.gridLayout_2.addWidget(prop_widg)

	#everything is being written pkg attrib for xml!!!

	def elt_func(self, elt, key, val):
		print "this key  " + key
		elt.attrib[key] = val

	#adding child to current selected item
	#do this for the treeWidget and the editor tree
	#use QWizard for xml elts
	#maybe the mk methods should return full wizards
	#insertChild for widget side update, only when complete
	def add_dialog(self):

		#can be None
		if self.curr_entry is not None:
			self.wizard = AddWizard(self.curr_entry)
		else:
			return

		#gather data on submit 

		self.verticalLayout_11.addWidget(self.wizard)
		self.wizard.setWindowTitle("Add New Entry")
		self.wizard.setModal(True)
		self.wizard.show()
		self.wizard.accepted.connect(self.add_action)

	def add_action(self):
		self.editor_tree.add_to_tree(self.wizard.node, self.curr_entry.instance)
		i = LaunchtreeEntryItem()
		i.instance = self.wizard.node
		i.setText(0, self.wizard.node.name)
		i.setIcon(0, self.get_icon(i))
		self.curr_entry.insertChild(0, i)


	#edit so that node is now the .instance
	def delete_item(self):
		curr = self.curr_entry
		parent = curr.parent()
		if parent is not None:
			parent.removeChild(curr)
			self.editor_tree.delete_item(curr.instance, parent.instance)
		else:
			self.editor_tree.delete_item(curr.instance, None)
	#	curr.hide()
		del curr

	def configure(self):
		if not hasattr(self, 'editor_tree'):
			return
		
		self.config_wizard = ConfigWizard(self.editor_tree.file_map)
		self.verticalLayout_11.addWidget(self.config_wizard)
		self.config_wizard.setWindowTitle("Configure File Setup")
		self.config_wizard.setModal(True)
		self.config_wizard.show()

		#self.config_wizard.accepted.connect(self.config_wizard.)








		