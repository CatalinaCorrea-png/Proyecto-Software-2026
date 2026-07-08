# 🎤 Speech — Presentación Final AeroSearch AI (versión unificada + FODA)

> Guion para presentar `presentacion_unificada_aerosearch.html` (11 slides).
> Tono natural, rioplatense. Duración aproximada: **9–11 minutos**.

---

## SLIDE 01 — Portada _(quien abre)_

> "Buenas tardes a todos. Somos el Grupo 1 y venimos a presentarles **AeroSearch AI**, el proyecto en el que trabajamos durante todo el cuatrimestre.
>
> AeroSearch es un sistema de **búsqueda y rescate con drones**, que combina visión artificial y telemetría en tiempo real. En una sola plataforma integramos tres mundos que normalmente van por separado: el backend en Python, el frontend en React, y el hardware con un ESP32. Y arriba de todo eso, un modelo de IA propio para detectar personas.
>
> Déjenme empezar por el porqué."

_(bajar a slide 2)_

---

## SLIDE 02 — El problema

> "El problema que quisimos atacar es uno bien concreto: **buscar personas en zonas extensas lleva demasiado tiempo**. Y en rescate, el tiempo es literalmente la diferencia entre encontrar a alguien o no.
>
> Estos tres números lo resumen: hay una **ventana crítica de 72 horas** después de la cual las probabilidades de supervivencia caen muchísimo. En operaciones reales, hasta un **80% del área queda sin cubrir** en las primeras horas. Y el ratio de rescatistas es de apenas **uno cada 50 km²**.
>
> Hoy eso se resuelve con equipos a pie, celda por celda, sin visión nocturna ni térmica, con fatiga acumulada. Y las aeronaves tripuladas son caras y no siempre están disponibles.
>
> Nuestra propuesta es un **drone autónomo** que recorre una grilla de búsqueda de forma sistemática, detecta personas con inteligencia artificial y manda **alertas geolocalizadas en tiempo real** a un centro de comando web. Que el operador no tenga que mirar el video: que el sistema le avise."

_(bajar a slide 3)_

---

## SLIDE 03 — El equipo, roadmap y velocity

> "Detrás de todo esto estamos **nosotros seis**: Catalina, Nicolás, Dana, Maximiliano, Fernanda y Martín.
>
> Y algo que para nosotros fue una **fortaleza real** como equipo: todos somos desarrolladores fullstack. Nos dividimos en frentes — uno de front, otro de back y otro de hardware —, pero no nos quedamos encasillados en eso. Cuando alguien se trababa, cualquiera podía saltar a darle una mano, y así evitábamos que el bloqueo de una sola persona frenara el avance de todo el equipo.
>
> Trabajamos con **Scrum a lo largo de 6 sprints**. Para estimar el esfuerzo de cada tarea usamos **story points con la escala de Fibonacci** — 1, 2, 3, 5, 8, 13 —, porque nos pareció una forma mucho más fiel que una escala lineal de reflejar lo que nos podía costar cada tarea y cada sprint: a mayor tamaño, mayor incertidumbre, y los saltos de Fibonacci capturan justamente eso.
>
> Con esos puntos medimos el **velocity de cada sprint**: cuánto nos comprometíamos versus cuánto realmente completábamos. Y esa comparación nos mostró, sprint a sprint, los momentos en los que el cumplimiento bajaba — que casi siempre coincidían con los sprints en los que nos habíamos **sobre-comprometido**.
>
> Y esa es la lección que nos llevamos de esta práctica: aprender a leer esas señales para **planificar los siguientes sprints con tareas y metas realistas**, comprometiéndonos con lo que de verdad podíamos cumplir.
>
> Y acá tenemos que ser honestos con un impedimento que nos tocó sobre el final: **se nos quemó el dron**, y por tiempo y presupuesto no llegamos a rearmarlo. Pero queremos dejar algo bien claro: **el sistema no depende de ese dron en particular**. La app se comunica con el hardware a través de una capa desacoplada — telemetría y comandos por UDP —, así que puede funcionar con cualquier dron que hable ese lenguaje: una controladora tipo **Pixhawk con ArduPilot o PX4** por MAVLink, un **DJI con su SDK**, o una companion computer como una **Raspberry Pi con cámara**. Y la detección ya corre sobre cualquier fuente de video —webcam, un archivo, YouTube o el ESP32—, o sea que el motor de IA es totalmente independiente del dron físico. Se quemó _un_ dron, no el sistema."

_(bajar a slide 4)_

