import sys
import os
from python_qt_binding.QtCore import *
from python_qt_binding.QtGui import *
from python_qt_binding.QtWidgets import *
import xml.etree.ElementTree as ElementTree
from xml.etree.ElementTree import Element
from editor_tree import YamlStruct, EditorNode


#configure the file_map
class ConfigPage(QWizardPage):

	def __init__(self, file_map):
		# file_map is dict that maps
		#EditableFile to a data structure
		super(ConfigPage, self).__init__()
		self.file_map = file_map

		self.setTitle("Configure Settings")
		self.setSubTitle("Change the files to be modified")

		self.layout = QGridLayout()

		self.count = 0

		self.tracker = {}

		#create a page representing file maps
		for mapper, struct in file_map.items():
			self.count += 1
			self.tracker[self.count] = mapper
			old_path = str(mapper.path)
			label = QLabel(old_path)
			edit = QLineEdit(old_path)
			if not os.path.isfile(old_path):
				continue
			self.registerField("field" + str(self.count), edit)
			self.layout.addWidget(label, self.count - 1, 0)
			self.layout.addWidget(edit, self.count - 1, 1)

		self.setLayout(self.layout)

	#change values of file_map when page is submitted
	def validatePage(self):
		for i in range(self.count):
			j = str(self.wizard().field("field" + str(i + 1)))
			if j == self.tracker[i + 1]:
				continue
			else:
				if os.path.isfile(j):
					self.tracker[i+1].path = j 
				else:
					print "-----No Such Path Exists-----"
		return True



#wizard containing a ConfigPage
class ConfigWizard(QWizard):

	def __init__(self, file_map):
		super(ConfigWizard, self).__init__()
		self.file_map = file_map

		config_page = ConfigPage(self.file_map)
		self.addPage(config_page)


