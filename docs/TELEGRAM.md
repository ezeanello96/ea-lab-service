# Configuración del bot de Telegram

El bot de Telegram es opcional y se activa mediante el perfil `telegram` de Docker Compose.

---

## Requisitos previos

1. Crear un bot en Telegram hablando con [@BotFather](https://t.me/BotFather)
2. Copiar el token generado
3. Obtener tu ID de Telegram (podés usar [@userinfobot](https://t.me/userinfobot))

---

## Configuración en .env

```dotenv
TELEGRAM_ENABLED=1
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi
TELEGRAM_ADMIN_USER_IDS=123456789,987654321
```

- `TELEGRAM_ENABLED`: Poner en `1` para activar el bot
- `TELEGRAM_BOT_TOKEN`: El token que te dio BotFather
- `TELEGRAM_ADMIN_USER_IDS`: IDs de Telegram separados por coma de los usuarios administradores del bot

---

## Iniciar el bot

```bash
# Iniciar todos los servicios incluyendo el bot
docker compose --profile telegram up -d

# O solo el bot (si el resto ya está corriendo)
docker compose --profile telegram up -d bot

# Ver logs del bot
make logs-bot
```

---

## Vincular una cuenta de Telegram a un usuario del sistema

1. Iniciar sesión en el sistema web como el usuario a vincular
2. Ir a Configuración → Perfil → "Vincular Telegram"
3. El sistema genera un código temporal (válido 30 minutos)
4. Abrir el bot en Telegram y enviar el comando: `/vincular TU_CODIGO`
5. El bot confirmará la vinculación

---

## Comandos disponibles del bot (Fase 0 — esqueleto)

Los comandos del bot se implementarán en fases posteriores.
Por ahora el servicio solo arranca y queda a la espera.

---

## Silencio nocturno

El bot respeta el horario de silencio configurado en Configuración del negocio.
Las notificaciones generadas fuera del horario activo se marcan como "omitidas"
y no se envían por Telegram.

---

## Troubleshooting

**El bot no responde**: Verificar que `TELEGRAM_BOT_TOKEN` es correcto y que el contenedor `bot` está corriendo (`make status`).

**Error de conexión**: El contenedor necesita acceso a `api.telegram.org:443`. Verificar firewall/proxy si el servidor está en una red corporativa.

**Errores de permisos**: Verificar que tu `TELEGRAM_ADMIN_USER_IDS` coincide exactamente con tu ID de Telegram.
