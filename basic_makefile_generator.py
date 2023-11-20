import os
import string

__FILES__ = [] # used as cache

def has_visible_chars(input_string):
    invisible_chars = set(string.whitespace)
    return any(char not in invisible_chars for char in input_string)


def get_files(dir=''):
    if dir == '':
        return os.listdir()
    else:
        return os.listdir(dir)


def get_files_with(extention=('.c', '.h'), dir='', force=False):
    global __FILES__
    if force:
        temp = get_files(dir)
        __FILES__ = temp
        package = []
        for fname in temp:
            if fname.endswith(extention):
                package.append(fancy_file(fname))
        return package
        # return [fancy_file(fname, start=True) for fname in temp if fname.endswith(extention)]
    return [fancy_file(fname) for fname in __FILES__ if fname.endswith(extention)]


def has_makefile(file_list):
    return 'Makefile' in file_list


def toString(arr, seperator):
    if len(arr) > 0:
        out = ''
        for a in arr:
            out += a + seperator
        return out[:-1]
    return ""


def makefile_builder(fileTable, mName):
    content = "CC = g++\nCFLAGS = -Wall -Wextra"
    total_objs = ''
    rules = {}

    for filename, fileObjects in fileTable.items():
        base_name, ext = os.path.splitext(filename)
        total_objs += f"\n{base_name.upper()}_DEPS = {' '.join(fileObjects)}"
        rule = f"{base_name}: $({base_name.upper()}_DEPS)\n"
        rule += f"\t$(CC) $(CFLAGS) $({base_name.upper()}_DEPS) -o {base_name}\n"
        rules[base_name] = rule

    if len(rules.keys()) == 0:
        print('ERROR: No targets found. (no files that end in .cpp have a main function)')
        exit(1)

    targets = "TARGETS = " + ' '.join(rules.keys())
    # rules['all'] = 'all: $(TARGETS)' // direct insertion
    dot_o_file_rule = '%.o: %.cpp\n\t$(CC) $(CFLAGS) -c $< -o $@'
    clean = 'clean:\n\trm -f $(TARGETS) $(wildcard *.o)'

    newline = '\n'
    content += f"{total_objs}\n{targets}\n\nall: $(TARGETS)\n\n{newline.join(rules.values())}\n{dot_o_file_rule}\n\n{clean}"

    if safe_write(content, mName):
        print("> Use `make` to compile all executables and object files")
        print("> Use `make clean` to remove all executables and object files")
        print("> Use `make <name>` to compile a specific executable and object file")
        print("      (otions for <name> are: " + grab(rules.keys()) + ")\n\n")

def grab(funny_dict):
    return toString(funny_dict, ' ').replace(' ', ', ')


def safe_write(contnet, filename):
    if os.path.exists(filename)and has_visible_chars(open(filename).read()):
        while True:
            i = input("File exists, overwrite? (y/n) ").lower()
            if (i in ['y', 'yes', 'ye', 'sure', 'yeah', 'ya', 'ok']):
                break
            if (i in ['n', 'no', 'nah', 'nope', 'nop',]):
                filename = input("Enter altenative filename (q=quit): ")
                if filename in ['q', 'quit']: 
                    print("Exiting...")
                    return False
    with open(filename, 'w') as f:
        f.write(contnet)
    print('Wrote to', filename)
    return True


class fancy_file:
    def __init__(self, filename):
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
        self.includes = self._get_includes() # ignore
        self.has_main = self._check_main()
        self.dObjects = ['None']
        if self.has_main:
            self.dObjects = _get_dependency_objects(self.filename)

        # if not start or self.has_main:
        #     self._deep_dependency_search(ignore)
        #     # pass

    def _get_type(self):
        fPlus = self.filename.split('.')
        if len(fPlus) == 1:
            return ''
        return fPlus[-1]

    def _get_includes(self): # , ignore
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
        return any('int main(' in line or 'void main(' in line for line in self.lines)

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
        if (d+'.hpp') in __FILES__:
            hpp = d+'.hpp'
        if (d+'.cpp') in __FILES__:
            cpp = d+'.cpp'
        return cpp, hpp


def deep_copy(arr:list):
    return [item for item in arr if item]


def _get_dependency_objects(file, depth=0, found=[], hide_missing_files_tree=False):
    # print('\nSearching for dependency objects in file: ' + file)
    deps = _deep_dependency_search_recursive(file, '', depth=depth, found=found)
    udeps = []
    for dep in deps:
        udep = _object(dep)
        if udep not in udeps:
            udeps.append(udep)
    # print(f"Found: {udeps}\n\n")
    return udeps


def _object(file):
    if os.path.exists(file.split('.')[0]+'.cpp'):
        return file.split('.')[0]+'.o'
    return file.split('.')[0]+'.hpp'


def _deep_dependency_search_recursive(file, tree, depth=0, found=[]): # returns total not unique
    # print(f'\t> DDSR({file=}, {depth=}, {found=})\n')
    tree += f'{file}->'
    found += [file]
    if not os.path.exists(file):
        print(f'WARNING: Could not find file: {file}, following path: {tree[:-2]}')
        # if input("> Continue? (y/n) ").lower() == 'y':
        return found
        # exit(1)
    deps = __read_includes(
        file, 
        open(file).read().split('\n')
    )
    deps = add_extentions(deps)
    if not deps:
        return found
    udeps = [dep for dep in deps if dep not in found]
    for dep in udeps:
        if dep not in found:
            found = _deep_dependency_search_recursive(dep, tree, depth=depth+1, found=found)
    return found


def add_extentions(deps):
    out = deep_copy(deps)
    for dep in deps:
        other = dep.split('.')[0] + '.cpp'
        if dep.endswith('.cpp'):
            other = dep.split('.')[0] + '.hpp'
        if other not in out:
            out.append(other)
    return out


def __read_includes(file, lines): # , ignore
    includes = [file]
    for line in lines:
        if line.strip().startswith("#include"):
            include_tokens = line.split('"')
            if len(include_tokens) > 1:
                includes.append(include_tokens[1])
    return includes


def main():
    files = get_files_with(extention='.cpp', force=True)
    flTable = {}
    for file in files:
        if file.has_main:
            flTable[file.filename] = file.dObjects
    makefile_builder(flTable, 'Makefile')


if __name__ == "__main__" :
    main()
