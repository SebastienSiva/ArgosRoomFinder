import os, errno, sys, ast, json, webbrowser, shutil, subprocess, traceback
from datetime import datetime
from collections import OrderedDict
import PySimpleGUI as sg
from appdirs import user_data_dir
import argos_rooms as rooms
from argos_schedule import *
from argos_room_finder import validate_schedule

class IssueTable:
	def __init__(self):
		self.reset()
			
	def reset(self):
		self.issue_index = 0
		self.issue_list = []
		self.processed = False
	
	def get_current_issue(self):
		issue = None
		if self.processed and len(self.issue_list) > self.issue_index:
			issue = self.issue_list[self.issue_index]
		return issue

	def remove_current_issue(self):
		del self.issue_list[self.issue_index]
		self.adjust_index()

	def adjust_index(self):
		self.issue_index = 0 if len(self.issue_list) == 0 else (
			self.issue_index % len(self.issue_list))

class ArgosRoomFindGUI:

	def __init__(self):
	
		self.default_data_dir = user_data_dir("ArgosRoom", "Siva")
		if not os.path.exists(self.default_data_dir): os.makedirs(self.default_data_dir)
		self.json_file = os.path.join(self.default_data_dir, 'argos_room.json')
		if os.path.exists(self.json_file):
			with open(self.json_file) as f: self.json = json.load(f)		
		else:
			self.install_app()
		self.init_links()
		self.issue_table = IssueTable()

	def install_app(self):
		# BRAND NEW JSON FILE
		self.json = {
			'DataFolder': self.default_data_dir,
			'RoomsXLFile': None,
			'Argos_URL':'https://argos.ggc.edu',
			'Argos_FILE_BASE_NAME':'Course Schedule Dashboard 2.0 - Dashboard - CrseSch_MC_CourseSchedule',
			'Banner_URL':'https://ggc.gabest.usg.edu/applicationNavigator/seamless',
			'SemesterList':[],
			'CurrentSemester':None,
			'Semesters':{},
			'zero_room_ins_meth_list':['E', '55', '81']
		}
		self.update_json()
	
	def update_json(self):
		with open(self.json_file, 'w') as json_file: 
			json.dump(self.json, json_file, indent = 4, sort_keys=True)
	
	def current_sem_json(self):
		if self.json['CurrentSemester'] == None:
			raise Exception("Current Semester Not Set!")
		if self.json['CurrentSemester'] not in self.json['Semesters']:
			self.json['Semesters'][self.json['CurrentSemester']] = {}
		
		return self.json['Semesters'][self.json['CurrentSemester']]

#####################LINKS#######################
	def init_links(self):
		self.std_links = OrderedDict()
		self.std_links['-URL Argos-'] = ['Argos', self.json['Argos_URL']]
		self.std_links['-URL Banner-'] = ['Banner Tools', self.json['Banner_URL']]
		self.std_links['-FILE Rooms-'] = ['Rooms.xlsx', self.json['RoomsXLFile']]

	def create_link_text_boxes(self, links):
		layout = []
		for k, v in links.items():
			layout.append(sg.pin(self.create_link(v[0], k)))
		return layout		

	def update_link_text_boxes(self, links):
		for k, v in links.items():
			self.main_window[k].update(v[0], visible=(v[1]!=None))

#####################GET ROOM XL#######################
	def _get_roomxl_file(self, init_path):
		window = self.create_window(
			'Rooms.xlsx File Required',
			[
				[
					sg.In(init_path, size=(50, 1), key='-roomxl_file-'),			
					sg.FileBrowse(initial_folder = init_path, 
						file_types=(("Excel File", "*.xlsx"),))
				],
				[sg.Push(), sg.Button('Ok')]
			]
		)
		while True:
			event, values = window.read()
			if event == sg.WIN_CLOSED:
				return False
			elif event == 'Ok':
				if os.path.isfile(values['-roomxl_file-']):
					self.json['RoomsXLFile'] = values['-roomxl_file-']
					self.update_json()
					window.close()
					return True
				else:
					self.error_popup('That is not a valid Excel file...')
			elif event == 'Cancel':
				window.close()
				return False

	def get_roomxl_file(self):
		init_path = self.json['RoomsXLFile'] or os.path.expanduser('~')
		#keep popping up until file selected.
		while not self._get_roomxl_file(init_path): continue
		self.std_links['-FILE Rooms-'] = ['Rooms.xlsx', self.json['RoomsXLFile']]

