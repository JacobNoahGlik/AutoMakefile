import os
import sys
import string
import platform

__DIR__ = ''

__FILES__ = []  # used as cache


def printy_deprecated(out, color):
  if color == 'red':
    print('\033[1;31;40m' + out + '\033[0m')
  elif color == 'green':
    print('\033[92m' + out + '\033[0m')
  elif color == 'yellow':
    print('\033[93m' + out + '\033[0m')
  elif color == 'blue':
    print('\033[94m' + out + '\033[0m')
  elif color == 'purple':
    print('\033[95m' + out + '\033[0m')
  elif color == 'grey' or color == 'gray':
    print('\033[38;2;128;128;128m' + out + '\033[0m')


def printy(out, color, end='\n'):
  color = color.lower()

  if platform.system().lower() == "windows":
    import ctypes
    Kernel = ctypes.windll.kernel32
    colors = {
        "green": 0x0A,
        "red": 0x0C,
        "grey": 0x08,
        "gray": 0x08,
    }
    if color in colors:
      Kernel.SetConsoleTextAttribute(Kernel.GetStdHandle(-11), colors[color])
      print(out, end=end)
      Kernel.SetConsoleTextAttribute(Kernel.GetStdHandle(-11), 0x07)
    else:
      print(out, end=end)

  else:
    # Linux system
    colors = {
        "green": "\033[92m",
        "red": "\033[1;31;40m",
        "grey": "\033[90m",
        "gray": "\033[90m",
    }
    if color in colors:
      print(f"{colors[color]}{out}\033[0m", end=end)
    else:
      print(out, end=end)


def has_visible_chars(input_string):
  invisible_chars = set(string.whitespace)
  return any(char not in invisible_chars for char in input_string)


def get_files():
  global __DIR__
  if __DIR__ == '':
    return os.listdir()
  else:
    return os.listdir(__DIR__)


def get_files_with(extention=('.c', '.h'), dir='', force=False, _warn=False):
  global __FILES__
  if force:
    global __DIR__
    __DIR__ = dir
    temp = get_files()
    __FILES__ = temp
    package = []
    for fname in temp:
      if fname.endswith(extention):
        package.append(fancy_file(fname, _warn=_warn))
    return package
    # return [fancy_file(fname, start=True) for fname in temp if fname.endswith(extention)]
  return [
      fancy_file(fname, _warn=_warn) for fname in __FILES__ if fname.endswith(extention)
  ]


def has_makefile(file_list):
  return 'Makefile' in file_list


def toString(arr, seperator):
  if len(arr) > 0:
    out = ''
    for a in arr:
      out += a + seperator
    return out[:-1]
  return ""


def getH_File(baseName):
  if os.path.exists(baseName + '.h'):
    return baseName + '.h'
  if os.path.exists(baseName + '.hpp'):
    return baseName + '.hpp'
  return None


def makefile_builder(fileTable, mName):
  c_only_files = read_file_except()
  flags = '$(CXX) $(CPPFLAGS)'
  content = "CXX = g++\nCPPFLAGS = -Wall -Wextra"
  if c_only_files:
    content = "CC = gcc\nCFLAGS = -g -Wall"
    flags = '$(CC) $(CFLAGS)'
  total_objs = ''
  rules = {}
  oRules = ''

  for filename, fileObjects in fileTable.items():
    base_name, ext = os.path.splitext(filename)
    total_objs += f"\n{base_name.upper()}_DEPS = {' '.join(fileObjects)}"
    rule = f"{base_name}: $({base_name.upper()}_DEPS)\n\t{flags} $^ -o $@\n"
    rules[base_name] = rule
    oRules += addObjectRule(base_name)

  if len(rules.keys()) == 0:
    printy(
        'ERROR: No targets found. (no files that end in .c or .cpp have a main function)',
        'red')
    exit(1)

  targets = "TARGETS = " + ' '.join(rules.keys())
  # rules['all'] = 'all: $(TARGETS)' // direct insertion
  generic_o_rule = '%.o: %.cpp\n\t$(CXX) $(CPPFLAGS) -c $< -o $@'
  if c_only_files:
    generic_o_rule = '%.o: %.c\n\t$(CC) $(CFLAGS) -c $< -o $@'
  clean_prefix = '.PHONY: clean\nclean:\n\t'
  clean = f'{clean_prefix}rm -f $(TARGETS)\n\trm -f $(wildcard *.o)'

  newline = '\n'
  content += f"{total_objs}\n{targets}\n\nall: $(TARGETS)\n\n{newline.join(rules.values())}\n{generic_o_rule}\n\n{clean}"

  if safe_write(content, mName):
    out = "> Use `make` to compile all executables and object files"
    out += "\n> Use `make clean` to remove all executables and object files"
    out += "\n> Use `make <name>` to compile a specific executable and object file"
    out += "\n      (otions for <name> are: " + grab(rules.keys()) + ")\n\n"
    printy(out, 'green')


