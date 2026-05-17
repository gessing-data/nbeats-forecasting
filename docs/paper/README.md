# Paper

Este directorio contiene la versión modular del informe en LaTeX. El documento trata, de forma general, sobre pronóstico univariado de demanda eléctrica mediante N-BEATS, con comparación contra ARIMA y evaluación temporal mediante métricas de error. Este README funciona como referencia de trabajo para entender la organización del paper y las convenciones del documento.

## Estructura

- `main.tex`: punto de entrada del documento y archivo que define el orden general del paper.
- `config/`: configuración global de paquetes, formato, bibliografía y bloques de código.
- `metadata/cover-data.tex`: datos editables de portada y metadatos del informe.
- `frontmatter/cover.tex`: composición visual de la portada institucional.
- `sections/`: cuerpo modular del documento.
- `bibliography/references.bib`: base bibliográfica en formato BibTeX/BibLaTeX.
- `assets/`: recursos gráficos usados por el documento.
- `template/`: plantilla institucional de referencia.
- `build/`: directorio esperado durante el desarrollo para la salida de compilación; está ignorado por Git.

## Orden Del Documento

El orden estructural se controla desde `main.tex`:

- Portada: `frontmatter/cover.tex`.
- Introducción: `sections/01-introduccion.tex`.
- Marco teórico: `sections/02-marco-teorico.tex`.
- Método: `sections/03-metodo.tex`.
- Resultados: `sections/04-resultados.tex`.
- Discusión: `sections/05-discusion.tex`.
- Conclusiones: `sections/06-conclusiones.tex`.
- Agradecimientos: `sections/07-agradecimientos.tex`.
- Referencias: generadas con `\printbibliography`.
- Anexos: `sections/08-anexos.tex`.

`main.tex` debe mantenerse como orquestador. Solo debería modificarse cuando cambie el orden estructural del documento o se agregue/elimine una sección principal.

## Configuración

- `config/packages.tex`: paquetes, fuentes, idioma, rutas gráficas y configuración de enlaces.
- `config/document.tex`: márgenes, espaciado, encabezados, pies de página, formato de títulos y profundidad de numeración.
- `config/bibliography.tex`: configuración de `biblatex`, backend `biber`, estilo APA y archivo `.bib` usado por el documento.
- `config/code.tex`: definición del estilo de código y del entorno `codeblock`.
- `metadata/cover-data.tex`: título, autores, correos, asesor, resumen, palabras clave, nombre esperado del archivo final e identificador del proyecto.

Los ajustes de formato o comportamiento global deben hacerse en el archivo de configuración correspondiente, no directamente en las secciones.

## Modularidad

Cada sección principal vive inicialmente como un archivo individual dentro de `sections/`. Si una sección necesita dividirse en módulos más pequeños, se reemplaza el archivo por un directorio con el mismo nombre base y se usa `module.tex` como agregador interno.

Ejemplo:

```text
sections/01-introduccion.tex
```

puede convertirse en:

```text
sections/01-introduccion/
  module.tex
  contexto.tex
  problema.tex
  objetivo.tex
```

En ese caso, `module.tex` debe incluir los submódulos necesarios y `main.tex` debe apuntar únicamente al módulo principal de la sección, no a cada subarchivo interno.

## Referencias

- Las fuentes se registran en `bibliography/references.bib`.
- Las claves deben ser estables, legibles y en minúsculas, por ejemplo `oreshkin2020`, `hyndman2021` o `hong2020`.
- Cada entrada debe conservar los campos bibliográficos relevantes según su tipo: `author`, `title`, `year` y, cuando aplique, `journal`, `booktitle`, `publisher`, `doi` o `url`.
- Se debe preferir `doi` cuando exista. La `url` puede mantenerse cuando facilite la recuperación de la fuente.
- Las citas dentro del texto deben usar comandos de `biblatex`, como `\parencite`, `\textcite` o `\parencites`.
- No se debe escribir bibliografía manual dentro de las secciones.
- Actualmente `main.tex` contiene `\nocite{*}`, por lo que todas las entradas del archivo `.bib` se imprimen aunque no estén citadas explícitamente.

## Requisitos Tecnológicos

- El documento requiere XeLaTeX por el uso de `fontspec`, `polyglossia` y Times New Roman.
- La bibliografía usa `biblatex` con backend `biber` y estilo APA.
- Se espera que `latexmk` gestione las pasadas necesarias de compilación.
- La salida de compilación debe concentrarse en `build/`.
- No cambiar el flujo a pdfLaTeX.
