# 🎤 Speech — Presentación Final AeroSearch AI (versión unificada + FODA)

> Guion para presentar `presentacion_unificada_aerosearch.html` (10 slides).
> Tono natural, rioplatense. Duración aproximada: **9–11 minutos**.

---

## SLIDE 01 — Portada *(quien abre)*

> "Buenas tardes a todos. Somos el Grupo 1 y venimos a presentarles **AeroSearch AI**, el proyecto en el que trabajamos durante todo el cuatrimestre.
>
> AeroSearch es un sistema de **búsqueda y rescate con drones**, que combina visión artificial y telemetría en tiempo real. En una sola plataforma integramos tres mundos que normalmente van por separado: el backend en Python, el frontend en React, y el hardware con un ESP32. Y arriba de todo eso, un modelo de IA propio para detectar personas.
>
> Déjenme empezar por el porqué."

*(bajar a slide 2)*

---

## SLIDE 02 — El problema

> "El problema que quisimos atacar es uno bien concreto: **buscar personas en zonas extensas lleva demasiado tiempo**. Y en rescate, el tiempo es literalmente la diferencia entre encontrar a alguien o no.
>
> Estos tres números lo resumen: hay una **ventana crítica de 72 horas** después de la cual las probabilidades de supervivencia caen muchísimo. En operaciones reales, hasta un **80% del área queda sin cubrir** en las primeras horas. Y el ratio de rescatistas es de apenas **uno cada 50 km²**.
>
> Hoy eso se resuelve con equipos a pie, celda por celda, sin visión nocturna ni térmica, con fatiga acumulada. Y las aeronaves tripuladas son caras y no siempre están disponibles.
>
> Nuestra propuesta es un **drone autónomo** que recorre una grilla de búsqueda de forma sistemática, detecta personas con inteligencia artificial y manda **alertas geolocalizadas en tiempo real** a un centro de comando web. Que el operador no tenga que mirar el video: que el sistema le avise."

*(bajar a slide 3)*

---

## SLIDE 03 — El equipo

> "Detrás de esto estuvimos **seis personas**: Catalina, Nicolás, Dana, Maximiliano, Fernanda y Martín. Trabajamos con **Scrum a lo largo de 6 sprints**, todos tocando backend, frontend, hardware e IA — no nos encasillamos en un solo rol.
>
> En el roadmap pueden ver cómo fue creciendo: arrancamos en el Sprint 1 con el setup, los repos, el CI y el primer mapa. En el 2 sumamos WebSocket, telemetría y YOLO. En el 3, las bases de datos y Docker. En el 4, historial, estadísticas y control manual. En el 5 — el más fuerte — logramos el **movimiento autónomo y la conexión real entre hardware y software**. Y nos queda el Sprint 6, donde vamos por roles de usuario, modo solo lectura y tests end-to-end."

*(bajar a slide 4)*

> 💡 *Nota: las iniciales de cada integrante se reemplazan por la foto si está en `docs/team/` (`catalina.jpg`, `nicolas.jpg`, `dana.jpg`, `maximiliano.jpg`, `fernanda.jpg`, `martin.jpg`).*

---

## SLIDE 04 — Arquitectura

> "Técnicamente, AeroSearch es una **arquitectura de tres capas**.
>
> El **Frontend**, en React 19 con TypeScript, es el dashboard en tiempo real: mapa, video, telemetría, alertas y estadísticas.
>
> El **Backend**, en FastAPI, es el cerebro: corre la visión artificial con YOLOv8, el motor de grilla, la simulación de vuelo y maneja las dos bases de datos.
>
> Y la capa de **Hardware**, el firmware del ESP32 en C++, con GPS, control PID de los motores, cámara y telemetría.
>
> Lo interesante es **cómo se comunican**: el frontend habla con el backend por **WebSocket y REST**, y el backend habla con el drone por **UDP bidireccional** — UDP porque para telemetría necesitábamos baja latencia. Cada capa está modularizada: cada bloque hace una sola cosa, y eso fue clave para trabajar de a seis sin pisarnos."

