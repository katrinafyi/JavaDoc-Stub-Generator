# JavaDoc Stub Generator
```
usage: javadoc_stubs.py [-h] [--output-directory OUTPUT_DIRECTORY]
                        [--indent INDENT] [--todo]
                        INPUT [INPUT ...]

Generates Java method stubs from a JavaDoc folder.

positional arguments:
  INPUT                 input JavaDoc HTML files or directory

optional arguments:
  -h, --help            show this help message and exit
  --output-directory OUTPUT_DIRECTORY, -o OUTPUT_DIRECTORY
                        output directory (default: ./stub)
  --indent INDENT, -i INDENT
                        number of spaces to use for indentation (default: 4)
  --todo, -t            add TODO comments to methods
```