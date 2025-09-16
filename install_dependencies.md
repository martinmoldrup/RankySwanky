# Installing Graphviz on Windows for using erdantic for creating ER diagrams
Install Graphviz, using installer: https://graphviz.org/download/ or in windows you can use winget:

``` powershell
winget install -e --id Graphviz.Graphviz
```

Validate using `dot -V` in your terminal, you might need to restart your terminal, or sign our and in again on you windows account for PATH changes to take effect.

Compilers need additional environment variables to find Graphviz headers and libraries, do this first if installing the erdantic (pygraphviz) package is failing.

``` powershell
$env:INCLUDE="C:\Program Files\Graphviz\include"
$env:LIB="C:\Program Files\Graphviz\lib"
$env:PATH="$env:PATH;C:\Program Files\Graphviz\bin"
uv add erdantic
```