#!/usr/bin/python3

class TimeSlot:
	def __init__(self, ptrm, days, start, end, room, isLab):
		self.room = room
		self.ptrm = ptrm
		self.days = days
		self.start = start
		self.end = end
		self.isLab = isLab

	def hasRoomTimePart(self):
		return self.room or self.days or self.start or self.end

	def hasTime(self):
		return self.ptrm and self.days and self.start and self.end
			
	def __overlap_ptrms(self, other_ptrm):
		# 1 is full semester, all other values represent mutually exclusive dates
		return (1 in (self.ptrm, other_ptrm)) or (self.ptrm == other_ptrm)
	
	def __overlap_days(self, other_days):
		for d in self.days:
			if d in other_days:
				return True
		return False
	
	def __overlap_times(self, other_time):
		return self.start <= other_time <= self.end

	def overlapTimes(self, other):
		if not self.__overlap_ptrms(other.ptrm): return False
		if not self.__overlap_days(other.days): return False

		for t in (self.start, self.end):
			if other.__overlap_times(t): return True

		for t in (other.start, other.end):
			if self.__overlap_times(t): return True

		return False

	def overlapRoomTimes(self, other):
		return (self.room == other.room and self.overlap_times(other))
	
	def containsTime(self, ptrm, day, time):
		return (self.__overlap_ptrms(ptrm) and
			self.__overlap_days(day) and self.__overlap_times(time))
	
	def equalTo(self, other):
		return str(self) == str(other)

	def __str__(self):
		return "PTRM %s %s%s %s %s-%s" % (self.ptrm, 
		'LAB ' if self.isLab else '', self.room[0:6] if self.room else '', 
		self.days, self.start, self.end)
	__repr__ = __str__

