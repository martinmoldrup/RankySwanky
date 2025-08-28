# Installing Graphviz on Windows
Install Graphviz, using installer.
Validate using `dot -V` in your terminal.

Compilers need additional environment variables to find Graphviz headers and libraries.:

``` powershell
$env:INCLUDE="C:\Program Files\Graphviz\include"
$env:LIB="C:\Program Files\Graphviz\lib"
$env:PATH="$env:PATH;C:\Program Files\Graphviz\bin"
```