*(bajar a slide 5)*

---

## SLIDE 05 — Funcionalidades

> "¿Qué hace el sistema, de punta a punta? Estas son las funcionalidades principales:
>
> - **Telemetría en tiempo real** — posición, altitud, velocidad y batería, por WebSocket.
> - **Detección con IA** — YOLOv8 sobre la imagen RGB, fusionada con una simulación térmica, que clasifica cada detección en confianza alta, media o baja.
> - **Mapa interactivo con grilla** — con el trail de vuelo y las celdas pintándose a medida que se exploran.
> - **Control manual** con joystick virtual, por si el operador quiere tomar el mando.
> - **Galería de capturas** que se guardan solas al detectar a alguien, con sus bounding boxes.
> - **Historial y estadísticas** de cada misión.
> - **Video multi-fuente** — webcam, el ESP32, un archivo o YouTube, cambiable por configuración.
> - Y todo se levanta con **Docker Compose**, un solo comando.
>
> No quiero detenerme en cada una; lo importante es que es un sistema **completo**, no una demo de una sola feature."

*(bajar a slide 6)*

---

## SLIDE 06 — Flujo de una misión *(con escenario real)*

> "Para que se entienda cómo se usa, sigamos una misión de principio a fin — y en cada paso, fíjense en la etiqueta verde de qué cambiaría **en un escenario real**:
>
> **Uno — Configurar.** El operador define nombre, coordenadas GPS, altitud y grilla. *En real*, el coordinador delimita la zona de búsqueda en segundos, sin planear rutas a mano.
>
> **Dos — Vuelo y barrido.** El drone recorre la grilla en serpentina y el mapa pinta las celdas exploradas. *En real*, cubre en minutos terreno que a pie llevaría horas — incluso de noche o en zona inaccesible.
>
> **Tres — Detección en tiempo real.** Cada frame pasa en paralelo por YOLO y por el térmico; si la confianza es media o alta, salta la alerta geolocalizada. *En real*, el rescatista no tiene que mirar el video: el sistema le dice dónde mirar, y eso **reduce el error humano por fatiga**.
>
> **Cuatro — Reporte.** Queda todo guardado: cobertura, batería, detecciones. *En real*, deja trazabilidad de qué se cubrió y dónde, útil para coordinar relevos y auditar la operación.
>
> Y la foto completa: AeroSearch convierte una búsqueda **lenta, peligrosa y dependiente de gente** en una **sistemática, geolocalizada y trazable** — ampliando el área cubierta por hora y liberando a los equipos humanos para que actúen solo donde hay una detección concreta, ganando minutos dentro de esa ventana crítica de 72 horas."

*(bajar a slide 7)*

---

## SLIDE 07 — FODA del proyecto

> "Ahora bien, además de construir, nos paramos a **mirar el proyecto con honestidad**, y para eso hicimos un análisis FODA.
>
> En **Fortalezas** teníamos cosas reales: IA propia con YOLO, un stack moderno, hardware funcionando, arquitectura dockerizada y un equipo trabajando con sprints.
>
> En **Debilidades** fuimos autocríticos: al momento del análisis teníamos **poca cobertura de tests**, seguridad sin implementar, un `main.py` monolítico de 900 líneas, los modelos pesados versionados en git y dos bases de datos sin una estrategia escrita.
>
> En **Oportunidades** vimos el horizonte: el salto a hardware real, ampliar el dashboard, mejorar el modelo con datos de cada misión, e integraciones con servicios de emergencia.
>
> Y en **Amenazas**, lo que nos rodea y no controlamos del todo: la dependencia del hardware, la latencia del ML sin medir, la deuda técnica que se acumula, los datos sensibles sin cifrar y un CI/CD incompleto."

*(bajar a slide 8)*

---

## SLIDE 08 — Del diagnóstico a la acción + Testing

