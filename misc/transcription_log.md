# Registro de Pruebas de Transcripción - Voice2Clip

Resumen de las pruebas de latencia realizadas con la API de Google Gemini para transcripción de audio.

## Configuración
- **Fecha:** 15 Febrero 2026
- **Modelo Inicial:** `gemini-3-flash-preview`
- **Modelo Final:** `gemini-2.5-flash-lite`
- **Formato:** WAV 16kHz Mono

## Resultados de Latencia (Gemini 3 Flash Preview)

| Prueba | Duración Audio | Tamaño | Latencia API | Caracteres | Ratio (Tiempo/Audio) |
|--------|---------------:|-------:|-------------:|-----------:|---------------------:|
| 1      | ~13s           | 412 KB | **16s**      | 116        | 1.23x (Lento)        |
| 2      | ~50s           | 1.5 MB | **74s**      | 556        | 1.48x (Muy Lento)    |
| 3      | ~88s           | 2.7 MB | **20s**      | 1016       | 0.22x (Rápido*)      |

> *Nota: La prueba 3 fue extrañamente rápida comparada con las anteriores, posible calentamiento de caché o variabilidad del endpoint preview.*

## Acciones Tomadas
1. **Cambio de Modelo:** Se ha migrado a `gemini-2.5-flash-lite` para buscar latencias consistentemente bajas (<1-2s para frases cortas).
2. **Optimización de Prompt:** Se ha reescrito el prompt del sistema para actuar como "Prompt Engineer" cuando detecta instrucciones, eliminando divagaciones y formateando la salida.
