# Paper

Este directorio contiene la versi\'on modular del informe en LaTeX, ajustada para trabajar con `XeLaTeX`, `biblatex + biber` y una portada alineada con la plantilla institucional.

## Estructura

- `main.tex`: archivo orquestador.
- `config/`: paquetes y configuraci\'on global del documento.
- `metadata/cover-data.tex`: datos editables de la portada.
- `frontmatter/cover.tex`: composici\'on de la portada.
- `sections/`: secciones modulares del informe.
- `bibliography/references.bib`: referencias bibliogr\'aficas.
- `build/`: salida de compilaci\'on.

## Compilaci\'on

Desde `docs/paper/`:

```powershell
latexmk main.tex
```

Para limpiar manualmente la salida:

```powershell
latexmk -C main.tex
```
