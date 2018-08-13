import bs4
import os
from collections import defaultdict

def _lazy_str(self):
    return self.__class__.__name__ + '('+', '.join((x+'='+repr(y)) for x, y in self.__dict__.items())+')'

def javadoc_comment(comment, at_tags={}):
    at_tags_str = '\n'.join(
        tag + ' ' + (text) for tag, texts in at_tags.items() for text in texts
    )
    comment = comment.replace('\n ', '\n')
    return ('/**\n'+comment.rstrip()+'\n'+at_tags_str).replace('\n', '\n * ').rstrip()+'\n */'



class JavaClass:
    def __init__(self, name, definition, description):
        self.name = name
        self._definition = definition
        self._desc = description
        self._constructors = []
        self._methods = []

    def add_constructor(self, method):
        self._constructors.append(method)

    def add_method(self, method):
        self._methods.append(method)

    def format(self):
        interface = 'interface ' in self._definition
        ret = [javadoc_comment(self._desc), self._definition + ' {']
        ret.append('')
        for c in self._constructors + self._methods:
            ret.extend(c.format(interface))
            ret.append('')
        ret.append('}')
        return '\n'.join(ret)

    __repr__ = __str__ = _lazy_str

class JavaMethod:

    def __init__(self, definition):
        self._definition = definition
        self._at_tags = {
            '@param': [],
            '@throws': [],
            '@return': [],
        }
        self._description = ''

    def add_at_tag(self, tag, text):
        self._at_tags[tag].append(text)

    def set_description(self, description):
        self._description = description

    def format(self, interface=False):
        return [
            javadoc_comment(self._description, self._at_tags),
            self._definition + (';' if interface else ' {}')
        ]


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
        'stylesheet.css'
    ]
    def __init__(self):
        self._classes = []

    def parse_folder(self, folder):
        for file in os.listdir(folder):
            path = folder+'/'+file
            if os.path.isfile(path) and file not in self.EXCLUDE_FILES:
                yield self.parse_file(path)

    def parse_file(self, file):
        with open(file, encoding='utf-8') as f:
            soup = bs4.BeautifulSoup(f.read(), features='lxml')
            header = soup.find('li', {'class': 'blockList'})
            j_class = JavaClass(
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
            return j_class

    def parse_one_method(self, li_elem: bs4.Tag):
        children = list(x for x in li_elem.children if x != '\n')
        j_meth = JavaMethod(children[1].text.replace('java.lang.', ''))
        for child in children[2:]:
            if 'class' in child.attrs and 'block' in child.attrs['class']:
                j_meth.set_description(child.encode_contents().decode('utf-8'))
            elif child.name == 'dl':
                self.parse_dl(child, j_meth)
            else:
                print('Unknown', child)
        return j_meth

    AT_TAGS = {
        'Parameters:': '@param',
        'Returns:': '@return',
        'Throws:': '@throws',
        'Specified by:': None
    }

    def parse_dl(self, dl, meth: JavaMethod):
        current = None
        for c in dl.children:
            if c.name == 'dt':
                current = self.AT_TAGS[c.text]
            elif current is not None and c.name == 'dd':
                meth.add_at_tag(current, c.text.replace(' - ', ' ', 1))




if __name__ == '__main__':
    out = JavaDocParser().parse_folder(os.path.dirname(__file__) + '/../Csse2002_Ass1/javadoc2')

    for c in out:
        with open(os.path.dirname(__file__) + '/../Csse2002_Ass1/stub/'+c.name+'.java', 'w', encoding='utf-8') as f:
            f.write(c.format().replace('\xa0', ' ').replace(' ', ' '))