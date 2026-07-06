# 🎤 Guion de presentación — AeroSearch AI

**Sistema de búsqueda y rescate asistido por drones · UNSAM 2026**
Pitch de ~11–12 min · 6 integrantes · acompaña al deck de 13 slides.

---

## Cómo usar este guion

- El que habla maneja las flechas **← →** de su tramo y, al terminar, dice la frase de relevo mientras el siguiente se acerca.
- El deck muestra abajo a la izquierda **"▸ Habla: [nombre]"** en cada slide, para que nadie se pierda.
- Los textos entre `[corchetes]` son acotaciones o datos a completar, **no se leen en voz alta**.

---

## 👤 Catalina — Apertura + Problema · Slides 1–2 · ~1:50

**[Slide 1 — Portada]**

> Buenas. Somos el equipo de **AeroSearch AI**. Imaginen una persona perdida en un cerro, de noche, con la temperatura bajando. Un equipo de rescate sale a buscarla a pie… y el reloj corre. Eso es lo que quisimos atacar: **encontrar personas antes de que el tiempo se agote.**
>
> Les vamos a mostrar un sistema de búsqueda y rescate asistido por drones, que hoy ya es un prototipo funcional. Somos seis y cada uno les va a contar una parte.

**[avanzar a Slide 2 — El problema]**

> Empecemos por el problema, porque define todo lo demás. En un rescate, **cada minuto cuenta**: la probabilidad de supervivencia cae fuerte con las horas. Y la búsqueda manual tiene tres debilidades grandes.
>
> Primero, es **lenta y peligrosa**: un equipo a pie cubre poco terreno y se expone. Segundo, usa **un solo sentido** — la vista — que falla cuando hay vegetación, oclusión o poca luz. Y tercero, **no es sistemática**: es difícil saber qué zona ya se cubrió, y no queda registro de qué se buscó y dónde.
>
> Ese es el vacío. Y ahí es donde entra nuestra propuesta, que les va a contar Nicolás.

*→ Relevo: "Te dejo con la solución, Nicolás."*

---

## 👤 Nicolás — Propuesta + Qué hace · Slides 3–4 · ~2:00

**[Slide 3 — Propuesta de valor]**

> Gracias. Nuestra propuesta en una frase: **reducimos el tiempo hasta encontrar a una persona**, fusionando visión RGB y térmica sobre un barrido sistemático del terreno, con conciencia situacional en vivo para el operador.
>
> Tres promesas concretas. **Más rápido**: el dron cubre en minutos lo que a un equipo le lleva horas. **Más confiable**: dos sensores se complementan donde uno solo falla. Y **más ordenado**: una grilla de cobertura y un registro auditable de cada hallazgo.

**[avanzar a Slide 4 — Qué hace]**

> ¿Cómo se traduce eso en el producto? No les voy a leer veinte features; son **cuatro capacidades** que nos diferencian.
>
> **Fusión RGB + térmica**: robusto a oclusión, vegetación y baja luz. **Barrido en grilla**: búsqueda sistemática, con el porcentaje de terreno cubierto actualizándose en vivo — nada queda al azar. **Conciencia situacional en tiempo real**: telemetría, cámara, mapa y alertas de detección, todo al instante. Y **trazabilidad total**: cada detección queda georreferenciada y guardada, en una galería y un historial auditable.
>
> Y lo mejor es que no se los tengo que contar… se los podemos mostrar. Dana los lleva a la demo.

*→ Relevo: "Adelante con la demo, Dana."*

---

## 👤 Dana — Demo en vivo · Slide 5 · ~2:15

**[Slide 5 — Demo]**

> Esto es lo que hace el sistema, de principio a fin. Son cuatro pasos, y los vamos a ver en la aplicación real.
>
> **Paso uno, configurar**: defino la zona, la altitud y la grilla de búsqueda desde el panel de misión. *[cambiar a la app]*
>
> **Paso dos, barrer**: inicio la misión y el dron empieza a recorrer la grilla. Miren el mapa: se va **pintando la cobertura** en tiempo real, así en todo momento sé qué ya revisé.
>
> **Paso tres, detectar**: cuando la fusión de sensores reconoce a una persona, dispara una **alerta** y captura la imagen, ya georreferenciada. *[señalar la alerta y la cámara]*
>
> **Paso cuatro, registrar**: ese hallazgo aparece en la **galería** y queda asociado a la misión en el historial, con su ubicación, hora y nivel de confianza.
>
> *[Si algo falla en vivo]* — y como buen equipo de software, tenemos el video de respaldo listo, porque una demo sin plan B no es una demo.
>
> Eso es el flujo completo. Lo que vieron corriendo por detrás tiene una arquitectura pensada para que esto funcione en tiempo real y para varios espectadores a la vez. Maximiliano se los explica.

*→ Relevo: "¿Cómo está construido? Te toca, Maximiliano."*

---

## 👤 Maximiliano — Arquitectura + Evidencia · Slides 6–7 · ~2:10

**[Slide 6 — Arquitectura]**

> Gracias. Rápido, porque el objetivo acá es que confíen en que esto es sólido, no marearlos.
>
> El recorrido es: el **dron** captura imagen y telemetría. Eso llega a un **backend en FastAPI**, que corre el pipeline — detección visual, detección térmica, **fusión**, y persistencia. Los datos van a **dos bases**: MongoDB para las imágenes georreferenciadas, y SQL para misiones, usuarios y detecciones. Y el **frontend en React** recibe todo por WebSocket y lo muestra en vivo.
>
> Una decisión de diseño de la que estamos orgullosos: el pipeline pesado corre **una sola vez por misión** y se transmite a todos los que estén mirando. Así el sistema **escala en espectadores** sin recalcular nada.

**[avanzar a Slide 7 — Evidencia]**

