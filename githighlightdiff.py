# Copyright 2012 Google Inc. All Rights Reserved.

"""Plugin for highlighting added lines based on git diff.

TODOs:
- Highlight only changed characters, not entire lines.
- Show an indicator for deleted lines.
- Move highlight to be ala IntelliJ (just over in the left rail).
"""

__author__ = 'petek@google.com (Pete Kruskall)'

import os.path
import subprocess

import sublime
import sublime_plugin


class GitHighlightDiff(sublime_plugin.EventListener):
  """Save event listener for highlighting lines that differ from git commit."""

  def HighlightRegions(self, view, regions):
    """Erases old highlights and highlights new regions."""
    old_regions = view.get_regions('GitDiff')
    for r in old_regions:
      view.add_regions('GitDiff', [r], '', 0)

    print str(regions)

    # TODO(tek): Make this a setting.
    just_show_gutter = False
    # TODO(tek): Make this a setting.
    color_style = "comment"

    if just_show_gutter:
      regions = [sublime.Region(r.a, r.a) for r in regions]

    view.add_regions('GitDiff', regions, color_style, "bookmark")

  def RetrieveOutputFromSubproc(self, proc):
    """Returns lines returned from a subprocess command."""
    result = ''
    for stream in [proc.stderr, proc.stdout]:
      while True:
        out = stream.read(1)
        # pylint: disable-msg=C6403
        if out == '' and proc.poll() is not None:
          break
        if out != '':
          result += out
    return result

  # pylint: disable-msg=C6409
  def on_post_save(self, view):
    """Called after save on all files, highlights added lines.

    Will exit if file is not inside a git repo.

    Args:
      view: A sublime view object.
    """
    file_dir = os.path.dirname(view.file_name())
    file_name = os.path.basename(view.file_name())

    test_is_git_repo_cmd = 'git status %s' % file_name
    is_git_repo_proc = subprocess.Popen(test_is_git_repo_cmd,
                                        shell=True,
                                        cwd=file_dir,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)

    is_git_repo_result = self.RetrieveOutputFromSubproc(is_git_repo_proc)

    print test_is_git_repo_cmd
    print is_git_repo_result

    if is_git_repo_result.startswith('fatal:'):
      return

    # Actual diff.

    cmd = 'git diff %s' % file_name
    res = subprocess.Popen(cmd, shell=True, cwd=file_dir,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    git_diff_result = self.RetrieveOutputFromSubproc(res)
    lines = git_diff_result.split('\n')

    # Skip the first few lines, which just have the file name...
    current_line_number = -1
    highlight_regions = []
    for line in lines[4:]:
      if line:
        if line[0] == '@':
          line_num = line[line.index('+') + 1:]
          line_num = line_num[:line_num.index(',')]
          current_line_number = int(line_num)

        if line[0] != '-':
          current_line_number += 1

          if line[0] == '+':
            # Added line, show it
            found_line = view.line(view.text_point(current_line_number - 3, 0))
            highlight_regions.append(found_line)

    self.HighlightRegions(view, highlight_regions)