#####################Semesters#######################
	def add_new_semester(self):
		sem_list = self.json['SemesterList']
		window = self.create_window(
			'New Semester' + (' Required' if len(sem_list) == 0 else ''),
			[
				[sg.Text("New Semester Name"), sg.In('Spring 2022', key='-new_sem-')],
				[sg.Push(), sg.Button('Ok'), sg.Button('Cancel')]
			]
		)
		
		while True:
			event, values = window.read()
			if event == sg.WIN_CLOSED:
				return
			elif event == 'Ok':
				sem_name = values['-new_sem-']
				if sem_name in sem_list:
					self.error_popup('Semester Name Already Exists!')
				else:
					self.json['SemesterList'].append(sem_name)
					self.json['CurrentSemester'] = sem_name
					self.current_sem_json()['IGNORED_ISSUES'] = {}
					self.update_json()
					window.close()
					return
			elif event == 'Cancel':
				window.close()
				return

	def sem_list_menu_items(self):
		return self.json['SemesterList'] + ['Add New...']
	
	def create_semester_frame(self):
		while len(self.json['SemesterList']) == 0:
			self.add_new_semester()

		menu = sg.Combo(self.sem_list_menu_items(),
			default_value=self.json['CurrentSemester'], key='-sem_chg-', 
			readonly=True, enable_events=True)
		
		return ([sg.Text('Semester:'), menu, sg.Push(), sg.Text('Links: ')] + 
			self.create_link_text_boxes(self.std_links))
			
	def process_semester_frame(self, event, values):
		if event == '-sem_chg-':
			if values['-sem_chg-'] == "Add New...":
				self.add_new_semester()
				self.main_window['-sem_chg-'].update(values=self.sem_list_menu_items())
				self.main_window['-sem_chg-'].update(value=self.json['CurrentSemester'])
			else:
				self.json['CurrentSemester'] = values['-sem_chg-']
				self.update_json()
				
				self.issue_table.reset()
				self.update_argos_tab()
			
