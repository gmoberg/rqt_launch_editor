import xml.etree.ElementTree as ET
import os
import yaml
import io
import roslaunch

from rqt_launchtree import LaunchtreeEntryItem

class DisplayItem:
	def __init__(self, tag, attrib, update_path):
		self.tag = tag
		self.attrib = attrib
		self.update_path = update_path

	def update(self, x):
		self.update_path(x)

def parse(file):
	tree = ET.parse(file)
	root = tree.getroot()
	return process_tag(root)

# create struct from files
# be able to edit struct - edit, text, tail, attrib

def resolve_args(str):


def process_tag(root):
	tag = root.tag
	if tag = "rosparam":
		x = 5
	elif tag = "include":
		x = 5
	elif tag = "node":
		x = 5
	else:
	for child in tag.children:



class EditorTree(ET):
	def __init__(self, root):
		self.root = root
		self.children = []

	def add_to_tree(self, item):
		self.chilren.append(item)

