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
from python_qt_binding.QtWidgets import QFileDialog, QWidget, QTreeWidgetItem, QLabel, QLineEdit, QWidgetItem, QFileDialog
from python_qt_binding.QtWidgets import QInputDialog, QWizard, QWizardPage, QGridLayout, QComboBox, QSizePolicy, QPushButton
from python_qt_binding.QtGui import QIcon, QColor

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

from editor_tree import EditorTree, YamlStruct, EditorNode
from wizards import YamlPage, XmlPage, AddWizard
from config_wizard import ConfigWizard, ConfigPage



#widget that stores information about a specific XML or YAML tag
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

		#make widget
		self._label_name.setText(name)
		self._lineEdit_arg.setText(value)


	#change value in underlying native data structure
	def update(self):
		if self.isXml:
			self.value = self._lineEdit_arg.text()
			self.obj.attrib[self.name] = self.value
		else:
			self.value = self._lineEdit_arg.text()
			self.update_path(self._lineEdit_arg.text())

	def changed(self):
		return str(self._lineEdit_arg.text()) != str(self.value)


#widget that creates overlying UI of application
#extends the UI and some visual elements from LaunchtreeWidget
class EditorWidget(LaunchtreeWidget):

	def __init__(self, context):
		super(EditorWidget, self).__init__(context)
		
		self.setObjectName('EditorWidget')
		self.curr_entry = None
		
		self.gridLayout_2.setAlignment(Qt.AlignTop)

		#set signals
		self.apply.clicked.connect(self.apply_changes)
		self._add_button.clicked.connect(self.add_dialog)
		self._del_button.clicked.connect(self.delete_item)
		self.save_as.clicked.connect(self.configure)


	#write changes to file
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

	#generate tree widget
	def display_config_tree(self, xml_tree):
		filename = os.path.join(
			self._rp.get_path(self.package_select.currentText()),
			self.launchfile_select.currentText()
		)
		
		self.editor_tree = EditorTree(filename)
		

		def _display_config_tree(root):
			#create widget
			i = LaunchtreeEntryItem()
			i.instance = root
			
			if type(i.instance.obj).__name__ == 'Element':
				i.setText(0, root.name + '  (' + str(i.instance.obj.line_num) + ')') 
			else:
				i.setText(0, root.name)
			
			i.setIcon(0, self.get_icon(i))
			

			# recursively add children to tree
			for child in root.children:
				i.addChild(_display_config_tree(child))			
			return i


		return [_display_config_tree(self.editor_tree.getroot())]


	#extend launchtree method to clear property pane	
	def load_launchfile(self):
		super(EditorWidget, self).load_launchfile()
		self.clear_prop_pane()
		return

	#delete all PropertyWidgets in property pane
	def clear_prop_pane(self):
		if not hasattr(self, 'curr_entry'):
			return
		if self.curr_entry is not None:
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
			for widg in del_items:
				layout.removeWidget(widg)
				widg.setParent(None)
				widg.deleteLater()
				widg.hide()
				del widg



	#extending QTreeWidget method
	#executed when a new tree item is selected
	def launch_entry_changed(self, current, previous):
		if current is None:
			return
		
		self.curr_entry = current

		# log changes to data structure if applicable
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
			for widg in del_items:
				layout.removeWidget(widg)
				widg.setParent(None)
				widg.deleteLater()
				widg.hide()
				del widg

		data = current.instance.obj

		#generate new property widgets for selected element

		size_pol = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

		if isinstance(data, YamlStruct):

			n = "Value: "
			v = str(data.value)
			prop_widg = PropertyWidget(n, v, lambda t: data.update(t), data, False)
			prop_widg.setSizePolicy(size_pol)
			self.gridLayout_2.addWidget(prop_widg)

		elif type(data).__name__ == "Element":

			for key, instance in data.attrib.items():
				n = str(key)
				v = str(instance)
				prop_widg = PropertyWidget(n, v, lambda t: data.set(n, t), data, True)
				prop_widg.setSizePolicy(size_pol)
				self.gridLayout_2.addWidget(prop_widg)


	# generate interface to add a new element
	def add_dialog(self):

		#can be None
		if self.curr_entry is not None and not isinstance(self.curr_entry.instance.obj, YamlStruct):
			self.wizard = AddWizard(self.curr_entry)
		else:
			return

		#gather data on submit 
		self.wizard.setWindowTitle("Add New Entry")
		self.wizard.setWindowModality(Qt.ApplicationModal)
		self.wizard.show()
		self.wizard.accepted.connect(self.add_action)

	# called when add_wizard is submitted, changes data structures
	def add_action(self):
		self.editor_tree.add_to_tree(self.wizard.node, self.curr_entry.instance)
		i = LaunchtreeEntryItem()
		i.instance = self.wizard.node
		i.setText(0, self.wizard.node.name)
		i.setIcon(0, self.get_icon(i))
		#self.curr_entry.insertChild(0, i)
		self.curr_entry.addChild(i)

	#delete selected XML or YAML item from widget
	def delete_item(self):
		curr = self.curr_entry
		parent = curr.parent()

		#deleting launch tag creates invalid launch XML
		if hasattr(curr.instance.obj, "tag"):
			if curr.instance.obj.tag == "launch":
				print "-----Launch tag cannot be deleted-----"
				return

		if parent is not None:
			parent.removeChild(curr)
			self.editor_tree.delete_item(curr.instance, parent.instance)
		else:
			self.editor_tree.delete_item(curr.instance, None)
		del curr
		return

	#configue files to writes changes to
	def configure(self):
		if not hasattr(self, 'editor_tree'):
			return
		
		self.config_wizard = ConfigWizard(self.editor_tree.file_map)
		#self.verticalLayout_11.addWidget(self.config_wizard)
		self.config_wizard.setWindowTitle("Configure File Setup")
		self.config_wizard.setWindowModality(Qt.ApplicationModal)
		self.config_wizard.resize(850, 100)
		self.config_wizard.show()
		
		#filename = QFileDialog.getSaveFileName(self)
