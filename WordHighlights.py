import sublime
import sublime_plugin

DEFAULT_COLOR_SCOPE_NAME = 'comment'

ALL_SETTINGS = [
    'word_highlights',
    'word_highlights_draw_outlined',
    'word_highlights_when_selection_is_empty',
]

used_color_scope_names = []


def settings_changed():
    for window in sublime.windows():
        for view in window.views():
            reload_settings(view)


def reload_settings(view):
    '''Restores user settings.'''
    settings_name = 'WordHighlights'
    settings = sublime.load_settings(settings_name + '.sublime-settings')
    settings.clear_on_change(settings_name)
    settings.add_on_change(settings_name, settings_changed)

    for setting in ALL_SETTINGS:
        if settings.get(setting) is not None:
            view.settings().set(setting, settings.get(setting))

    if view.settings().get('word_highlights') is None:
        view.settings().set('word_highlights', True)


def word_highlights_enabled(view, default=None):
    if view.settings().get('word_highlights') is None:
        reload_settings(view)
    return view.settings().get('word_highlights', default)


def regex_escape(string):
    outstring = ""
    for c in string:
        if c != '\\':
            outstring += '[' + c + ']'
        else:
            outstring += '\\'
    return outstring


def highlight(view, color_scope_name=DEFAULT_COLOR_SCOPE_NAME, when_selection_is_empty=False):
    settings = view.settings()
    draw_outlined = sublime.DRAW_OUTLINED if settings.get('word_highlights_draw_outlined') else 0
    word_separators = settings.get('word_separators')

    view_sel = view.sel()
    if len(view_sel) > 1:
        regions = list(view_sel)
    else:
        regions = []
        for sel in view_sel:
            # If we directly compare sel and view.word(sel), then in compares their
            # a and b values rather than their begin() and end() values. This means
            # that a leftward selection (with a > b) will never match the view.word()
            # of itself.
            # As a workaround, we compare the lengths instead.
            if not sel:
                if when_selection_is_empty:
                    string = view.substr(view.word(sel)).strip()
                    if string and any(c not in word_separators for c in string):
                        regions += view.find_all('\\b' + regex_escape(string) + '\\b')
            else:
                string = view.substr(sel).strip()
                if string:
                    if len(sel) == len(view.word(sel)):
                        regex = '\\b' + regex_escape(string) + '\\b'
                    else:
                        regex = regex_escape(string)
                    regions += view.find_all(regex)
    if color_scope_name not in used_color_scope_names:
        used_color_scope_names.append(color_scope_name)
    view.add_regions('WordHighlights_%s' % color_scope_name, regions, color_scope_name, '', draw_outlined | sublime.PERSISTENT)


def reset(view):
    while used_color_scope_names:
        view.erase_regions('WordHighlights_%s' % used_color_scope_names.pop())


class WordHighlightsListener(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
        settings = view.settings()
        if word_highlights_enabled(view, True):
            highlight(view, DEFAULT_COLOR_SCOPE_NAME, settings.get('word_highlights_when_selection_is_empty', False))


class WordHighlightsToggleCommand(sublime_plugin.TextCommand):
    _word_highlights = None
    _word_highlights_when_selection_is_empty = None

    def run(self, edit, block=False):
        settings = self.view.settings()
        _word_highlights = word_highlights_enabled(self.view, True)
        _word_highlights_when_selection_is_empty = settings.get('word_highlights_when_selection_is_empty', True)
        if self.__class__._word_highlights is None:
            self.__class__._word_highlights = _word_highlights
        if self.__class__._word_highlights_when_selection_is_empty is None:
            self.__class__._word_highlights_when_selection_is_empty = _word_highlights_when_selection_is_empty
        if _word_highlights_when_selection_is_empty and _word_highlights:
            settings.set('word_highlights', self.__class__._word_highlights)
            settings.set('word_highlights_when_selection_is_empty', self.__class__._word_highlights_when_selection_is_empty)
            reset(self.view)
        else:
            settings.set('word_highlights', True)
            settings.set('word_highlights_when_selection_is_empty', True)
            highlight(self.view, DEFAULT_COLOR_SCOPE_NAME, True)


class WordHighlightsResetCommand(sublime_plugin.TextCommand):
    def run(self, edit, block=False):
        reset(self.view)


class WordHighlightsCommand(sublime_plugin.TextCommand):
    def run(self, edit, block=False, color_scope_name=DEFAULT_COLOR_SCOPE_NAME):
        highlight(self.view, color_scope_name, True)
