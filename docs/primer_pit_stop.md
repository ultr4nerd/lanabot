# Primer Pit Stop

## LanaBot – tu asistente de caja en WhatsApp

### Problemática (el relato que nos inspira)

Imagina a Doña Carmen, dueña de una tiendita de barrio. Cada noche, tras 14 horas de trabajo, abre su libreta: ventas fiadas, tickets sueltos, cuentas a medias… y descubre, ya muy tarde, que no tendrá efectivo para surtir mercancía al amanecer.

Aunque Doña Carmen es solo un personaje ficticio, refleja la realidad de 1.2 millones de tenderos en México que aún manejan su caja “de memoria”. El 50 % de las MIPYMES no adoptó herramientas digitales tras la pandemia (INEGI 2024).

> **¿El resultado?** Estrés, errores de caja y compras urgentes con sobreprecio.

---

### Objetivo general

Que cualquier tendero pueda registrar ventas y gastos con un simple audio o foto en WhatsApp y, en segundos, recibir:

- Saldo en caja.
- Días que le rendirá el efectivo.
- Consejos cortos para mejorar sus finanzas.

---

### Idea general sobre la solución

1. El tendero envía un audio:  
   _“Vendí 120 pesos en refrescos”._

2. LanaBot lo convierte en texto, suma la venta y responde:  
   _"✅ Venta guardada. Caja: $3 540."_

3. Si envía la foto de un ticket, LanaBot detecta el total y lo descuenta.  
4. Cuando el saldo baja de su límite, el bot envía una alerta preventiva.  
5. Cada semana recibe un mini-reporte con puntos clave y un tip, por ejemplo:  
   _“Tus viernes superan 15 % tus otros días, considera extender horario”._

---

## Estudio de viabilidad y fases de implementación

### ¿Por qué sí lo podemos hacer?

- **Técnica**: WhatsApp ya permite chatbots. Existen servicios para convertir audios en texto y leer montos en fotos. Solo sumamos ventas y gastos en la nube; no hace falta instalar servidores ni comprar licencias caras.
- **Económica**: Para el demo gastamos prácticamente $0. Un piloto con 100 tiendas cuesta unos 20 USD/mes y cada tienda extra vale centavos, así que escalar sigue siendo barato.
- **Mercado**: Los tenderos usan WhatsApp a diario y evitan apps complejas. LanaBot responde en el mismo chat que ya conocen y ninguna app de punto de venta actual les habla con audios ni entrega reportes instantáneos en su propio chat.

---

### Fases de implementación (metas claras)

- **MVP – Hackathon (48 h)**: registrar 2 ventas y 1 gasto por audio, responder “¿Cuánto tengo?” y lanzar una alerta, todo en ≤ 5 s con montos correctos.
- **Mes 1 – Pulir experiencia (20 tiendas piloto)**: audio de bienvenida, tres botones (“Venta”, “Gasto”, “Saldo”), foto de ticket y FAQs.  
  Meta: 60 % de las tiendas usan LanaBot 5 días seguidos.
- **Meses 2 y 3 – Primeros ingresos (100 tiendas)**: suscripción de $79 MXN/mes, panel web con historial y reporte PDF.  
  Meta: 20 % de activas pagan.
- **Trimestre 2 – Inteligencia y motivación (500 tiendas)**: búsqueda natural (“¿cuánto gasté en refrescos?”), badges y tips personalizados.  
  Meta: +15 % de uso diario.
- **Trimestre 3 y 4 – Escala y nuevos nichos (1000 tiendas)**: soporte Telegram/Line y personalización por giro manteniendo costo < US $0.10/tienda.

---

### Riesgos clave y cómo los reducimos

- **Baja adopción**: Onboarding con botones + video de 30 s.
- **Límites de WhatsApp**: Plan B: Telegram/SMS si hiciera falta.
- **Ingresos inciertos**: Modelo freemium + alianzas con fintechs que financien el servicio para sus clientes.

---

### ¿Cómo funciona sin entrar en tecnicismos?

1. **Escucha**: LanaBot recibe tu audio o foto en WhatsApp.  
2. **Entiende**: Servicios existentes traducen la voz o leen el ticket.  
3. **Actualiza**: Suma o resta el monto en la nube.  
4. **Responde**: Devuelve el saldo y, si el tendero lo desea, una estimación aproximada de su flujo de efectivo, más un tip cuando aplique.  
5. **Aprende**: Cada semana genera un resumen de lo que pasó y te da una sugerencia.

---

## Herramientas clave bajo el cofre

- **Twilio WhatsApp API**: canal principal para recibir audios, fotos y enviar respuestas; sandbox gratuito ideal para desarrollo rápido sin verificaciones complejas.
- **FastAPI con Python**: orquestador principal que maneja la secuencia audio → texto → clasificación → respuesta.
- **Whisper + GPT-4o Vision**: Whisper transcribe audio; GPT-4o Vision lee tickets y entiende contexto.
- **GPT-4o (LLM)**: procesa texto transcrito, extrae montos y tipos de transacción, genera tips financieros y redacta respuestas en lenguaje mexicano coloquial.
- **Postgres en Supabase**: base de datos en tiempo real, plan gratuito suficiente para piloto.
- **Railway**: hosting con deploy automático desde Git, variables de entorno, logs y webhooks sin configuración compleja.

---

### Por qué estas herramientas

Todas ofrecen planes gratuitos y se despliegan sin administrar servidores.  
Para el MVP del hackathon, priorizamos rapidez de implementación:

- **Twilio** simplifica la integración con WhatsApp con sandbox inmediato.
- **Railway** elimina túneles locales con webhooks públicos automáticos.
- **GPT-4o** centraliza el procesamiento inteligente.

> En fase 2 se introducirán **LangGraph** para flujos más sofisticados y **Supabase Edge Functions** para análisis pesados.

---

## Referencias

- INEGI (2024). Estadísticas Día de las MIPYMES.  
- Statista (2023). Uso de WhatsApp en México.
