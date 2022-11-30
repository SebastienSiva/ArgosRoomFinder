#!/usr/bin/python3

import math, sys, os, re, locale, csv, time, shutil
from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill
from openpyxl.comments import Comment
import math, sys, os, re
locale.setlocale(locale.LC_ALL, '')
from argos_timeslot import TimeSlot

argos_header_row = 1
req_argos_headers = ['CRN', 'SUBJECT', 'COURSE', 'SECTION', 'WEB_VIEW', 
	'SCHD_TYPE', 'INS_METH', 'TITLE', 'LONG_TITLE', 'PTRM', 'RESTRICTION_CODE', 
	'BLOCK_CODE', 'XLST_CODE', 'SECTION_MAX_ENRL', 'SECTION_ACTUAL_ENRL',	'BLDG',	
	'ROOM', 'BEGIN_TIME1', 'END_TIME1', 'MONDAY_IND1', 
	'TUESDAY_IND1',	'WEDNESDAY_IND1', 'THURSDAY_IND1', 'FRIDAY_IND1', 
	'SATURDAY_IND1', 'BLDG1', 'ROOM1', 'BEGIN_TIME2', 'END_TIME2', 'MONDAY_IND2',	
	'TUESDAY_IND2', 'WEDNESDAY_IND2', 'THURSDAY_IND2', 'FRIDAY_IND2',	
	'SATURDAY_IND2', 'LAST_NAME', 'FIRST_NAME']

################################SECTION CLASS###################################
class Section:
	def __init__(self, row):
		self.row = row
		self.ID = row['CRN']
		self._time_slots = None
	
	def getValue(self, heading):
		return self.row[heading]
		
	@property
	def time_slots(self):
		if self._time_slots == None:
			self.buildTimeSlots()
		return self._time_slots
		
	def getRoomValues(self, index):
		index += 1
		x = '' if index == 1 else str(index - 1)
		return (self.getValue("BLDG" + x), self.getValue("ROOM" + x))
		
	def getDayValues(self, index):
		index += 1
		suf = 'IND' + str(index)
		days = ('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY') 
		return tuple(self.getValue(d + '_' + suf) for d in days)

	def getTimeValues(self, index):
		index += 1
		return (self.getValue('BEGIN_TIME' + str(index)), 
			self.getValue('END_TIME' + str(index)))

	def buildTimeSlots(self):
		self._time_slots = []
		ptrm = self.getValue('PTRM')
		for i in range(0, 2):
			room_vals = [v for v in self.getRoomValues(i) if v != '']
			if len(room_vals) >= 2:
				room = '-'.join(room_vals)
			else:			
				room = ''.join(room_vals)

			day_str =  ''.join(self.getDayValues(i))

			beg, end = self.getTimeValues(i)
			
			self._time_slots.append(TimeSlot(ptrm, day_str, beg, end, room, i==1))
		
	def numRoomsNeeded(self, zero_room_ins_meth_list):
		i = self.getValue("INS_METH")
		if i in zero_room_ins_meth_list: return 0
		elif self.time_slots[1].hasRoomTimePart(): return 2
		else: return 1

	def isVisible(self):
		return self.getValue("WEB_VIEW") == 'Y'

	def __str__(self):
		return "%s %s-%s (%s)" % (
			self.getValue('SUBJECT'), self.getValue('COURSE'), self.getValue('SECTION'), 
			self.ID)
	
	__repr__ = __str__
		
################################SCHEDULE CLASS##################################
class Schedule:
	def __init__(self, csv_file):
		with open(csv_file) as f:
			self.rows = [r for r in csv.DictReader(f)]

		self.sections = {}
		for r in self.rows:
			self.sections[r['CRN']]= Section(r)

###################################MAIN#########################################

if __name__ == "__main__":
	s = Schedule(sys.argv[1])
	print(s.sections['20757'])