> 💡 _Nota: las iniciales de cada integrante se reemplazan por la foto si está en `docs/team/` (`catalina.jpg`, `nicolas.jpg`, `dana.jpg`, `maximiliano.jpg`, `fernanda.jpg`, `martin.jpg`)._

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

_(bajar a slide 5)_

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

_(bajar a slide 6)_

---

## SLIDE 06 — Flujo de una misión _(con escenario real)_

> "Para que se entienda cómo se usa, sigamos una misión de principio a fin — y en cada paso, fíjense en la etiqueta verde de qué cambiaría **en un escenario real**:
>
> **Uno — Configurar.** El operador define nombre, coordenadas GPS, altitud y grilla. _En real_, el coordinador delimita la zona de búsqueda en segundos, sin planear rutas a mano.
>
> **Dos — Vuelo y barrido.** El drone recorre la grilla en serpentina y el mapa pinta las celdas exploradas. _En real_, cubre en minutos terreno que a pie llevaría horas — incluso de noche o en zona inaccesible.
>
> **Tres — Detección en tiempo real.** Cada frame pasa en paralelo por YOLO y por el térmico; si la confianza es media o alta, salta la alerta geolocalizada. _En real_, el rescatista no tiene que mirar el video: el sistema le dice dónde mirar, y eso **reduce el error humano por fatiga**.
>
> **Cuatro — Reporte.** Queda todo guardado: cobertura, batería, detecciones. _En real_, deja trazabilidad de qué se cubrió y dónde, útil para coordinar relevos y auditar la operación.
>
> Y la foto completa: AeroSearch convierte una búsqueda **lenta, peligrosa y dependiente de gente** en una **sistemática, geolocalizada y trazable** — ampliando el área cubierta por hora y liberando a los equipos humanos para que actúen solo donde hay una detección concreta, ganando minutos dentro de esa ventana crítica de 72 horas."

_(bajar a slide 7)_

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

_(bajar a slide 8)_

---

## SLIDE 08 — Del diagnóstico a la acción + Testing

> "Pero lo importante es que **el FODA no quedó en un dibujo bonito**: lo usamos como backlog. Nos dio prioridades, y atacamos primero las debilidades internas, las que sí controlábamos.
>
> La **prioridad número uno fue el testing**. Pasamos de prácticamente no tener tests a una **suite con pytest de 6 módulos**: fusión, grilla, modelos, estado, el detector térmico y — clave — las **rutas críticas de misiones**. Y algo importante: pudimos testear porque antes **modularizamos**. Un `main.py` de 900 líneas es intesteable; separado en piezas, cada una se prueba aislada. Los tests end-to-end quedan para el Sprint 6, y cierran el ciclo.
>
> En paralelo atacamos el resto: el `main.py` pasó de **904 a 56 líneas**, sacamos las credenciales del código con un `.env.example`, y dejamos el manejo de las dos bases explícito y ordenado. Lo que queda — Git LFS para los modelos, autenticación y CI/CD completo — lo dejamos **anotado a propósito** como deuda consciente, no olvidada.
>
> Y esa es la conclusión del FODA: convirtió **percepciones difusas en un backlog priorizado**. No solo describió el proyecto — **cambió cómo trabajamos**."

_(bajar a slide 9)_

---

## SLIDE 09 — Posible monetización _(visión a futuro)_

> "Y si miramos un poco más allá del aula: este proyecto **no tiene por qué terminar acá**. Pensamos, de forma general, a quién podría servirle y hacia dónde podría crecer.
>
> En cuanto a **posibles clientes**, el caso más directo son los **bomberos y la Defensa Civil**, organismos públicos como protección civil o parques nacionales, ONGs de rescate de montaña, e incluso seguridad privada para vigilar predios grandes — minería, energía, campos.
>
> Pero lo más interesante es que **el mismo motor de visión y telemetría sirve para mucho más que rescate**. Ahí aparece la **expansión**: en el **agro**, para conteo de ganado y monitoreo de cultivos; en **eventos masivos**, para contar y detectar personas en aglomeraciones; en **seguros**, para inspección aérea tras una catástrofe; o en **seguridad perimetral**.
>
> O sea, hay un **mercado dual**: uno de alto impacto social, el rescate, y otro comercial — agro, eventos, seguridad — que perfectamente podría financiar el desarrollo del primero. Y como vías posibles imaginamos una **licencia o suscripción** de la plataforma, vender el **kit de hardware más software**, o licenciar la **detección como una API** para que otros la integren.
>
> No es un plan cerrado, pero deja claro que lo que construimos tiene \*_recorrido más allá de la nota."_

