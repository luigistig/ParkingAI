# 🔐 Credenciales de Acceso - Sistema de Parqueadero IA

## Acceso de Administrador

**URL**: http://localhost:5000/admin/login

**Usuario por defecto**:
- **Usuario**: `admin`
- **Contraseña**: `admin123`

## Cambiar Credenciales

Para cambiar las credenciales de administrador, edita las variables de entorno:

```bash
# En el archivo .env (en la carpeta del proyecto)
ADMIN_USERNAME=tu_usuario
ADMIN_PASSWORD=tu_contraseña
```

O directamente en las variables de entorno del sistema (Windows):

```powershell
$env:ADMIN_USERNAME="tu_usuario"
$env:ADMIN_PASSWORD="tu_contraseña"
```

## Flujo de Acceso

### Para Usuarios Normales:
1. Ingresan a http://localhost:5000
2. Ven solo el botón "Inicio"
3. Buscan su placa y pagan

### Para Administrador:
1. Ingresan a http://localhost:5000
2. Hacen click en "Admin" (arriba a la derecha)
3. Van a /admin/login
4. Ingresan usuario y contraseña
5. Acceden a: REGISTRO, PAGO, HISTORIAL, ADMINISTRACIÓN

## Características de Sesión

- ✅ Las sesiones persisten por 7 días
- ✅ Opción "Recuérdame" guarda el usuario en localStorage
- ✅ El admin puede cerrar sesión desde el dropdown
- ✅ Cierre de sesión automático al limpiar cookies

## Seguridad

⚠️ **IMPORTANTE**: En PRODUCCIÓN, cambiar:
- Las credenciales por defecto
- La `SECRET_KEY` en app/__init__.py
- Usar base de datos para credenciales
- Habilitar HTTPS (SESSION_COOKIE_SECURE=True)

---

Para más información, revisa el archivo README.md principal.