#####################ARGOS TAB#######################
	def create_argos_tab(self):
		file_button_layout = [
			[sg.Column([[
				sg.Text('', key='-argos_file_timestamp-'),
				sg.In('', key='-argos_file-', visible=False, enable_events=True), 
				sg.Push(),
				sg.FileBrowse("Get New File", target='-argos_file-', 
					initial_folder = os.path.expanduser('~/Downloads')), 
				sg.Button('Refresh from Downloads', key='-argos_refresh-')
				]], key='-argos_col_file_buttons-', visible=True, expand_x=True)
			]
		]
		
		issue_counter_layout = [
			[sg.Push(), 
				sg.pin(sg.Text("◀", key='-argos_prev-', enable_events=True)), 
				sg.pin(sg.Text('ISSUES', key='-argos_issue_counter-')), 
				sg.pin(sg.Text("▶", key='-argos_next-', enable_events=True)),
			sg.Push()],
		]
			
		multiline_layout = [
			[sg.Multiline('Stuff', disabled=True, no_scrollbar=True, 
					size=(80, 15), key='-argos_issue_msg-')]  			
		]
		
		issue_button_layout = [
			[sg.Sizer(200, 0)],
			[sg.Button('IGNORE ONCE', disabled_button_color='light grey', key='-argos_ignore_once-')], 
			[sg.Button('IGNORE ALWAYS', disabled_button_color='light grey', key='-argos_ignore_always-')],
			[sg.Col([
				[sg.Text('View Room Options:')],
				[sg.Push(), sg.pin(sg.Button('FAKE 4400-5', key='-argos_room0-', s=13)), sg.Push()]
			], expand_x = True, key='-argos_room_opt_col-')]
		]
		
		layout = [
			[sg.Column(file_button_layout, expand_x=True)],
			[sg.Frame("", 
				[
					[sg.Column(issue_counter_layout, expand_x=True)],
					[
						sg.Col(multiline_layout, expand_y=True), 
						sg.Col(issue_button_layout, expand_x=True, expand_y=True)
					]
				], expand_x=True, expand_y=True, key='-argos_issue_frame-')
			]
		]

		return sg.Tab('Argos File', layout, key='-argos_tab-')	

	def process_argos_tab_event(self, event, values):
		if event == '-argos_file-':
			file = values['-argos_file-']
			if not os.path.isfile(file) or self.get_file_ext(file) != 'CSV':
				self.error_popup('That is not a valid csv file...')
			else:
				self.process_file(tab, file)
		
		elif event == '-argos_refresh-':
			file = self.find_latest_csv(self.json['Argos_FILE_BASE_NAME'])
			if file: self.process_argos_file(file)
			
		elif event in ('-argos_next-', '-argos_prev-') and self.issue_table.processed:
			i = -1 if event == '-argos_prev-' else 1
			self.issue_table.issue_index = (self.issue_table.issue_index + i) % len(self.issue_table.issue_list)
		
		elif event in ('-argos_ignore_once-', '-argos_ignore_always-'):
			issue = self.issue_table.get_current_issue()
			if issue:
				self.issue_table.remove_current_issue()
				if event == '-argos_ignore_always-':
					self.current_sem_json()['IGNORED_ISSUES'][str(issue)] = 1
					self.update_json()

		elif event == '-argos_room0-':
			issue = self.issue_table.get_current_issue()
			self.create_window(issue.get_sec_shortname() + ' Room Options', 
				[
					[sg.Table([s.split('\t') for s in issue.sec_room_options], 
						headings=['Also Used By', 'Room', 'Priority'], 
						justification='left', expand_y=True, expand_x=True)]
				], size=(600, 300)).finalize() #independent non-modal window.
			
		self.update_argos_tab()
		return	

	def update_argos_tab(self):
		sem_json = self.current_sem_json()
		issue = self.issue_table.get_current_issue()
		
		# FILE META DATA
		self.main_window['-argos_file_timestamp-'].update(
			"File:\t%s\nUpdated:\t%s" % (os.path.basename(sem_json['CSV']), sem_json['TIMESTAMP'])
			if self.issue_table.processed else 'No Argos CSV Loaded')

		#ISSUE FRAME
		self.main_window['-argos_issue_frame-'].update(visible=self.issue_table.processed)
		
		#ISSUE COUNTER		
		self.main_window['-argos_issue_counter-'].update(
			'NO ISSUES' if len(self.issue_table.issue_list) == 0 
			else f"ISSUE {self.issue_table.issue_index + 1} (out of {len(self.issue_table.issue_list)})")
		
		#ISSUE COUNTER ARROWS
		for k in ('-argos_prev-', '-argos_next-'):
			self.main_window[k].update(
				visible = (len(self.issue_table.issue_list) > 1))
				
		# IGNORE BUTTONS
		self.main_window['-argos_ignore_once-'].update(disabled = (issue==None))
		self.main_window['-argos_ignore_always-'].update(disabled = (issue==None))
		
		#ISSUE MSG
		msg = ''
		if issue:
			section_label = '  Section: %s' % (issue.sec)
			msg = (section_label + '\n\n  Error Msg: ' + issue.msg.replace('\n', '\n\n  '))
		self.main_window['-argos_issue_msg-'].update(msg)

		# ROOM OPTIONS
		if issue:
			self.main_window['-argos_room_opt_col-'].update(visible = issue.has_room_options())
			self.main_window['-argos_room0-'].update(issue.get_sec_shortname())
		else:
			self.main_window['-argos_room_opt_col-'].update(False)

	def process_argos_file(self, file):
		rooms.readRoomFile(self.json['RoomsXLFile'], tmp_folder=self.default_data_dir)
	
		sem_json = self.current_sem_json()
		file_mod_time = datetime.fromtimestamp(os.path.getmtime(file))
		sem_json['CSV'] = os.path.join(self.get_sem_dir(), os.path.basename(file))
		sem_json['TIMESTAMP'] = file_mod_time.strftime("%m/%d/%y %I:%M:%S %p")
		self.update_json()
		self.copyfile(file, sem_json['CSV'])

		sched = Schedule(sem_json['CSV'])
		issue_list = validate_schedule(sched, self.json['zero_room_ins_meth_list'])
		
		self.issue_table.reset()
		self.issue_table.issue_list = [i for i in issue_list 
			if str(i) not in sem_json['IGNORED_ISSUES']]

		self.issue_table.processed = True
		self.main_window['-argos_col_file_buttons-'].update(visible=True)
		self.main_window['-argos_issue_frame-'].update(visible=True)
		
#####################Settings#######################
	def create_stg_tab(self):
		layout = [
			[sg.Frame('Rooms.xlsx File', [[ 
				sg.In(self.json['RoomsXLFile'], size=(50, 1), disabled=True, key='-RoomsXLFile-'), 
				sg.Button('Choose New Rooms.xlsx File', key='-NewRoomsXLFile-')
			]])],
			[sg.Frame('Zero Rooms Needed INS_METH List', [[
				sg.Multiline(repr(self.json['zero_room_ins_meth_list']), size=(60, 3), key='-Ins_Meth_List-'),
				sg.Button('Revert', key='-Ins_Meth_List_Revert-'),
				sg.Button('Apply', key='-Ins_Meth_List_Apply-')
			]])],			
			[sg.Button('Reset All Ignores')]
		]
		return sg.Tab('Settings', layout, key='-stg_tab-')

	def prcoess_stg_tab(self, event, values):
		if event == 'Reset All Ignores':
			for sem in self.json['Semesters'].values():
				sem['IGNORED_ISSUES'] = {}
			self.update_json()
			return
			
		if event == '-NewRoomsXLFile-':
			self.get_roomxl_file()
			self.main_window['-RoomsXLFile-'].update(self.json['RoomsXLFile'])			
			return

		#Apply or Revert INS_METH List
		gui_key = '-Ins_Meth_List-'
		json_key = 'zero_room_ins_meth_list'
		if 'Apply' in event:
			try:
				self.json[json_key] = ast.literal_eval(values[gui_key])
				self.update_json()
				return
			except:
				self.error_popup('That is not valid syntax for a list...')
		elif 'Revert' in event:
			self.main_window[gui_key].update(self.json[json_key])

