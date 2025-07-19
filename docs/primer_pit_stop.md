# Primer Pit Stop

## LanaBot – tu asistente de caja en WhatsApp

### Problemática (el relato que nos inspira)

Imagina a Doña Carmen, dueña de una tiendita de barrio. Cada noche, tras 14 horas de trabajo, abre su libreta: ventas fiadas, tickets sueltos, cuentas a medias… y descubre, ya muy tarde, que no tendrá efectivo para surtir mercancía al amanecer.

Aunque Doña Carmen es solo un personaje ficticio, refleja la realidad de 1.2 millones de tenderos en México que aún manejan su caja "de memoria". El 50 % de las MIPYMES no adoptó herramientas digitales tras la pandemia (INEGI 2024).

> **¿El resultado?** Estrés, errores de caja y compras urgentes con sobreprecio.

---

### Objetivo general

Que cualquier tendero pueda registrar ventas y gastos con un simple audio o foto en WhatsApp y, en segundos, recibir:

- Saldo en caja.
- Días que le rendirá el efectivo.
- Consejos cortos para mejorar sus finanzas.

---

### Idea general sobre la solución

1. **Onboarding inteligente**: El tendero envía "hola" y recibe tutorial completo con ejemplos prácticos.

2. **Registro de transacciones**: Envía audio/texto como:  
   _"Vendí 120 pesos en refrescos"_ → LanaBot responde: _"✅ VENTA $120 registrada. Saldo: $3,540. 📅 Te rinde ~8.2 días. 💡 Tip: ¡Excelente ritmo de ventas!"_

3. **Ajustes de caja**: _"Empiezo el día con 500 pesos"_ → Registra saldo inicial automáticamente.

4. **Procesamiento de tickets**: Foto de ticket → Detección automática de monto y tipo con confirmación inteligente.

5. **Búsqueda natural**: _"¿Cuánto gasté en refrescos?"_ → Historial detallado con totales y fechas.

6. **Alertas preventivas**: Cuando el saldo baja, alerta con contexto: _"Te quedan $150, con tus gastos te rinde 1.2 días más"_.

7. **Tips financieros automáticos**: Consejos contextuales según el estado financiero actual.

---

## Estudio de viabilidad y fases de implementación

### ¿Por qué sí lo podemos hacer?

- **Técnica**: WhatsApp ya permite chatbots. Existen servicios para convertir audios en texto y leer montos en fotos. Solo sumamos ventas y gastos en la nube; no hace falta instalar servidores ni comprar licencias caras.
- **Económica**: Para el demo gastamos prácticamente $0. Un piloto con 100 tiendas cuesta unos 20 USD/mes y cada tienda extra vale centavos, así que escalar sigue siendo barato.
- **Mercado**: Los tenderos usan WhatsApp a diario y evitan apps complejas. LanaBot responde en el mismo chat que ya conocen y ninguna app de punto de venta actual les habla con audios ni entrega reportes instantáneos en su propio chat.

---

### Fases de implementación (metas claras)

- **✅ MVP – Hackathon (48 h) - COMPLETADO**: registrar ventas y gastos por audio/texto, consultar saldo, alertas de saldo bajo, procesamiento de tickets por foto, ajustes de caja manual, todo en ≤ 5 s con montos correctos.
- **✅ SUPERADO: Funcionalidades avanzadas implementadas**:
  - **Sistema de bienvenida inteligente**: detección automática de saludos y ayuda con tutorial completo
  - **Búsqueda natural**: "¿cuánto gasté en refrescos?", "mis ventas de dulces"
  - **Tips financieros contextuales**: consejos automáticos según el estado financiero
  - **Estimación de flujo de efectivo**: "tu efectivo te rinde ~3.2 días"
  - **Corrección de transacciones**: sistema de confirmación y corrección inteligente
- **Mes 1 – Pulir experiencia (20 tiendas piloto)**: optimización de respuestas, análisis de patrones de uso y mejoras de UX.  
  Meta: 60 % de las tiendas usan LanaBot 5 días seguidos.
- **Meses 2 y 3 – Primeros ingresos (100 tiendas)**: suscripción de $79 MXN/mes, panel web con historial y reporte PDF.  
  Meta: 20 % de activas pagan.
- **Trimestre 2 – Escalabilidad (500 tiendas)**: análisis predictivos, badges gamificados y reportes semanales automáticos.  
  Meta: +15 % de uso diario.
- **Trimestre 3 y 4 – Escala y nuevos nichos (1000 tiendas)**: soporte Telegram/Line y personalización por giro manteniendo costo < US $0.10/tienda.

---

### Riesgos clave y cómo los reducimos

- **Baja adopción**: Onboarding con tutorial automático + ejemplos claros desde el primer "hola".
- **Límites de WhatsApp**: Plan B: Telegram/SMS si hiciera falta.
- **Ingresos inciertos**: Modelo freemium + alianzas con fintechs que financien el servicio para sus clientes.