def read_file_except():
  cOnly = True
  cppOnly = True
  err = ['', '']
  throw = lambda lst: printy(
      f"EXCEPTION: found both 'C' and 'C++' files. Cannot compile both at once. Err on: ({lst[0]}, {lst[1]})",
      'red') or exit(1)
  for file in __FILES__:
    if file.endswith('.cpp') or file.endswith('.hpp'):
      cOnly = False
      err[0] = file
      if not cppOnly:
        throw(err)
    elif file.endswith('.c'):
      cppOnly = False
      err[1] = file
      if not cOnly:
        throw(err)
  return cOnly


def addObjectRule(base_name):
  f = [
      file for file in [
          base_name + '.c', base_name + '.h', base_name + '.cpp', base_name +
          '.hpp'
      ] if os.path.exists(file)
  ]
  if base_name + '.c' in f:
    return bild_c_object_rule(base_name, f)
  return bild_cpp_object_rule(base_name, f)


def bild_c_object_rule(base_name, files):
  deps = [file for file in files if file.endswith('.c') or file.endswith('.h')]
  return f'{base_name}.o: {toString(deps, " ")}\n\t$(CC) $(CFLAGS) -c $< -o $^\n'


def bild_cpp_object_rule(base_name, files):
  deps = [
      file for file in files
      if (file.endswith('.cpp') or file.endswith('.hpp') or file.endswith('.h')
          )
  ]
  return f'{base_name}.o: {toString(deps, " ")}\n\t$(CXX) $(CPPFLAGS) -c $< -o $^\n'


def grab(funny_dict):
  return toString(funny_dict, ' ').replace(' ', ', ')


def safe_write(contnet, filename):  # -> bool:
  while os.path.exists(filename) and has_visible_chars(open(filename).read()):
    i = input(f"'{filename}' already exists, overwrite? (y/n) ").lower()
    if (i in ['y', 'yes', 'ye', 'sure', 'yeah', 'ya', 'ok']):
      break
    if (i in [
        'n',
        'no',
        'nah',
        'nope',
        'nop',
    ]):
      filename = input("Enter altenative filename (q=quit): ")
      if filename in ['q', 'quit']:
        printy("Exiting...", 'gray')
        return False
  with open(filename, 'w') as f:
    f.write(contnet)
  printy(f'Wrote to {filename}\n', 'green')
  return True


class fancy_file:

  def __init__(self, filename, _warn=False):
    # , ignore=[], start=False, depth=0
    # if depth > 5:
    #     print("ERROR: Maximum recursion depth reached.")
    #     exit(1)
    # self.depth = depth
    # print(f"{filename=}, {ignore=}")
    self.filename = filename
    self.type = self._get_type()
    self.content = open(filename).read()
    self.lines = self.content.split('\n')
    self.includes = self._get_includes()  # ignore
    self.has_main = self._check_main()
    self.dObjects = ['None']
    if self.has_main:
      self._includes_exist()
      self.dObjects = _get_dependency_objects(self.filename, _warn=_warn)

    # if not start or self.has_main:
    #     self._deep_dependency_search(ignore)
    #     # pass

  def _includes_exist(self):
    err = False
    for i in self.includes:
      if not os.path.exists(i):
        get_line = '#include \"' + i + '\"'
        printy(
            f"ERROR: a file ('{i}') which was explicitly included in {self.filename} could not be found. '{get_line}' on line {self._get_line_no(get_line)} of {self.filename}.",
            'red')
        err = True
    if err:
      exit(1)

  def _get_line_no(self, string):
    for line_number, line in enumerate(self.lines):
      if string in line:
        return line_number + 1

  def _get_type(self):
    fPlus = self.filename.split('.')
    if len(fPlus) == 1:
      return ''
    return fPlus[-1]

  def _get_includes(self):  # , ignore
    includes = [self.filename]
    for line in self.lines:
      if line.strip().startswith("#include"):
        # Extract the included file name
        include_tokens = line.split('"')
        if len(include_tokens) > 1:
          # if inc not in ignore and inc not in includes:
          includes.append(include_tokens[1])
    return includes

  def _check_main(self):
    return any('int main(' in line or 'void main(' in line
               for line in self.lines)

  # def _deep_dependency_search(self, ignore):
  #     # global __SEARCH_MAX__
  #     # if __SEARCH__ >= __SEARCH_MAX__:
  #     #     exit(1)
  #     # __SEARCH__ += 1
  #     for dependency in deep_copy(self.includes):
  #         if dependency == self.filename or dependency in ignore:
  #             continue
  #         cpp, hpp = self._get_ch_files(dependency)
  #         if cpp:
  #             ffcpp = fancy_file(cpp, ignore=self.includes + ignore, depth = self.depth + 1)
  #             self.includes += ffcpp.includes
  #         if hpp:
  #             ffhpp = fancy_file(hpp, ignore=self.includes + ignore, depth = self.depth + 1)
  #             self.includes += ffhpp.includes

  def _get_ch_files(self, dep):
    d = dep.split('.')[0]
    hpp = None
    cpp = None
    if (d + '.hpp') in __FILES__:
      hpp = d + '.hpp'
    elif (d + '.h') in __FILES__:
      hpp = d + '.h'
    if (d + '.cpp') in __FILES__:
      cpp = d + '.cpp'
    return cpp, hpp


