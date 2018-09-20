import bs4
import os
from collections import defaultdict
from enum import Enum, auto

def _lazy_str(self):
    return self.__class__.__name__ + '('+', '.join((x+'='+repr(y)) for x, y in self.__dict__.items())+')'

def javadoc_comment(comment, at_tags={}):
    at_tags_str = '\n'.join(
        tag + ' ' + (text) for tag, texts in at_tags.items() for text in texts
    )
    if at_tags_str:
        at_tags_str = '\n'+at_tags_str
    comment = comment.replace('\n ', '\n')
    return ('/**\n'+comment.rstrip()+at_tags_str).replace('\n', '\n * ').rstrip()+'\n */'

METHOD_MODIFIERS = {
    'public', 'private', 'static', 'abstract', 'final', 'synchronized',
    'native', 'strictfp', 'protected', 'volatile'
}

CLASS_TYPES = {'class', 'interface', 'enum'}

ALL_MODIFIERS = METHOD_MODIFIERS | CLASS_TYPES

PRIMITIVE_TYPES = {
    'byte': '0', 'short': '0', 'int': '0', 'long': '0', 'float': '0',
    'double': '0', 'boolean': 'true', 'char': '\'0\'', 'void': None,
}

RESERVED_WORDS = ALL_MODIFIERS | set(PRIMITIVE_TYPES.keys())

class JavaObject:
    def __init__(self, definition):
        self._definition = definition.replace('\xa0', ' ')

        self._modifiers = []
        self._parse_modifiers()

    def _parse_modifiers(self):
        for token in self._definition.split(' '):
            if not token:
                continue
            if token not in ALL_MODIFIERS:
                break
            self._modifiers.append(token)

    @staticmethod
    def indent(indent, lines):
        for l in lines:
            yield ' '*indent + l

class JavaClass(JavaObject):
    def __init__(self, package, name, definition, description):
        super().__init__(definition)

        self.package = package
        self.name = name
        self.file_path = os.path.join(*self.package.split('.'), name+'.java')
        self._desc = description

        self._constructors = []
        self._methods = []
        self._fields = []

        self.type = next(filter(lambda x: x in CLASS_TYPES, self._modifiers))

    def add_constructor(self, method: 'JavaMethod'):
        self._constructors.append(method)
        method.set_as_constructor(True)
        method.set_class(self)

    def add_method(self, method):
        self._methods.append(method)
        method.set_class(self)

    def add_field(self, field):
        self._fields.append(field)

    def format_as_lines(self, **kwargs):
        is_interface = 'interface' == self.type
        ret = []
        if self.package:
            ret.append('package ' + self.package + ';')
            ret.append('')
        ret.extend([
            javadoc_comment(self._desc), 
            self._definition + ' {'
        ])
        ret.append('')
        indent = kwargs.get('indent', 4)
        for c in self._fields + self._constructors + self._methods:
            ret.extend(self.indent(indent, c.format_as_lines(**kwargs)))
            ret.append('')
        ret.append('}')
        return ret

    def format(self, **kwargs):
        return '\n'.join(self.format_as_lines(**kwargs))

    __repr__ = __str__ = _lazy_str


# TODO: Superclass for these Java* classes defining common methods.
class JavaField(JavaObject):
    def __init__(self, definition):
        super().__init__(definition)
        self._name = self._definition.split(' ')[-1]

    def set_description(self, description):
        self._description = description

    def format_as_lines(self, **kwargs):
        todo = kwargs.get('todo', False)

        todo_comment = ''
        if todo:
            todo_comment = ' // TODO: Implement field ' +self._name

        return (
            javadoc_comment(self._description) + '\n' +
            (self._definition + ';' + todo_comment)
        ).split('\n')

class JavaMethod(JavaObject):

    def __init__(self, definition):
        super().__init__(definition)
        self._at_tags = defaultdict(lambda: [])
        self._description = ''
        self._decorators = []

        self._is_constructor = False
        self._return_type = self._parse_return_type()

        self.signature = self._parse_method_signature()

    def _parse_return_type(self):
        capturing_type = False
        ret_type = []
        for t in self._definition.split(' '):
            if not capturing_type:
                if not t: continue 
                if t in METHOD_MODIFIERS: continue 
            capturing_type = True 
            if '(' in t:
                break
            ret_type.append(t)
        return ' '.join(ret_type)

    def _parse_method_signature(self):
        signature = []
        left = None
        capturing_signature = False
        for t in self._definition.split(' '):
            t = t.strip()
            if not capturing_signature:
                if '(' in t: # Method signatures begin with Name( ...
                    capturing_signature = True
                    method_name = t.split('(')
                    left = method_name[0] + '('
                    if method_name[1] != ')':
                        signature.append(method_name[1])
                continue
            # Parameter name or blank, not in signature.
            if not t or t.endswith(','): 
                continue 
            if t.endswith(')'): # Ends with a close bracket.
                break
            signature.append(t)
        return left+', '.join(signature) + (')' if not left.endswith(')') else '')

    def set_as_constructor(self, is_constructor=True):
        self._is_constructor = is_constructor

    def set_class(self, class_: JavaClass):
        self._parent = class_

    def add_at_tag(self, tag, text):
        self._at_tags[tag].append(text)

    def set_description(self, description):
        self._description = description

    def add_decorator(self, dec):
        if dec not in self._decorators:
            self._decorators.append(dec)

    def format_as_lines(self, **kwargs):
        has_body = 'abstract' not in self._modifiers \
            and self._parent.type != 'interface'

        indent = kwargs.get('indent', 4)
        todo = kwargs.get('todo', False)

        if not todo:
            todo_comment = ''
        else:
            todo_comment = '// TODO: Implement method '+self.signature

        body = []
        if not has_body:
            definition_suffix = ';'
            suffix = ()
        else:
            definition_suffix = ' {'
            suffix = ('}', )

            if todo:
                body.append(todo_comment)
            body.append(self._make_return_statement())
            
            body = self.indent(indent, body)
        
        lines = javadoc_comment(self._description, self._at_tags).split('\n')
        lines.extend(self._decorators)
        lines.extend((self._definition + definition_suffix).split('\n'))
        lines.extend(body)
        lines.extend(suffix)

        return lines

    def _make_return_statement(self):
        if self._is_constructor:
            return ''
        try:
            return_value = PRIMITIVE_TYPES[self._return_type]
        except KeyError:
            return_value = 'null'
        if return_value is None:
            return 'return;'
        return 'return '+return_value+';'


    __repr__ = __str__ = _lazy_str