> "Pero lo importante es que **el FODA no quedó en un dibujo bonito**: lo usamos como backlog. Nos dio prioridades, y atacamos primero las debilidades internas, las que sí controlábamos.
>
> La **prioridad número uno fue el testing**. Pasamos de prácticamente no tener tests a una **suite con pytest de 6 módulos**: fusión, grilla, modelos, estado, el detector térmico y — clave — las **rutas críticas de misiones**. Y algo importante: pudimos testear porque antes **modularizamos**. Un `main.py` de 900 líneas es intesteable; separado en piezas, cada una se prueba aislada. Los tests end-to-end quedan para el Sprint 6, y cierran el ciclo.
>
> En paralelo atacamos el resto: el `main.py` pasó de **904 a 56 líneas**, sacamos las credenciales del código con un `.env.example`, y dejamos el manejo de las dos bases explícito y ordenado. Lo que queda — Git LFS para los modelos, autenticación y CI/CD completo — lo dejamos **anotado a propósito** como deuda consciente, no olvidada.
>
> Y esa es la conclusión del FODA: convirtió **percepciones difusas en un backlog priorizado**. No solo describió el proyecto — **cambió cómo trabajamos**."

*(bajar a slide 9)*

---

## SLIDE 09 — Aprendizajes y conclusiones *(foco ágil)*

> "¿Qué nos llevamos de todo esto? Más que código, una **forma de trabajar**.
>
> Aprendimos **Scrum en serio, no de adorno** — planning, review y retro en cada sprint. Y entendimos que un **backlog vivo y priorizado vale más que un plan rígido de cuatro meses**.
>
> Aprendimos que **priorizar es decidir qué NO hacer**: el FODA y el backlog nos enseñaron a elegir lo de mayor impacto y postergar el resto a conciencia, en vez de querer todo a la vez.
>
> Aprendimos a **iterar y adaptarnos** — casi nada salió bien a la primera. Entregar algo simple, mostrarlo en la review y mejorarlo al sprint siguiente fue mucho más efectivo que buscar la perfección desde el arranque.
>
> Y aprendimos a **trabajar en equipo de verdad**: seis personas en un repo, con branches, pull requests, code reviews y conflictos de merge — comunicándonos cuando algo se rompía en lugar de arreglarlo en silencio.
>
> La conclusión es esta: un proyecto grande **no se sostiene por talento individual, sino por proceso**. Las metodologías ágiles dejaron de ser teoría de parcial: las **vivimos**. El FODA nos dio el mapa, el backlog las prioridades y las retros la mejora continua. Nos llevamos un producto que funciona — y, sobre todo, una manera de trabajar que podemos repetir en cualquier equipo."

*(bajar a slide 10)*

---

## SLIDE 10 — Cierre

> "Para cerrar: AeroSearch pasó de ser **una idea en un Sprint Planning** a un producto funcional con drone, IA, mapa en tiempo real y despliegue containerizado.
>
> En números: **6 sprints, 6 integrantes, 3 capas de tecnología, 2 bases de datos y 6 módulos de tests** — y un FODA que convertimos en backlog.
>
> Estamos muy orgullosos de lo que construimos, y lo más lindo es que cada una de estas funcionalidades hoy **anda**.
>
> Muchas gracias — y quedamos para las preguntas que quieran hacernos."

---

## Notas para la exposición

- **Ritmo:** las slides 4 y 5 son las más densas; las 7 y 8 (FODA) son el corazón de la parte de proceso. Si vas corto de tiempo, en la 5 nombrá 3 features y seguí, y en la 7 leé solo un par de puntos por cuadrante (el resto está en pantalla).
- **Reparto sugerido (6 personas):** 1–2 quien abre · 3 equipo · 4–5 parte técnica · 6 flujo/demo · 7–8 FODA y testing · 9 aprendizajes · 10 cierre. Si hay demo en vivo, encajala después de la slide 6.
- **Fotos del equipo:** poné las imágenes en `docs/team/` con los nombres indicados; si falta alguna, caen las iniciales automáticamente.
- **Navegación:** flechas ↓/→ o barra espaciadora pasan de slide; los puntitos de la derecha saltan directo.
