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

def validate_schedule(sched, zero_room_ins_meth_list = ['E', '55', '81']):
	
	issues = []

	global section_by_timeslot; section_by_timeslot = {}
	global timeslots_by_room; timeslots_by_room = {}
	
	# BUILD SECTIONS BY TIMESLOT DICTIONARY
	crosslist_codes = set()
	for sec in sched.sections.values():
		for ts in sec.time_slots:
			if ts.hasTimePart() and ts.missingTimePart():
				raise Exception("\nINCOMPLETE DAYS/TIME IN " + 
					('LAB' if ts.isLab else '') + f" TIMESLOT.\nSECTION: {sec}")
		
			section_by_timeslot[ts] = sec

	# BUILD TIMESLOTS BY ROOM DICTIONARY
	for ts in section_by_timeslot:
		if ts.room not in timeslots_by_room:
			timeslots_by_room[ts.room] = []
		timeslots_by_room[ts.room].append(ts)

	for sec in sched.sections.values():
		for i in range(sec.numRoomsNeeded(zero_room_ins_meth_list)):
			slot = sec.time_slots[i]

			if slot.room and slot.room not in rooms.all_rooms:
				issues.append(Issue(f"Room '{slot.room}' unknown, leaving blank." + 
					"\nConsider adding it to Rooms.xlsx", sec))
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
				msg += '\nTIMESLOT: %s %s-%s (ptrm %s)' % (slot.days, slot.start, slot.end, slot.ptrm)

			if msg:
				issue = Issue(msg, sec)
				issues.append(issue)
				for r in getFreeRooms(sched, slot, sec.getValue('SUBJECT'), sec.getValue('COURSE')):
					issue.sec_room_options.append(r)
	
	return issues

###################################MAIN#########################################
if __name__ == "__main__":
	searchSlot = None
	ex_file = "'CourseSchedule.csv'"
	if len(sys.argv) == 9:
		searchSub, searchCourse = sys.argv[3:5]
		ptrm, days, start, end = sys.argv[5:9]
		searchSlot = TimeSlot(ptrm, days, start, end, None, False)
	elif len(sys.argv) == 3:
		pass
	else:
		print('py ' + os.path.basename(sys.argv[0]), ex_file, 'Reference_Folder')
		print('py ' + os.path.basename(sys.argv[0]), ex_file, 'Reference_Folder', 'subj', 
			'course', 'ptrm', 'days', 'start', 'end')
		sys.exit(0)

	rooms.readRoomFile(sys.argv[2])

	sched = Schedule(sys.argv[1])	
	issues = validate_schedule(sched)
	
	if searchSlot:
		print('\n'.join(getFreeRooms(sched, searchSlot, searchSub, searchCourse)))
	else:
		for i in issues:
			print(i)
			if i.has_room_options():
				print("\t" + '\t\n'.join(i.sec_room_options))
			
	
	
###############################END MAIN#########################################