class JavaDocParser:
    EXCLUDE_FILES = [
        'allclasses-frame.html',
        'allclasses-noframe.html',
        'constant-values.html',
        'deprecated-list.html',
        'help-doc.html',
        'index-all.html',
        'index.html',
        'overview-tree.html',
        'package-frame.html',
        'package-list',
        'package-summary.html',
        'package-tree.html',
        'script.js',
        'stylesheet.css',
        'serialized-form.html'
    ]
    EXCLUDE_FOLDERS = [
        'index-files'
    ]

    def __init__(self):
        self._classes = []

    def parse_folder(self, folder):
        for root, folders, files in os.walk(folder):
            if os.path.basename(root) in self.EXCLUDE_FOLDERS:
                continue
            for file in files:
                path = root+'/'+file
                if os.path.isfile(path) and file not in self.EXCLUDE_FILES:
                    yield self.parse_file(path)

    def parse_file(self, file):
        with open(file, encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f.read(), features='lxml')
            header = soup.find('li', {'class': 'blockList'})
            try:
                package = soup.find('div', {'class': 'subTitle'}).text
            except AttributeError:
                package = ''
            j_class = JavaClass(
                package,
                header.find('span', {'class': 'typeNameLabel'}).text,
                header.find('pre').text.replace('\n', ' ').replace('java.lang.', ''),
                header.find('div', {'class': 'block'}).text
            )
            try:
                constructors = soup.find('a', {'name': 'constructor.detail'}).parent('ul', recursive=False)
            except AttributeError:
                constructors = []
            for constr in constructors:
                j_class.add_constructor(self.parse_one_method(constr.li))

            try:
                method_details = soup.find('a', {'name': 'method.detail'}).parent('ul', recursive=False)
            except AttributeError:
                method_details = []
            for meth in method_details:
                j_class.add_method(self.parse_one_method(meth.li))

            try:
                fields = soup.find('a', {'name': 'field.detail'}).parent.find_all('ul', recursive=False)
            except AttributeError:
                fields = ()
            for field in fields:
                j_class.add_field(self.parse_one_field(field.li))

            return j_class

    def parse_one_field(self, li_elem: bs4.Tag):
        j_field = JavaField(li_elem.pre.text)
        j_field.set_description(
            li_elem.find('div', {'class': 'block'}).decode_contents())
        return j_field

    def parse_one_method(self, li_elem: bs4.Tag):
        children = list(x for x in li_elem.children if x != '\n')
        j_meth = JavaMethod(children[1].text.replace('java.lang.', ''))
        for child in children[2:]:
            if 'class' in child.attrs and 'block' in child.attrs['class']:
                j_meth.set_description(child.decode_contents())
            elif child.name == 'dl':
                self.parse_dl(child, j_meth)
            else:
                print('Unknown', child)
        return j_meth

    AT_TAGS = {
        'Parameters:': '@param',
        'Returns:': '@return',
        'Throws:': '@throws',
        'Specified by:': None,
        'Require:': '@require',
        'Overrides:': 'DECORATOR:@Override',
        'Ensure:': '@ensure'
    }

    def parse_dl(self, dl, meth: JavaMethod):
        current = None
        for c in dl.children:
            if c.name == 'dt':
                current = self.AT_TAGS[c.text]
            elif current is not None and current.startswith('DECORATOR:'):
                meth.add_decorator(current.replace('DECORATOR:', '', 1))
            elif current is not None and c.name == 'dd':
                meth.add_at_tag(current, c.text.replace(' - ', ' ', 1))




if __name__ == '__main__':
    import argparse
    import errno

    arg_parser = argparse.ArgumentParser(
        description='Generates Java method stubs from a JavaDoc folder.')
    arg_parser.add_argument('INPUT', nargs='+', 
        help='input JavaDoc HTML files or directory')
    arg_parser.add_argument('--output-directory', '-o', default='./stub', 
        help='output directory (default: ./stub)')
    arg_parser.add_argument('--indent', '-i', type=int, default=4,
        help='number of spaces to use for indentation (default: 4)')
    arg_parser.add_argument('--todo', '-t', action='store_true',
        help='add TODO comments to methods')
    args = arg_parser.parse_args()
    
    javadoc_parser = JavaDocParser()
    out = []

    for file_or_dir in args.INPUT:
        try:
            out.extend(javadoc_parser.parse_folder(file_or_dir))
        except NotADirectoryError:
            out.append(javadoc_parser.parse_file(file_or_dir))

    os.makedirs(args.output_directory, exist_ok=True)

    for c in out:
        java_file_path = os.path.join(args.output_directory, c.file_path)
        os.makedirs(os.path.dirname(java_file_path), exist_ok=True)
        
        with open(java_file_path, 'w', encoding='utf-8') as f:
            f.write(c.format(**{
                'indent': args.indent, 'todo': args.todo
            }).replace('\xa0', ' ').replace(' ', ' ').replace('<br/>\n', '\n')) 
