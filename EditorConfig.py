import pprint
import sublime
import sublime_plugin

def unexpanduser(path):
	from os.path import expanduser
	return path.replace(expanduser('~'), '~')

try:
	import os, sys
	# stupid python module system
	sys.path.append(os.path.dirname(os.path.realpath(__file__)))
	from .editorconfig import get_properties, EditorConfigError
except:
	# Python 2
	from editorconfig import get_properties, EditorConfigError

LINE_ENDINGS = {
	'lf': 'unix',
	'crlf': 'windows',
	'cr': 'cr'
}

CHARSETS = {
	'latin1': 'Western (ISO 8859-1)',
	'utf-8': 'utf-8',
	'utf-8-bom': 'utf-8 with bom',
	'utf-16be': 'utf-16 be',
	'utf-16le': 'utf-16 le'
}

def log(msg):
	print('EditorConfig: %s' % msg)

def debug(msg):
	if sublime.load_settings('EditorConfig.sublime-settings').get('debug', False):
		log(msg)

class EditorConfig(sublime_plugin.EventListener):
	MARKER = 'editorconfig'

	def on_load(self, view):
		if not view.settings().has(self.MARKER):
			self.init(view, 'load')

	def on_activated(self, view):
		if not view.settings().has(self.MARKER):
			self.init(view, 'activated')

	def on_pre_save(self, view):
		self.init(view, 'pre_save')

	def on_post_save(self, view):
		if not view.settings().has(self.MARKER):
			self.init(view, 'post_save')

	def init(self, view, event):
		path = view.file_name()
		if not path:
			return

		try:
			config = get_properties(path)
		except EditorConfigError:
			print('Error occurred while getting EditorConfig properties')
		else:
			if config:
				if event == 'activated' or event == 'load':
					debug('File Path \n%s' % unexpanduser(path))
					debug('Applied Settings \n%s' % pprint.pformat(config))
				if event == 'pre_save':
					self.apply_pre_save(view, config)
				else:
					self.apply_config(view, config)

	def apply_pre_save(self, view, config):
		view.run_command('detect_indentation')
		settings = view.settings()
		spaces = settings.get('translate_tabs_to_spaces')
		charset = config.get('charset')
		end_of_line = config.get('end_of_line')
		indent_style = config.get('indent_style')
		insert_final_newline = config.get('insert_final_newline')
		if charset in CHARSETS:
			view.set_encoding(CHARSETS[charset])
		if end_of_line in LINE_ENDINGS:
			view.set_line_endings(LINE_ENDINGS[end_of_line])
		if indent_style == 'space' and spaces == False:
			view.run_command('expand_tabs', {'set_translate_tabs': True})
		elif indent_style == 'tab' and spaces == True:
			view.run_command('unexpand_tabs', {'set_translate_tabs': True})
		if insert_final_newline == 'false':
			view.run_command('remove_final_newlines')

	def apply_config(self, view, config):
		settings = view.settings()
		indent_style = config.get('indent_style')
		indent_size = config.get('indent_size')
		trim_trailing_whitespace = config.get('trim_trailing_whitespace')
		insert_final_newline = config.get('insert_final_newline')
		if indent_style == 'space':
			settings.set('translate_tabs_to_spaces', True)
		elif indent_style == 'tab':
			settings.set('translate_tabs_to_spaces', False)
		if indent_size:
			try:
				settings.set('tab_size', int(indent_size))
			except ValueError:
				pass
		if trim_trailing_whitespace == 'true':
			settings.set('trim_trailing_white_space_on_save', True)
		elif trim_trailing_whitespace == 'false':
			settings.set('trim_trailing_white_space_on_save', False)
		if insert_final_newline == 'true':
			settings.set('ensure_newline_at_eof_on_save', True)
		elif insert_final_newline == 'false':
			settings.set('ensure_newline_at_eof_on_save', False)

		view.settings().set(self.MARKER, True)

class RemoveFinalNewlinesCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		region = self.view.find('\n*\Z', 0)
		self.view.erase(edit, region)
