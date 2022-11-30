class Issue:
	def __init__(self, msg, section):
		self.msg = msg
		self.sec = section
		self.sec_room_options = []
	
	def get_sec_shortname(self):
		subj = self.sec.getValue('SUBJECT')
		course = self.sec.getValue('COURSE')
		sec_num = self.sec.getValue('SECTION')
		return "%s %s-%s" % (subj, course, sec_num)

	def has_room_options(self):
		return len(self.sec_room_options) > 0
	
	def __str__(self):
		return str(self.sec) + " Msg: " + self.msg

