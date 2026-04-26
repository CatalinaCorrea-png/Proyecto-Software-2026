Este script procesa el dataset **VisDrone2019-DET** para convertir sus anotaciones al formato requerido por los modelos **YOLO**, filtrando los datos para enfocarse exclusivamente en la detección de personas.

---

## 1. Objetivo del Script
El código realiza una reestructuración y conversión de datos para que un modelo YOLO pueda ser entrenado únicamente para reconocer la clase "persona", ignorando otros objetos presentes en VisDrone como coches, camiones o bicicletas.

## 2. Lógica de Filtrado y Mapeo
VisDrone tiene múltiples categorías. Este script selecciona específicamente dos y las unifica en una sola:
* **Categoría 1 (pedestrian):** Mapeada a la clase YOLO `0`.
* **Categoría 2 (people):** Mapeada a la clase YOLO `0`.
* **Resto de categorías:** Se ignoran.
* **Filtro de visibilidad:** Solo procesa objetos donde `score` sea distinto de 0 (objetos válidos).

## 3. Transformación de Coordenadas
El script realiza una conversión matemática crítica, ya que los formatos de anotación son distintos:

| Característica | Formato VisDrone (Origen) | Formato YOLO (Destino) |
| :--- | :--- | :--- |
| **Referencia** | Píxeles absolutos | Valores normalizados (0.0 a 1.0) |
| **Punto de anclaje** | Esquina superior izquierda ($x_{left}, y_{top}$) | Centro del objeto ($x_{center}, y_{center}$) |
| **Cálculo X** | $x$ | $(x + w/2) / \text{ancho\_imagen}$ |
| **Cálculo Y** | $y$ | $(y + h/2) / \text{alto\_imagen}$ |



## 4. Estructura de Salida
El script organiza los archivos en una estructura jerárquica compatible con Ultralytics (YOLOv8/v10/v11):

* **`images/`**: Contiene las imágenes originales copiadas (solo de aquellas que contienen personas).
* **`labels/`**: Contiene archivos `.txt` con las nuevas coordenadas normalizadas.
* **`dataset.yaml`**: Archivo de configuración que indica a YOLO dónde están los datos y que solo existe 1 clase (`nc: 1`) llamada `person`.

## 5. Flujo de Ejecución
1.  **Iteración:** Recorre las carpetas de `train` y `val`.
2.  **Validación:** Abre cada imagen para obtener sus dimensiones (necesarias para la normalización).
3.  **Conversión:** Lee el archivo `.txt` de VisDrone, filtra las clases 1 y 2, y calcula las nuevas coordenadas.
4.  **Limpieza:** Si una imagen no contiene personas, la ignora (`skipped`) para evitar alimentar al modelo con ejemplos vacíos de esa clase.
5.  **Escritura:** Guarda las nuevas etiquetas y genera el archivo `.yaml`.