#Qt imports etc.

# is this class necessary
class PropertyWidget(QWidget):
	def __init__(self, edit_node, update_path):
		self.edit_node = edit_node
		self.update_path = update_path

	# utilize tree?