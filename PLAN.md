# Plan: Migrar Voice2Clip de rumps a PySide6

## TL;DR

Reemplazar la UI actual basada en `rumps` (menu bar minimalista) por una app PySide6 con **icono en la barra de menú + ventana popover elegante** que muestre: botón de grabación, waveform en tiempo real, última transcripción, historial, y configuración. El backend (recorder, transcriber, hotkey, history, sounds) se mantiene **prácticamente intacto** — solo `src/main.py` se reescribe completamente. La arquitectura sigue un patrón **Controller + Views** con Qt signals/slots para comunicación thread-safe, eliminando el hack actual del `SimpleQueue` + timer polling.

Solo 4 de 23 tests se rompen (los que mockean `rumps`). PySide6 funciona en macOS y Windows, preparando el camino para soporte cross-platform futuro.

---

## Arquitectura nueva
src/
main.py → Entry point: QApplication + wiring
app_controller.py → NEW: lógica de negocio (state machine) extraída de main.py
recorder.py → +3 líneas: callback de nivel de audio (RMS)
transcriber.py → SIN CAMBIOS
history.py → SIN CAMBIOS
sounds.py → SIN CAMBIOS
hotkey_handler.py → SIN CAMBIOS
ui/
init.py
tray_manager.py → QSystemTrayIcon + menú contextual
popover_window.py → Ventana frameless anclada al tray
main_view.py → Vista principal: botón rec + waveform + última transcripción
history_view.py → Lista de transcripciones con botones de copiar
settings_view.py → Panel de configuración inline
waveform_widget.py → Widget custom pintando niveles de audio en tiempo real
theme.py → QSS styles + detección dark/light mode
resources.py → Carga de iconos y recursos
icons/ → Los mismos 8 PNGs actuales


---

## Steps

### Paso 1 — Extraer lógica de negocio a `app_controller.py`

Crear un nuevo archivo `src/app_controller.py` que sea un `QObject` con toda la lógica del estado extraída de `src/main.py`:

- Mover el `AppState` enum y la máquina de estados (`_state`, `_state_lock`, `_transition_state`, `_get_state`, `_set_state`)
- Mover `toggle_recording()`, `_start_recording()`, `_stop_and_process()`, `_process_audio()`, `_finish_processing()`
- Mover `_maybe_cleanup_audio()` y `_on_silence_detected()`
- Definir **Qt signals** para comunicar cambios al UI:
  - `state_changed(AppState)` — para actualizar iconos, botones, textos
  - `audio_level(float)` — para el waveform en tiempo real
  - `transcription_ready(str)` — cuando el texto está listo
  - `error_occurred(str)` — para errores
  - `history_updated()` — cuando cambia el historial
- El controller es **dueño** de `AudioRecorder`, `GeminiTranscriber`, `HotkeyHandler`
- Reemplazar el patrón `SimpleQueue` + timer por `QMetaObject.invokeMethod` o signals cross-thread (nativos de Qt)

### Paso 2 — Modificar `recorder.py` para emitir niveles de audio

En `src/recorder.py`, cambio mínimo (~3 líneas):

- Añadir parámetro opcional `level_callback: Callable[[float], None] | None = None` al método `start()`
- En `_record_loop()`, después de calcular RMS (que ya se hace para detección de silencio), invocar `self._level_callback(rms)` si está definido
- Esto entrega ~15 valores RMS por segundo (1024 samples @ 16kHz ≈ 64ms por chunk)

### Paso 3 — Crear el sistema de tray (`ui/tray_manager.py`)

- `QSystemTrayIcon` con los iconos actuales de `src/icons/`
- Usar `QIcon.setIsMask(True)` para replicar el comportamiento de "Template images" de macOS (auto dark/light mode)
- Menú contextual derecho: "Start/Stop Recording", separador, "Quit"
- Click izquierdo: toggle de la ventana popover
- Cambio dinámico de icono según estado (`idle`, `rec`, `process`, `success`) — mismo flujo que el actual

### Paso 4 — Crear la ventana popover (`ui/popover_window.py`)

- `QWidget` frameless (`Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint`)
- Posicionada justo debajo del icono del tray (obtener geometría con `QSystemTrayIcon.geometry()`)
- Bordes redondeados con QSS + `setAttribute(Qt.WA_TranslucentBackground)`
- Sombra sutil con `QGraphicsDropShadowEffect`
- Tamaño: ~320×480px
- Contiene un `QStackedWidget` con 3 vistas: Main, History, Settings
- Barra de navegación inferior con 3 iconos/tabs
- Se cierra al perder foco (`focusOutEvent`) o al hacer click fuera

### Paso 5 — Vista principal (`ui/main_view.py`)

Layout vertical:

1. **Estado** — Texto descriptivo: "Listo", "Grabando...", "Procesando..."
2. **Botón de grabación** — Botón circular grande. Idle: micrófono gris. Grabando: rojo pulsante (animación `QPropertyAnimation`). Procesando: spinner
3. **Waveform** — Widget custom visible solo durante grabación (ocupa ~80px de alto)
4. **Última transcripción** — `QLabel` con el texto de la última transcripción, truncado con "..." si es largo. Click para copiar. Icono de clipboard al lado
5. **Hotkey hint** — Texto sutil: "Ctrl × 2 para grabar"

### Paso 6 — Widget de waveform (`ui/waveform_widget.py`)

