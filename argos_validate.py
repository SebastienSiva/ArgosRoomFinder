#!/usr/bin/python3

from argos_schedule import *
import argos_rooms as rooms
from argos_issue import Issue

def getRoomTimeSlots(sched, room):
	return timeslots_by_room[room] if room in timeslots_by_room else []

def getFreeRooms(sched, searchSlot, searchSub, searchCourse):
	"""returns list of display strings"""
	
	room_sets = [set(), set(), set()]
	room_set_strings = ['SAME COURSE', 'SAME SUBJECT', '']
	for room_name in rooms.all_rooms:
		timeslots = getRoomTimeSlots(sched, room_name)
		for slot in timeslots:
			if slot.overlapTimes(searchSlot): break
		else: # NO BREAK IN LOOP
			# ROOM IS AVAILABLE, CHECK ALL COURSES IN THIS ROOM
			room_set_index = 2 # other
			for slot in timeslots:
				sec = section_by_timeslot[slot]
				if sec.getValue('SUBJECT') == searchSub:
					if sec.getValue('COURSE') == searchCourse:
						room_set_index = 0
						break
					else: 
						room_set_index = 1
			room_sets[room_set_index].add(room_name)
				
	output_strs = []
	for i in range(len(room_sets)):
		for r in sorted(room_sets[i]):
			output_strs.append("%s\t%s\t%s" % (
				room_set_strings[i], rooms.all_rooms[r], rooms.all_rooms[r].discipline))
	return output_strs 

def validate_schedule(sched):
	
	issues = []

	global section_by_timeslot; section_by_timeslot = {}
	global timeslots_by_room; timeslots_by_room = {}
	
	# BUILD SECTIONS BY TIMESLOT DICTIONARY
	crosslist_codes = set()
	for sec in sched.sections.values():
		for ts in sec.time_slots:
			section_by_timeslot[ts] = sec

	# BUILD TIMESLOTS BY ROOM DICTIONARY
	for ts in section_by_timeslot:
		if ts.room not in timeslots_by_room:
			timeslots_by_room[ts.room] = []
		timeslots_by_room[ts.room].append(ts)

	for sec in sched.sections.values():
		for i in range(sec.numRoomsNeeded()):
			slot = sec.time_slots[i]

			if slot.room and slot.room not in rooms.all_rooms:
				issues.append(Issue(f"Room '{slot.room}' unknown, marking None.", sec))
				slot.room = None
			
			msg = None
			if slot.room:				
				max_enrl = int(sec.getValue('SECTION_MAX_ENRL'))
				room_cap = rooms.all_rooms[slot.room].cap
				try:
					if max_enrl > int(room_cap):
						msg = 'Room %s too small for max enrollment %s.' % (slot.room, max_enrl)
				except ValueError:
					msg = 'Room %s cap is unknown.' % (slot.room)
			else:
				msg = 'Room %s required for %ssection coded SCHD_TYPE/INS_METH: %s/%s:' % (
					(i+1), '' if sec.isVisible() else 'HIDDEN ', 
					sec.getValue("SCHD_TYPE"), sec.getValue("INS_METH"))

			if msg:
				issue = Issue(msg, sec)
				issues.append(issue)
				for r in getFreeRooms(sched, slot, sec.getValue('SUBJECT'), sec.getValue('COURSE')):
					issue.sec_room_options.append(r)
	
	return issues	

###################################MAIN#########################################
if __name__ == "__main__":
	searchSlot = None
	display_room_options = False
	#TODO update this for general use with sys arg path.
	ref_dir = '/Users/ssiva/Scheduling/Reference_Files'
	rooms.readRoomFile(ref_dir)
	if len(sys.argv) == 8:
		searchSub, searchCourse = sys.argv[2:4]
		ptrm, days, start, end = sys.argv[4:8]
		searchSlot = TimeSlot(int(ptrm), days, int(start), int(end), None, None, None)
		
	elif len(sys.argv) == 2:
		pass

	elif len(sys.argv) == 3 and sys.argv[2] == 'SHOW_ROOM_OPTIONS':
		display_room_options = True

	else:
		print(os.path.basename(sys.argv[0]), 'SST.xlsx')
		print(os.path.basename(sys.argv[0]), 'SST.xlsx', 'SHOW_ROOM_OPTIONS')
		print(os.path.basename(sys.argv[0]), 'SST.xlsx', 'subj', 'course', 
			'ptrm', 'days', 'start', 'end')
		sys.exit(0)

	master = SST_Schedule(sys.argv[1])
	ScheduleMaster.setSchedules(master)
	master.load_sections()
	
	validate_schedule(master, False, display_room_options)
	if searchSlot:
		print("SEARCH OPTIONS")
		for s in getFreeRooms(master, searchSlot, searchSub, searchCourse):
				print("\t%s" % s)

	
	ScheduleMaster.write_files()
	print("SUCCEEDED!")
###############################END MAIN#########################################