#####################Utils#######################
	def create_window(self, *args, **kwargs):
		return sg.Window(*args, font=self.font, **kwargs) # keep_on_top=True, ttk_theme='aqua', use_ttk_buttons=True
	
	def error_popup(self, msg):
		self.create_window('Error...', 
			[[sg.Text(msg)], [sg.Push(), sg.Button('Ok')]]).read(close=True)			

	def msgbox_popup(self, msg, title):
		self.create_window(title, 
			[
				[sg.Multiline(msg, disabled=True, size=(80, 10))], 
				[sg.Push(), sg.Button('Ok')]
			]).read(close=True)
		
	def create_link(self, label, link_key):
		return sg.Text(label, enable_events=True, text_color='blue', 
			font=self.font + ('underline',), key=link_key)

	def get_file_ext(self, f):
		return os.path.splitext(f)[1].upper()[1:]

	def get_sem_dir(self):
		dir = os.path.join(self.json['DataFolder'], self.json['CurrentSemester'])
		os.makedirs(dir, exist_ok=True)
		return dir

	def copyfile(self, src, dest):
		if os.path.exists(dest):
			d, f = os.path.split(dest)
			shutil.move(dest, os.path.join(d, 'prev_' + f))
		
		shutil.copy(src, dest)
		
	def find_latest_csv(self, file_base_name):
		dl = os.path.expanduser('~/Downloads')
		files = [os.path.join(dl, f) for f in os.listdir(dl) if 
			os.path.isfile(os.path.join(dl, f)) and f.startswith(file_base_name) and
			self.get_file_ext(f) == 'CSV']
		
		if len(files) == 0:
			self.error_popup('No files matching %s.%s found in %s.' % (file_base_name, 'csv', dl))
			return None
		
		max_i = 0
		for i in range(len(files)):
			if os.path.getmtime(files[i]) > os.path.getmtime(files[max_i]):
				max_i = i
		return files[max_i]

	def open_file_with_app(self, filename):
		if not os.path.exists(filename):
			raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)
		
		if sys.platform == "win32":
			os.startfile(filename)
		else:
			opener = "open" if sys.platform == "darwin" else "xdg-open"
			subprocess.call([opener, filename])

#####################MAIN#######################
	def main(self):
		# sg.ChangeLookAndFeel('Dark') 	
		sg.theme('DefaultNoMoreNagging')
		self.font = ('Any', 12)
	
		try:
			if self.json['RoomsXLFile'] == None:
				self.get_roomxl_file()
			self.main_window = sgui.create_window('Argos Room Finder',
				[
					[sgui.create_semester_frame()],
					[sg.VPush()],
					[sg.TabGroup([[sgui.create_argos_tab(), sgui.create_stg_tab()]], 
						expand_y=True, expand_x=True, enable_events=True, key='-tab-')],
					[sg.Multiline("Console Output...\n", disabled=True, size=(80, 5), 
						expand_x=True, reroute_stdout = True, reroute_stderr = True,
						echo_stdout_stderr = True)]
				], finalize=True, resizable=True)

			self.update_argos_tab()
			self.update_link_text_boxes(self.std_links)

			while True:
				event, values = self.main_window.read()
				if event == sg.WIN_CLOSED:
					break
				elif event.startswith('-sem_'):
					self.process_semester_frame(event, values)
				elif event.startswith('-URL'):
					webbrowser.open(self.std_links[event][1])
				elif event.startswith('-FILE'):
					self.open_file_with_app(self.std_links[event][1])
				elif values['-tab-'] == '-argos_tab-':
					self.process_argos_tab_event(event, values)
				elif values['-tab-'] == '-stg_tab-': 
					self.prcoess_stg_tab(event, values)
			
			self.main_window.close()
		except (FileNotFoundError, IOError) as e:
			self.error_popup(str(e) + "\nCheck Folder Paths Under Settings...\nApp Must Be Restart...")
		except BaseException as e:
			self.error_popup(traceback.format_exc() + "\nApp Must Be Restart...")

if __name__ == "__main__":
	sgui = ArgosRoomFindGUI()
	sgui.main()
	