> Y acá viene lo que nos parece nuestro diferencial más fuerte. Un pitch cualquiera dice 'somos eficientes'. Nosotros **lo medimos**: el sistema se autoinstrumenta.
>
> Medimos el **tiempo hasta la primera detección**, la **eficiencia de barrido** en metros cuadrados por minuto, la **densidad de detecciones** por kilómetro cuadrado, y el **consumo de batería** por área cubierta. Incluso cruzamos altitud contra confianza, para saber a qué altura conviene volar.
>
> *[Insertar una conclusión real de tus datos, ej.:]* Y de nuestros propios vuelos ya sacamos que… [dato]. No lo afirmamos: lo instrumentamos.

*→ Relevo: "Ahora, ¿quién usa esto? Fernanda."*

---

## 👤 Fernanda — Roles + Validación · Slides 8–9 · ~2:00

**[Slide 8 — Usuarios y roles]**

> Un rescate no es una sola persona frente a una pantalla; es una **operación con varios actores**. Por eso el sistema tiene control de acceso por roles.
>
> El **operador** controla la misión: configura, inicia, finaliza y administra el historial. El **espectador** solo observa — pensemos en coordinación de emergencia, prensa, o familiares que quieren seguir la búsqueda en vivo, sin poder tocar nada. Y el modelo de permisos es **jerárquico**: el operador también es espectador, los permisos se acumulan. Es **seguro por diseño**.
>
> Esto no es un adorno: en un contexto donde la información es sensible, definir **quién puede qué** es parte del producto.

**[avanzar a Slide 9 — Validación]**

> Y para cerrar la parte técnica: esto **no es una demo de humo**. Está probado.
>
> Tenemos una **suite de tests en verde** — unitarios y de punta a punta — que cubre los flujos críticos: autenticación, roles y ciclo de vida de la misión. Los tests E2E ejercitan la **aplicación real**, con el hardware y la red neutralizados, así validamos el comportamiento de verdad, no una maqueta.
>
> Lo importante: esos tests **bloquean regresiones**. Si alguien rompe la autorización por roles sin querer, un test lo detecta antes de que llegue a producción.

*→ Relevo: "Para cerrar, seamos honestos sobre qué falta. Martín."*

---

## 👤 Martín — Limitaciones + Ética + Roadmap + Cierre · Slides 10–13 · ~2:30

**[Slide 10 — Limitaciones]**

> Gracias. Y acá quiero ser transparente, porque es lo que nos hace serios, no débiles.
>
> Esto es un **prototipo**. La detección térmica hoy está **simulada** — falta integrar una cámara térmica real. Corre en **condiciones controladas**, no está certificado para un rescate real. Y depende de algunos **servicios externos** con límites de uso. Nada de esto lo escondemos: sabemos exactamente qué falta y por qué. Es nuestra hoja de ruta, no un problema oculto.

**[avanzar a Slide 11 — Ética]**

> Y volar sobre personas es una **responsabilidad**. Capturamos imágenes de gente, así que la **privacidad** está protegida por el acceso por roles y el uso acotado al rescate. La operación está sujeta a **regulación** de espacio aéreo, la de ANAC. Y lo pensamos como una herramienta para **asistir a rescatistas** — no para vigilar ni para decidir de forma autónoma.

**[avanzar a Slide 12 — Roadmap]**

> ¿Hacia dónde va? En lo inmediato, **hardware térmico real**. Después, **detección en el borde**, corriendo en el propio dron sin depender de conexión. Una **app responsive** para usar en el campo desde el celular. Y a futuro, **coordinar varios drones** sobre una misma grilla.

**[avanzar a Slide 13 — Cierre]**

> Cerramos donde empezamos. En un rescate, **cada minuto cuenta**. AeroSearch AI convierte esos minutos en cobertura — y esa cobertura, en vidas.
>
> Lo que les mostramos es un prototipo **funcional, medible y probado**. Lo que pedimos es **[continuar el proyecto / su feedback / apoyo para la etapa de hardware]**.
>
> Muchas gracias. Quedamos abiertos a sus preguntas.

---

## ⏱️ Cuadro de tiempos

| # | Integrante | Slides | Tema | Tiempo |
|---|-----------|--------|------|--------|
| 1 | Catalina | 1–2 | Apertura + Problema | ~1:50 |
| 2 | Nicolás | 3–4 | Propuesta + Qué hace | ~2:00 |
| 3 | Dana | 5 | **Demo en vivo** | ~2:15 |
| 4 | Maximiliano | 6–7 | Arquitectura + Métricas | ~2:10 |
| 5 | Fernanda | 8–9 | Roles + Validación | ~2:00 |
| 6 | Martín | 10–13 | Límites + Ética + Roadmap + Cierre | ~2:30 |
| | | | **Total** | **~12:45 con margen de aire** |

> Si van justos de tiempo: recortá el bloque de Roadmap (slide 12) a una sola frase y acortá la intro de la demo. Eso te baja a ~11 limpio.

---

## ✅ Checklist antes de presentar

- [x] Nombres del equipo cargados en el guion y el deck.
- [ ] **Slide 2** — poner la cifra de supervivencia citada de una fuente de SAR real.
- [ ] **Slide 7** — insertar una conclusión real sacada de los datos de vuelo.
- [ ] **Slide 9** — ajustar el conteo de tests al número real.
- [ ] **Slide 13** — elegir el "ask" según la audiencia (jurado → continuar el proyecto; partner → apoyo para hardware).
- [ ] Tener el **video de respaldo** de la demo cargado y listo.
- [ ] Probar el deck en el proyector: flechas ← → para navegar, `Home`/`End` para saltar.

---

*Equipo AeroSearch AI · Proyecto de Software · UNSAM 2026*
