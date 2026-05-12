Este script ejecuta el **entrenamiento (fine-tuning)** del modelo YOLOv8 utilizando una estrategia de **Transfer Learning** (Aprendizaje por Transferencia) en dos fases. Su objetivo es adaptar un modelo ya entrenado en objetos genéricos (COCO) para que se especialice en detectar personas desde una perspectiva aérea (VisDrone).

---

## 1. Estrategia de Transfer Learning
El código no entrena el modelo desde cero, sino que aprovecha el conocimiento previo de pesos preentrenados (`yolov8n.pt`). Se divide en dos etapas tácticas:



### Fase 1: Entrenamiento Congelado (Frozen Backbone)
* **Acción:** Se congelan las primeras **10 capas** (`freeze=10`).
* **Lógica:** Estas capas corresponden al "Backbone" (la columna vertebral), encargado de detectar formas básicas como bordes, texturas y colores. Como estas características son universales, no hace falta cambiarlas.
* **Enfoque:** Solo se entrena el "Neck" y el "Head" (las capas finales), que son las responsables de interpretar esas formas para identificar "personas" específicamente en el contexto de drones.

### Fase 2: Ajuste Fino Total (Full Fine-tuning)
* **Acción:** Se descongelan todas las capas (`freeze=0`).
* **Lógica:** Se carga el mejor resultado de la Fase 1 y se permite que **toda la red** se ajuste ligeramente.
* **Precaución:** Se utiliza una tasa de aprendizaje (Learning Rate) mucho más baja (`lr0=1e-4`) para no destruir el conocimiento previo y lograr una convergencia más precisa hacia los detalles del dataset aéreo.

---

## 2. Configuración de Entrenamiento
El script define parámetros específicos para optimizar el rendimiento:

| Parámetro | Valor | Descripción |
| :--- | :--- | :--- |
| **imgsz** | 640 | Re escala las imágenes a 640x640 píxeles. |
| **epochs** | 30 + 20 | Total de 50 épocas de entrenamiento entre ambas fases. |
| **batch** | 16 | Procesa 16 imágenes simultáneamente antes de actualizar pesos. |
| **optimizer** | AdamW | Un optimizador avanzado que gestiona mejor la caída de pesos (weight decay). |

---

## 3. Flujo de Archivos
1.  **Entrada:** Utiliza el archivo `dataset.yaml` generado por el script anterior y los pesos iniciales de YOLOv8n.
2.  **Proceso:**
    * Crea una carpeta de ejecución en `backend/training/runs/phase1_frozen`.
    * Tras terminar, inicia una segunda ejecución en `backend/training/runs/phase2_full`.
3.  **Salida:** El resultado final son los pesos `best.pt` de la fase 2, que representan el modelo optimizado y listo para ser usado en una aplicación de detección.

## 4. Por qué se hace así
Este enfoque de dos fases es estándar en ingeniería de IA (como menciona el comentario sobre el curso de IBM) porque:
1.  **Ahorra tiempo:** Entrenar solo las capas superiores es más rápido inicialmente.
2.  **Previene el olvido catastrófico:** Evita que el modelo pierda su capacidad de reconocer formas básicas al inicio del entrenamiento con datos nuevos.
3.  **Precisión:** El ajuste fino final suele dar un pequeño aumento de precisión (mAP) que es vital en imágenes de drones donde los objetos son muy pequeños.