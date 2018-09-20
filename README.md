# JavaDoc Stub Generator

A Python tool for generating Java stub files when given a JavaDoc.

## Features
 - Generates Java source files which compile.
 - Copies JavaDoc comments and tags (almost) exactly, including HTML.
    - Understands `@param`, `@return`, `@throws`, `@require` and `@ensure`.
 - Optionally inserts `TODO` comments.
 - Inserts `@Override` for overidden methods.
 - Indentation of classes and functions.
 - Inserts `package` declaration and creates correct folder structure.
 - Differentiates between interface/abstract methods and regular methods.

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

## Example Output
```java
package csse2002.block.world;

/**
 * Represents a position on the grid.
 */
public class Position extends Object {

    /**
     * Constructs a position of (x, y).
     * @param x the x coordinate.
     * @param y the y coordinate.
     */
    public Position(int x,
                    int y) {
        // TODO: Implement method Position(int, int)
        
    }

    /**
     * Gets the x coordinate.
     * @return the x coordinate.
     */
    public int getX() {
        // TODO: Implement method getX()
        return 0;
    }

    /**
     * Gets the y coordinate.
     * @return the y coordinate.
     */
    public int getY() {
        // TODO: Implement method getY()
        return 0;
    }
}
```