- Custom `QWidget` que sobreescribe `paintEvent()`
- Mantiene un ring buffer circular de los últimos ~60 valores RMS
- Pinta barras verticales (estilo visualizador de audio) con gradiente de color
- Conectado a la señal `audio_level(float)` del controller
- Animación suave con `QTimer` de 60fps para interpolar entre valores
- Se esconde cuando no se está grabando

### Paso 7 — Vista de historial (`ui/history_view.py`)

- `QScrollArea` con lista de transcripciones
- Cada ítem: timestamp (relativo: "hace 2 min"), texto (truncado), botón de copiar
- Click en un ítem: expande el texto completo
- Usa `history.get_recent(10)` — polling con `QTimer` cada 2s (como el actual)
- Items copiables: click en botón copia al clipboard con feedback visual

### Paso 8 — Vista de configuración (`ui/settings_view.py`)

- Controles para todas las variables de entorno actuales:
  - **Silence timeout** (slider, 1-10s, default 3s)
  - **Silence threshold** (slider, 200-2000, default 800)
  - **History enabled** (toggle switch)
  - **Max history items** (spinbox, 10-200)
  - **Audio retention** (toggle: keep/delete)
- Los valores se guardan en `~/.voice2clip.env` o un nuevo `~/.voice2clip_config.json`
- Aplicar cambios en caliente sin reiniciar la app

### Paso 9 — Theme y estilos (`ui/theme.py`)

- Detectar si macOS está en dark o light mode (`QApplication.palette()` o `NSAppearance`)
- Stylesheet QSS global con variables de color:
  - Dark: fondo `#1E1E1E`, texto `#FFFFFF`, acento `#007AFF` (azul macOS)
  - Light: fondo `#F5F5F7`, texto `#1D1D1F`, acento `#007AFF`
- Bordes redondeados, spacing consistente, tipografía San Francisco (nativa macOS)
- Animaciones sutiles en botones y transiciones

### Paso 10 — Reescribir `main.py` como entry point

Nuevo `src/main.py`:

- Crear `QApplication` con `app.setQuitOnLastWindowClosed(False)` (imprescindible para apps de tray)
- Instanciar `AppController`
- Instanciar `TrayManager` y `PopoverWindow`
- Conectar signals del controller a slots de los widgets
- Conectar acciones de UI (botón rec) a métodos del controller
- Arrancar el `HotkeyHandler`
- `app.exec()`

### Paso 11 — Actualizar `pyproject.toml` y dependencias

En `pyproject.toml`:

- Reemplazar `rumps>=0.4.0` por `PySide6>=6.7.0`
- Mantener todas las demás dependencias
- Opcionalmente añadir `qt-material` si se quiere un theme Material Design alternativo

### Paso 12 — Actualizar build system

En `build_app.py` y `Voice2Clip.spec`:

- Actualizar PyInstaller hiddenimports para PySide6
- Asegurar que los iconos y recursos Qt se incluyen en el bundle
- PySide6 con PyInstaller requiere un hook especial (`--collect-all PySide6` o similar)
- Mantener la firma de código y entitlements

### Paso 13 — Actualizar tests

- Los 19 tests que no tocan rumps: **sin cambios**
- `tests/test_main_state.py` (3 tests): migrar a testear `AppController` directamente (más limpio que antes, ya no hay que hackear `__new__`)
- `tests/test_main_integration_flow.py` (4 tests): reescribir mocks para PySide6 (`QSystemTrayIcon`, notificaciones) y testear el flujo a través de `AppController`

### Paso 14 — Actualizar README y documentación

- Actualizar `README.md` con screenshots nuevos
- Documentar la nueva arquitectura
- Actualizar instrucciones de instalación (PySide6 puede necesitar `brew install qt@6`)

---

## Verificación

1. **Unit tests**: `pytest tests/` — los 19 tests de backend deben pasar sin cambios. Los 4 reescritos deben pasar
2. **Manual — flujo completo**: Doble-Ctrl → graba → se ve waveform → para → transcribe → texto aparece en popover + clipboard
3. **Manual — UI**: Click en tray → popover aparece bien posicionada → tabs funcionan → historial se muestra → settings se guardan
4. **Manual — dark/light mode**: Cambiar apariencia del sistema → icono y popover se adaptan
5. **Manual — edge cases**: Transcripción vacía, error de red, API key inválida → mensajes de error apropiados
6. **Build**: `python build_app.py` → genera `Voice2Clip.app` funcional con PySide6 empaquetado

---

## Decisiones

- **PySide6 sobre PyQt6**: Licencia LGPL más permisiva (vs GPL de PyQt). API idéntica
- **Controller pattern sobre monolito**: Separar lógica de negocio (`AppController`) de la UI facilita testing y futuro soporte Windows
- **Qt signals sobre SimpleQueue**: Mecanismo nativo de Qt para comunicación cross-thread, elimina el timer de polling cada 100ms
- **QIcon.setIsMask(True) sobre template images**: Equivalente Qt del comportamiento de macOS template images para dark/light mode
- **Config JSON sobre .env para settings**: Los settings del usuario se guardan en `~/.voice2clip_config.json` (estructurado) mientras la API key sigue en `.env` (seguridad)
- **Sin `qt-material`** de momento: QSS custom para un look más nativo macOS. Se puede añadir después si se quiere Material Design