_(bajar a slide 10)_

---

## SLIDE 10 — Aprendizajes y conclusiones _(foco ágil)_

> "¿Qué nos llevamos de todo esto? La verdad, más que el código en sí, nos llevamos una forma distinta de trabajar.
>
> Lo de Scrum dejó de ser parte solo teoria y junto con el cuatrimestre anterior que tambien lo hicimos paso a ser la realidad. Hacer planning, review y retro sprint a sprint, eso cambia cómo encarás el proyecto — no es lo mismo verlo en una diapositiva que vivirlo seis veces seguidas.
>
> También aprendimos a priorizar, que hace y qué **no** hacer: elegir qué atacar primero y dejar el resto anotado, muchas veces hubieron tareas que se tuvieron que pasar a el siguiente sprint (eso creo que es por falta de practica y quiza subestimar el tiempo que va a tardar en completarce una tarea).
>
> Algo que nos dimos cuanta tambien es que estimar con story points sirve para, ademas de poder tener una coherencia en la cantidad de tareas que uno hace por sprint, te permite **cuantificar quién está aportando y quién no**. En nuestro caso no hizo falta usarlo para eso por que nuestro equipo funcionó parejo, pero quedó claro que con esos números son algo que te sirve para que no quede en la nada la tarea de uno y te deja identificar cuanto trabajo esta haciendo cada integrante.
>
> Y después está lo del **hardware** que me parece que hay que mencionarlo. De los seis, dos ya teniamos algo de experiencia con el ESP32 y hardware en general, pero igual hizo falta aprender bastante — el hardware no perdona, un cable mal puesto o una alimentación inestable, alguna cosa mal soldada te tira abajo una tarde entera de pruebas que de hecho nos paso mas de una vez. (se retraso muchoas veces por esto)
>
> Si hay una conclusión de fondo es esta: un proyecto grande hacerlo sin un plan no es posible, es algo que se sostiene por proceso constante de esfuerzo medido con roles claros. El backlog priorizado nos dio dirección, los story points nos dieron honestidad, y el hardware/software nos bajó a tierra ya que fue un proyecto complicado."

_(bajar a slide 11)_

---

## SLIDE 11 — Cierre

> "Para cerrar: basicamente nuestro proyecto AeroSearch arrancó como una idea quiza un poco mas simple (que en realidad era complicado) y terminó siendo un producto mas complejo que funciona de verdad para mas cosas que lo que se penso en un inicio, ademas implementa de todo hardware, firmware, IA, back, front, ademas de bases de datos, osea es algo muy completo.
>
> Y nada, la verdad estamos contentos con lo que armamos, y nos gusta que pudimos hacer funcionar un proyecto que la verdad que nos gusta posta.
>
> Muchas gracias, quedamos para las preguntas."

---

## Notas para la exposición

- **Ritmo:** las slides 3 (velocity), 4 y 5 son las más densas; las 7 y 8 (FODA) son el corazón de la parte de proceso. Si vas corto de tiempo, en la 3 quedate con la idea del velocity y el 78% de cumplimiento, en la 5 nombrá 3 features, y en la 7 leé solo un par de puntos por cuadrante (el resto está en pantalla).
- **Slide 3 (velocity):** el gráfico muestra cada barra como _comprometido_ (track) con la parte llena = _completado_. Es buen momento para conectar con la historia ágil: sobre-compromiso en S3 y S5 → los sprints donde más bajó el cumplimiento. El número clave (opcional) para decir en voz alta es **385 comprometidos / 335 completados = 87%**. Cerrá el bloque con el impedimento del dron quemado y la independencia del hardware (Pixhawk/MAVLink, DJI, Raspberry Pi).
- **Reparto sugerido (6 personas):** 1–2 quien abre · 3 equipo · 4–5 parte técnica · 6 flujo/demo · 7–8 FODA y testing · 9 monetización · 10 aprendizajes · 11 cierre. Si hay demo en vivo, encajala después de la slide 6.
- **Slide 9 (monetización):** es liviana y a futuro — no te enredes en números ni precios. El concepto fuerte para dejar picando es el **mercado dual**: rescate (impacto social) + agro/eventos/seguridad (comercial).
- **Fotos del equipo:** poné las imágenes en `docs/team/` con los nombres indicados; si falta alguna, caen las iniciales automáticamente.
- **Navegación:** flechas ↓/→ o barra espaciadora pasan de slide; los puntitos de la derecha saltan directo.
