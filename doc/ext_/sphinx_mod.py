import os
import sys
import inspect

# Events
from sphinx.ext.autodoc import MethodDocumenter, FunctionDocumenter
from sphinx.ext.autodoc import ModuleDocumenter, ClassDocumenter


class EventDocumenter(MethodDocumenter):
    objtype = "event"
    member_order = 45
    priority = 5

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):

        if not isinstance(parent, ClassDocumenter):
            return False
        try:
            return member.__name__ in member.__self__.__class__.event_types
        except:
            return False


class FunctionDocumenter2(FunctionDocumenter):
    objtype = 'function'

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        can = FunctionDocumenter.can_document_member(
            member, membername, isattr, parent)
        # bound methods
        plus = isinstance(
            parent, ModuleDocumenter) and inspect.ismethod(member)
        return can or plus


def setup(app):
    app.add_autodocumenter(EventDocumenter)
    app.add_autodocumenter(FunctionDocumenter2)


# Search all submodules
def find_modules(rootpath, skip=dict()):
    """
    Look for every file in the directory tree and return a dict
    Hacked from sphinx.autodoc
    """

    INITPY = '__init__.py'

    rootpath = os.path.normpath(os.path.abspath(rootpath))
    if INITPY in os.listdir(rootpath):
        root_package = rootpath.split(os.path.sep)[-1]
        print("Searching modules in", rootpath)
    else:
        print("No modules in", rootpath)
        return

    def makename(package, module):
        """Join package and module with a dot."""
        if package:
            name = package
            if module:
                name += '.' + module
        else:
            name = module
        return name

    skipall = list()
    for m in list(skip.keys()):
        if skip[m] is None:
            skipall.append(m)

    tree = dict()
    saved = 0
    found = 0

    def save(module, submodule):
        name = module + "." + submodule
        for s in skipall:
            if name.startswith(s):
                return False
        if module in skip:
            if submodule in skip[module]:
                return False
        if module not in tree:
            tree[module] = list()
        tree[module].append(submodule)
        return True

    for root, subs, files in os.walk(rootpath):
        py_files = sorted(
            [f for f in files if os.path.splitext(f)[1] == '.py'])

        if INITPY in py_files:
            subpackage = root[len(rootpath):].lstrip(os.path.sep). \
                replace(os.path.sep, '.')
            full = makename(root_package, subpackage)
            part = full.rpartition('.')
            base_package, submodule = part[0], part[2]
            found += 1
            if save(base_package, submodule):
                saved += 1

            py_files.remove(INITPY)
            for py_file in py_files:
                found += 1
                module = os.path.splitext(py_file)[0]
                if save(full, module):
                    saved += 1

    for item in list(tree.keys()):
        tree[item].sort()
    print("%s contains %i submodules, %i skipped" %
          (root_package, found, found - saved))
    return tree


def find_all_modules(document_modules, skip_modules):
    tree = dict()
    for mod in document_modules:
        mod_path = os.path.join('..', mod)
        if mod in list(skip_modules.keys()):
            tree.update(find_modules(mod_path, skip_modules[mod]))
        else:
            tree.update(find_modules(mod_path))
    return tree


def write_build(data, filename):
    with open(os.path.join('internal', filename), 'w') as f:
        f.write(".. list-table::\n")
        f.write("   :widths: 50 50\n")
        f.write("\n")
        for var, val in data:
            f.write("   * - " + var + "\n     - " + val + "\n")


def write_blacklist(pack, filename):
    with open(os.path.join('internal', filename), 'w') as f:
        modules = list(pack.keys())
        modules.sort()
        for mod in modules:
            if pack[mod] is None:
                f.write("* ``" + mod + "``\n")
            else:
                pack[mod].sort()
                for sub in pack[mod]:
                    f.write("* ``" + mod + "." + sub + "``\n")