def deep_copy(arr: list):
  return [item for item in arr if item]


def _get_dependency_objects(file,
                            depth=0,
                            found=[],
                            hide_missing_files_tree=False,
                           _warn=False):
  # print('\nSearching for dependency objects in file: ' + file)
  deps = _deep_dependency_search_recursive(file, '', depth=depth, found=found, _warn=_warn)
  udeps = []
  for dep in deps:
    udep = _object(dep)
    if udep and udep not in udeps:
      udeps.append(udep)
  # print(f"Found: {udeps}\n\n")
  return udeps


def _object(file):
  if os.path.exists(file.split('.')[0] + '.cpp'):
    return file.split('.')[0] + '.o'
  if os.path.exists(file.split('.')[0] + '.c'):
    return file.split('.')[0] + '.o'
  # return file.split('.')[0]+'.hpp'
  if os.path.exists(file):
    return file
  return None


def _deep_dependency_search_recursive(file,
                                      tree,
                                      depth=0,
                                      found=[],
                                      _warn=False):  # returns total not unique
  # print(f'\t> DDSR({file=}, {depth=}, {found=})\n')
  tree += f'{file}->'
  found += [file]
  if not os.path.exists(file) and _warn:
    # print()
    printy(
        f'WARNING: Could not find file: {file}, following path: {tree[:-2]}',
        'grey')
    # if input("> Continue? (y/n) ").lower() == 'y':
    return found
    # exit(1)
  deps = __read_includes(file, open(file).read().split('\n'))
  deps = add_extentions(deps)
  if not deps:
    return found
  udeps = [dep for dep in deps if dep not in found]
  for dep in udeps:
    if dep not in found:
      found = _deep_dependency_search_recursive(dep,
                                                tree,
                                                depth=depth + 1,
                                                found=found)
  return found


def add_extentions(deps):
  out = deep_copy(deps)
  for dep in deps:
    other = dep.split('.')[0] + '.cpp'
    if dep.endswith('.cpp'):
      other = dep.split('.')[0] + '.hpp'
      if not os.path.exists(other):
        other = dep.split('.')[0] + '.h'
    if other not in out:
      out.append(other)
  return out


def __read_includes(file, lines):  # , ignore
  includes = [file]
  for line in lines:
    if line.strip().startswith("#include"):
      include_tokens = line.split('"')
      if len(include_tokens) > 1:
        includes.append(include_tokens[1])
  return includes


def main():
  warn = False
  global __DIR__
  if len(sys.argv) > 1:
    __DIR__ = sys.argv[1]
  files = get_files_with(extention=('.cpp', 'c'), force=True, _warn=warn)
  flTable = {}
  for file in files:
    if file.has_main:
      flTable[file.filename] = file.dObjects
  makefile_builder(flTable, 'Makefile')


def idea():
  import re

  source_code = open('source_code.hpp').read() + open('source_code.cpp').read()

  # Extract library names from #include statements
  library_pattern = re.compile(r'#include <(\S+)/\S+\.hpp>')
  library_matches = library_pattern.findall(source_code)

  # Create library flags
  library_flags = ["-l" + lib for lib in library_matches]
  print(" ".join(library_flags))


if __name__ == "__main__":
  main()
