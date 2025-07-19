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
2. **Entiende**: Convierte tu voz a texto, lee números en fotos de tickets y comprende lo que quieres hacer.  
3. **Clasifica**: Sabe si es una venta, un gasto, una pregunta o si solo quieres saludar.  
4. **Actualiza**: Suma o resta el dinero y calcula cuánto te va a durar.  
5. **Responde**: Te dice tu saldo actual, cuántos días te rinde el efectivo y te da un consejo útil.  
6. **Busca**: Si preguntas "¿cuánto gasté en dulces?" te muestra el historial completo.  
7. **Aprende**: Con el tiempo te conoce mejor y te da consejos más personalizados.

---

## Herramientas clave bajo el cofre

- **WhatsApp Business Cloud API**: canal principal para recibir audios, fotos y enviar respuestas; integración directa con Meta para máxima confiabilidad y escalabilidad.
- **FastAPI con Python 3.12+**: orquestador principal que maneja la secuencia audio → texto → clasificación → respuesta con async/await para máximo rendimiento.
- **OpenAI Whisper + GPT-4o Vision**: Whisper transcribe audio en español mexicano; GPT-4o Vision lee tickets y entiende contexto visual; GPT-4o procesa texto y extrae información financiera.
- **PostgreSQL en Supabase**: base de datos en tiempo real con búsquedas optimizadas (ILIKE), índices automáticos y escalabilidad horizontal.
- **Railway**: hosting con deploy automático desde Git, variables de entorno seguras, logs centralizados y webhooks sin configuración compleja.
- **uv (Ultra-fast Python package manager)**: gestión de dependencias 10-100x más rápida que pip, con lock files determinísticos.

---

### Por qué estas herramientas

Todas ofrecen planes gratuitos y se despliegan sin administrar servidores.  
Para el MVP del hackathon, priorizamos rapidez de implementación y confiabilidad:

- **WhatsApp Business Cloud API** ofrece integración oficial de Meta con mejor deliverabilidad y límites más altos que Twilio.
- **Railway** elimina túneles locales (ngrok) con webhooks públicos automáticos y deploy continuo.
- **OpenAI GPT-4o** centraliza el procesamiento inteligente con capacidades multimodales (texto + visión + audio).
- **Python 3.12+** con type hints completos, async/await nativo y Pydantic v2 para validación de datos ultra-rápida.
- **Supabase** ofrece PostgreSQL real-time con APIs auto-generadas y Row Level Security nativo.
- **uv** permite builds reproducibles y setup de desarrollo en segundos vs minutos.

> En fase 2 se introducirán **LangGraph** para flujos conversacionales más sofisticados, **Supabase Edge Functions** para análisis pesados y **LangSmith** para observabilidad de LLM.

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

**Flujo recomendado para video demo (usar número 5215512345678 con datos precargados):**

1. **Onboarding inicial**:
   - Enviar: "hola"
   - Mostrar respuesta completa del tutorial

2. **Registro de transacciones**:
   - Audio: "Vendí 2 coca colas a 15 pesos cada una"
   - Texto: "Compré dulces por 50 pesos"
   - Mostrar respuestas con saldo actualizado y tips automáticos

3. **Procesamiento de tickets**:
   - Subir foto de ticket del OXXO
   - Mostrar detección automática y confirmación

4. **Búsqueda natural (funcionalidad avanzada)**:
   - "¿cuánto gasté en mercancía?" → $800.50 en 2 transacciones
   - "¿cuánto vendí de refrescos?" → $45.00 en 1 transacción
   - "mis gastos de dulces" → $80.00 en 1 transacción

5. **Consulta de saldo**:
   - "saldo" o "¿cuánto tengo?"
   - Mostrar estimación de días restantes y tip contextual

6. **Corrección de transacciones**:
   - Registrar algo mal clasificado
   - Responder "GASTO" o "VENTA" para corregir

7. **Ajustes de caja**:
   - "Saqué 200 pesos para gastos personales"
   - "Agregué 300 pesos de mi bolsa"

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