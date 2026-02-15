# Guía Definitiva: Iconos de Barra de Menú en macOS (Python/Rumps)

Esta guía detalla las especificaciones exactas para lograr iconos de barra de menú ("status bar items") que se vean 100% nativos, nítidos en pantallas Retina y soporten automáticamente el cambio de modo claro/oscuro en macOS.

## 1. Especificaciones Técnicas (La Regla de Oro)

Para que un icono se vea perfecto en pantallas Retina (la mayoría de los Macs actuales), debes diseñar pensando en **@2x** (escala x2). macOS escala automáticamente hacia abajo, pero necesitas la resolución alta para la nitidez.

### Dimensiones Exactas

| Propiedad | Valor Exacto (Retina @2x) | Valor Estándar (No-Retina) | Notas |
|-----------|---------------------------|----------------------------|-------|
| **Tamaño del Lienzo (Canvas)** | **44 x 44 px** | 22 x 22 px | El archivo PNG debe tener este tamaño total. |
| **Tamaño del Icono (Visual)** | **Max 36 px** de alto | Max 18 px de alto | Mantén un margen "padding" alrededor. |
| **Color** | **Negro Puro (#000000)** | Negro Puro | Fondo 100% transparente. |
| **Formato** | **PNG** (con canal Alpha) | PNG | |

> **Nota Crítica:** La barra de menú tiene una altura lógica de ~22pt.
> 22pt × 2 (factor Retina) = **44px**. 
> Si tu icono ocupa los 44px completos sin margen, tocará los bordes de la pantalla. **Deja espacio.**

### Diseño Recomendado
En un lienzo de **44x44 px**:
1.  Dibuja tu icono (ej. micrófono) centrado.
2.  La altura del dibujo (glifo) debe ser aproximadamente **32px - 34px**.
3.  Deja al menos **5px - 6px** de espacio vacío arriba y abajo en el lienzo.

---

## 2. Modo Oscuro Automático (Template Images)

Para que macOS invierta el color automáticamente (Negro en modo claro, Blanco en modo oscuro), el sistema debe tratar la imagen como una **"Template Image"**.

### Cómo funciona
Una "Template Image" utiliza solo el canal Alfa (transparencia).
-   Los píxeles **Negros (#000000)** se pintarán del color del texto del sistema.
-   La opacidad se respeta.
-   Cualquier otro color puede romper el efecto.

### Naming Convention
Añade el sufijo `_Template` al nombre del archivo (`icon_Template.png`). Esto ayuda a identificar el propósito del archivo y es una convención en desarrollo macOS/iOS.

---

## 3. Obtener Iconos Nativos (SF Symbols)

Instrucciones paso a paso para obtener el icono "mic" oficial de Apple.

### Paso 1: Descargar SF Symbols
Si no lo tienes, usa la app gratuita [SF Symbols de Apple](https://developer.apple.com/sf-symbols/).

### Paso 2: Exportar y Preparar
1.  Abre **SF Symbols** y busca `"mic"` o `"mic.fill"`.
2.  Selecciona el icono. Elige peso **Medium** o **Semibold**.
3.  **Método Rápido (Screenshot/Copy):**
    *   Copia el símbolo (`Cmd+C`).
    *   Pégalo en tu editor gráfico favorito (Pixelmator, Photoshop, Figma).
    *   Crea un lienzo nuevo de **44x44 px**.
    *   Pega y centra el icono. Asegúrate de que su altura sea ~32px.
    *   **Importante:** Asegúrate de que el color sea **Negro Puro (#000000)**.
    *   Exporta como **PNG**.

4.  **Método Pro (Exportar Template):**
    *   File > **Export Symbol...**. Esto genera un SVG.
    *   Abre el SVG en un editor vectorial.
    *   Exporta a PNG con altura de 44px.

---

## 4. Implementación Correcta en Python (Rumps)

Aquí está el código exacto para cargar el icono correctamente.

### Estructura de Archivos
```text
src/
├── main.py
└── icons/
    └── mic_Template.png  <-- Tu imagen de 44x44px
```

### Código Python ("minúsculo")

```python
import rumps

class MyApp(rumps.App):
    def __init__(self):
        super().__init__("App Name", icon="icons/mic_Template.png", template=True)
        # template=True es OBLIGATORIO para el modo oscuro automático.
```

### Solución de Problemas Comunes

1.  **El icono se ve gigante:** Tu lienzo es demasiado grande o no tiene margen. Redimensiona el lienzo a 44x44px.
2.  **El icono no cambia de color en modo oscuro:**
    *   Asegúrate de usar `template=True` en `rumps.App()`.
    *   Asegúrate de que la imagen sea **solo negro y transparente**. Si tiene grises o blancos "quemados", macOS no la coloreará bien.
3.  **Aparece texto en vez de icono:**
    *   Revisa tu código. `self.title = "ruta/al/icono.png"` mostrará la ruta como texto.
    *   Usa `self.icon = "ruta/al/icono.png"`.

---

## Checklist Final
- [ ] Archivo PNG de **44x44 píxeles**.
- [ ] Icono negro puro sobre fondo transparente.
- [ ] Icono centrado con ~5px de margen arriba/abajo.
- [ ] Nombre del archivo: `algo_Template.png`.
- [ ] Código: `template=True` y usar `self.icon`.