---

### ¿Cómo funciona sin entrar en tecnicismos?

1. **Escucha**: LanaBot recibe tu audio, texto o foto en WhatsApp.  
2. **Entiende**: Whisper transcribe audio en español mexicano; GPT-4o Vision lee tickets; GPT-4o procesa texto y extrae información financiera.  
3. **Clasifica**: Distingue automáticamente entre ventas, gastos, ajustes de caja, consultas de saldo y búsquedas.  
4. **Actualiza**: Suma o resta el monto en la nube con cálculos de flujo de efectivo en tiempo real.  
5. **Responde**: Devuelve saldo actualizado, estimación de días que rinde el efectivo, y tip financiero contextual.  
6. **Busca**: Permite consultas naturales como "¿cuánto gasté en dulces?" con historial detallado.  
7. **Aprende**: Analiza patrones de gasto para generar consejos personalizados automáticamente.

---

## Herramientas clave bajo el cofre

- **WhatsApp Business Cloud API**: canal principal para recibir audios, fotos y enviar respuestas; integración directa con Meta para máxima confiabilidad y escalabilidad.
- **FastAPI con Python 3.12+**: orquestador principal que maneja la secuencia audio → texto → clasificación → respuesta con async/await para máximo rendimiento.
- **Whisper + GPT-4o Vision**: Whisper transcribe audio en español mexicano; GPT-4o Vision lee tickets y entiende contexto visual.
- **GPT-4o (LLM)**: procesa texto transcrito, extrae montos y tipos de transacción, genera tips financieros contextuales y redacta respuestas en lenguaje mexicano coloquial.
- **Postgres en Supabase**: base de datos en tiempo real con búsquedas optimizadas, plan gratuito suficiente para piloto y escalabilidad automática.
- **Railway**: hosting con deploy automático desde Git, variables de entorno, logs y webhooks sin configuración compleja.

---

### Por qué estas herramientas

Todas ofrecen planes gratuitos y se despliegan sin administrar servidores.  
Para el MVP del hackathon, priorizamos rapidez de implementación y confiabilidad:

- **WhatsApp Business API** ofrece integración oficial de Meta con mejor deliverabilidad que Twilio.
- **Railway** elimina túneles locales con webhooks públicos automáticos.
- **GPT-4o** centraliza el procesamiento inteligente con capacidades multimodales.
- **Python 3.12+** con type hints y async/await para código mantenible y performante.

> En fase 2 se introducirán **LangGraph** para flujos conversacionales más sofisticados y **Supabase Edge Functions** para análisis pesados.

---

## Maquetas, primeras simulaciones y/o wireframes que construyan el prototipo final

### Landing Page Oficial
**🌐 Demo en vivo**: [https://lanabot.netlify.app/](https://lanabot.netlify.app/)

Nuestra landing page presenta:
- **Hero section** con propuesta de valor clara para tenderos mexicanos
- **Demostración interactiva** del flujo de conversación
- **Casos de uso reales** con ejemplos de transacciones
- **Testimonios simulados** de Doña Carmen y otros tenderos
- **Pricing transparente** con modelo freemium
- **Call-to-action** directo para comenzar a usar LanaBot

### Video Demostración del Chat
**🎥 Presentación completa del funcionamiento**:

*[Espacio reservado para video de demostración en vivo del chat de WhatsApp mostrando:]*
- *Flujo completo de onboarding con "hola"*
- *Registro de ventas por audio: "Vendí 3 refrescos a 15 pesos"*
- *Procesamiento de ticket por foto*
- *Búsqueda natural: "¿cuánto gasté en dulces?"*
- *Consulta de saldo con estimación de días*
- *Tips financieros contextuales automáticos*
- *Corrección de transacciones en tiempo real*

### Arquitectura del Flujo de Conversación

```
👤 Usuario: "Hola" / "Ayuda"
🤖 LanaBot: Tutorial completo con ejemplos

👤 Usuario: 🎤 "Vendí 3 coca colas a 15 pesos"
🤖 LanaBot: ✅ VENTA $45 registrada
          💰 Saldo: $845
          📅 Te rinde ~8.2 días
          💡 Tip: ¡Excelente! Mantén este ritmo

👤 Usuario: 📸 [Foto de ticket del OXXO]
🤖 LanaBot: 📊 Detecté GASTO $127 (mercancía)
          ¿Es correcto? Responde GASTO o VENTA

👤 Usuario: "¿Cuánto gasté en refrescos?"
🤖 LanaBot: 🔍 Búsqueda: gastos de 'refrescos'
          💰 Total: $450 (12 transacciones)
          📋 Últimas: 19/07: $127, 18/07: $89...
```

---

## Referencias

- INEGI (2024). Estadísticas Día de las MIPYMES.  
- Statista (2023). Uso de WhatsApp en México.