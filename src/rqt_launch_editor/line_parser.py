import xml.etree.ElementTree as ET

class LineParser(ET.XMLParser):
	def _start_list(self, *args, **kwargs):
		elt = super(self.__class__, self)._start_list(*args, **kwargs)
		elt.line_num = self.parser.CurrentLineNumber