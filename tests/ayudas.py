"""Utilidades de pruebas: resolver el CAPTCHA con la clave interna del servicio."""
import re
import time

import jwt


def captcha_resuelto(app, texto: str = "ABCDE") -> tuple[str, str]:
    cap = app.extensions["seguridad"].captcha
    nonce = f"n{time.time_ns()}"
    token = jwt.encode({"n": nonce, "h": cap._firma(nonce, texto), "typ": "captcha", "exp": int(time.time()) + 60}, cap._clave, algorithm="HS256")
    return token, texto


def iniciar_sesion(app, cliente, usuario: str, clave: str):
    token, texto = captcha_resuelto(app)
    return cliente.post("/auth/login", data={"usuario": usuario, "password": clave, "captcha_token": token, "captcha": texto})


def csrf(html: bytes) -> str:
    return re.search(rb'name="csrf_token" value="([0-9a-f]+)"', html).group(1).decode()
