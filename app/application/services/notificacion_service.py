import json
from datetime import datetime
from typing import List, Optional, Dict

from app.domain.ports.notificacion_repositorio_port import NotificacionRepositorioPort
from app.domain.ports.fcm_token_repositorio_port import FcmTokenRepositorioPort
from app.domain.ports.notificacion_push_port import NotificacionPushPort
from app.domain.ports.lectura_notificacion_port import LecturaNotificacionPort
from app.domain.entities.models import Notificacion as NotificacionEntity
from app.domain.entities.notificacion_entities import (
    SolicitudNotificacion,
    RespuestaEnvioNotificacion,
    NotificacionPersona,
    NotificacionDestino,
)
from app.application.services.firestore_sync_service import FirestoreSyncService
from app.infrastructure.utils.time_utils import ahora_sin_tz


class NotificacionService:
    """
    Servicio de aplicacion para orquestar el envio de notificaciones.

    Coordina: persistencia (PostgreSQL), push (FCM),
    tokens (Firestore) y estado de lectura (Firestore).
    """

    def __init__(
        self,
        notificacion_repo: NotificacionRepositorioPort,
        fcm_token_repo: FcmTokenRepositorioPort,
        push_service: NotificacionPushPort,
        lectura_service: LecturaNotificacionPort,
    ):
        self.notificacion_repo = notificacion_repo
        self.fcm_token_repo = fcm_token_repo
        self.push_service = push_service
        self.lectura_service = lectura_service
        self.firestore_sync = FirestoreSyncService()

    # ─── ENVIO ─────────────────────────────────────────────

    async def enviar_notificacion(
        self, solicitud: SolicitudNotificacion
    ) -> RespuestaEnvioNotificacion:
        mensaje_json = json.dumps({
            "titulo": solicitud.titulo,
            "cuerpo": solicitud.mensaje,
            "prioridad": solicitud.prioridad,
            "categoria": solicitud.categoria,
            "ruta_accion": solicitud.ruta_accion,
            "datos_accion": solicitud.datos_accion,
        })

        datos_push = {
            "notificacion_id": "",
            "tipo": solicitud.tipo,
            "categoria": solicitud.categoria,
            "prioridad": solicitud.prioridad,
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
        }
        if solicitud.ruta_accion:
            datos_push["ruta_accion"] = solicitud.ruta_accion

        notificacion_entidad = NotificacionEntity(
            tipo=solicitud.tipo or "notificacion_personalizada",
            mensaje=mensaje_json,
            usuario_creado="api_system",
            persona_emisor_id=solicitud.persona_emisor_id,
        )

        db_notificacion = await self.notificacion_repo.guardar_notificacion(
            notificacion_entidad
        )
        notificacion_id = db_notificacion.notificacion_pk

        if solicitud.enviar_a_todos:
            destinatario_ids = await self._obtener_todos_los_residentes()
        else:
            destinatario_ids = solicitud.destinatario_ids or []

        if not destinatario_ids:
            return RespuestaEnvioNotificacion(
                notificacion_id=notificacion_id,
                total_destinatarios=0,
                push_enviados=0,
                push_fallidos=0,
                errores=["No se encontraron destinatarios"],
                mensaje="Notificacion guardada sin destinatarios",
            )

        destinos_entidad = []
        for persona_id in destinatario_ids:
            destino = NotificacionDestino(
                notificacion_envio_id=notificacion_id,
                persona_receptor_id=persona_id,
                usuario_creado="api_system",
                entregada=False,
            )
            destinos_entidad.append(destino)

        await self.notificacion_repo.guardar_destinos(destinos_entidad)

        for persona_id in destinatario_ids:
            try:
                await self.firestore_sync.sincronizar_notificacion_enviada(
                    persona_id=persona_id,
                    notificacion_id=notificacion_id,
                    titulo=solicitud.titulo,
                    cuerpo=solicitud.mensaje,
                    categoria=solicitud.categoria,
                    prioridad=solicitud.prioridad,
                    ruta_accion=solicitud.ruta_accion,
                    datos_accion=solicitud.datos_accion,
                )
            except Exception as e:
                print(f"Error sincronizando Firestore persona {persona_id}: {e}")

        push_result = await self._enviar_push(
            destinatario_ids,
            solicitud.titulo,
            solicitud.mensaje,
            notificacion_id,
            datos_push,
        )

        return RespuestaEnvioNotificacion(
            notificacion_id=notificacion_id,
            total_destinatarios=len(destinatario_ids),
            push_enviados=push_result["exitosos"],
            push_fallidos=push_result["fallidos"],
            errores=push_result["errores"],
            mensaje=(
                f"Notificacion enviada a {len(destinatario_ids)} destinatarios. "
                f"Push: {push_result['exitosos']} ok, {push_result['fallidos']} fallidos"
            ),
        )

    async def enviar_notificacion_individual(
        self,
        persona_id: int,
        titulo: str,
        cuerpo: str,
        tipo: str = "notificacion_personalizada",
        prioridad: str = "normal",
        categoria: str = "general",
        ruta_accion: Optional[str] = None,
        datos_accion: Optional[dict] = None,
    ) -> RespuestaEnvioNotificacion:
        solicitud = SolicitudNotificacion(
            titulo=titulo,
            mensaje=cuerpo,
            tipo=tipo,
            prioridad=prioridad,
            categoria=categoria,
            destinatario_ids=[persona_id],
            ruta_accion=ruta_accion,
            datos_accion=datos_accion,
        )
        return await self.enviar_notificacion(solicitud)

    # ─── CONSULTA ──────────────────────────────────────────

    async def obtener_notificaciones(
        self,
        persona_id: int,
        pagina: int = 1,
        tamano_pagina: int = 20,
    ) -> dict:
        return await self.notificacion_repo.obtener_notificaciones_por_persona(
            persona_id=persona_id,
            pagina=pagina,
            tamano_pagina=tamano_pagina,
        )

    # ─── LECTURA ───────────────────────────────────────────

    async def marcar_como_leida(
        self, persona_id: int, notificacion_id: int
    ) -> None:
        # 1. PostgreSQL (se actualiza via repositorio + commit en router)
        # La logica real de marcar entregada/leida en PG
        # se hace en el router directamente con el modelo
        await self.firestore_sync.marcar_como_leida(
            persona_id, notificacion_id
        )

    async def marcar_todas_como_leidas(self, persona_id: int) -> None:
        await self.firestore_sync.marcar_todas_como_leidas(persona_id)

    # ─── TOKENS FCM ────────────────────────────────────────

    async def registrar_token_dispositivo(
        self, persona_id: int, token: str, plataforma: str
    ) -> None:
        await self.firestore_sync.guardar_token_fcm(
            persona_id, token, plataforma
        )

    async def eliminar_token_dispositivo(
        self, persona_id: int, token: str
    ) -> None:
        await self.firestore_sync.eliminar_token_fcm(persona_id, token)

    # ─── DESTINATARIOS ─────────────────────────────────────

    async def obtener_destinatarios(
        self,
        busqueda: Optional[str] = None,
        db=None,
    ) -> list:
        from app.infrastructure.db.models import (
            Persona, ResidenteVivienda, MiembroVivienda, PropietarioVivienda,
            Vivienda,
        )
        from app.domain.entities.notificacion_entities import DestinatarioInfo

        query = db.query(Persona).filter(
            Persona.estado == "activo",
            Persona.eliminado == False,
        )
        if busqueda:
            termino = f"%{busqueda}%"
            query = query.filter(
                (Persona.nombres.ilike(termino))
                | (Persona.apellidos.ilike(termino))
                | (Persona.identificacion.ilike(termino))
            )
        personas = query.limit(100).all()

        resultado = []
        for persona in personas:
            manzana = None
            villa = None
            tipo = "residente"
            encontrado = False

            residente = db.query(ResidenteVivienda).filter(
                ResidenteVivienda.persona_residente_fk == persona.persona_pk,
                ResidenteVivienda.estado == "activo",
                ResidenteVivienda.eliminado == False,
            ).first()
            if residente:
                tipo = "residente"
                encontrado = True
                vivienda = residente.vivienda
                if vivienda:
                    manzana = vivienda.manzana
                    villa = vivienda.villa

            if not encontrado:
                propietario = db.query(PropietarioVivienda).filter(
                    PropietarioVivienda.persona_propietario_fk == persona.persona_pk,
                    PropietarioVivienda.estado == "activo",
                    PropietarioVivienda.eliminado == False,
                ).first()
                if propietario:
                    tipo = "propietario"
                    encontrado = True
                    vivienda = propietario.vivienda
                    if vivienda:
                        manzana = vivienda.manzana
                        villa = vivienda.villa

            if not encontrado:
                miembro = db.query(MiembroVivienda).filter(
                    MiembroVivienda.persona_miembro_fk == persona.persona_pk,
                    MiembroVivienda.estado == "activo",
                    MiembroVivienda.eliminado == False,
                ).first()
                if miembro:
                    tipo = "miembro_familia"
                    encontrado = True
                    vivienda = miembro.vivienda
                    if vivienda:
                        manzana = vivienda.manzana
                        villa = vivienda.villa

            if not encontrado:
                continue

            resultado.append(
                DestinatarioInfo(
                    persona_id=persona.persona_pk,
                    nombre_completo=f"{persona.nombres} {persona.apellidos}",
                    identificacion=persona.identificacion,
                    manzana=manzana,
                    villa=villa,
                    tipo=tipo,
                )
            )
        return resultado

    # ─── INTERNOS ──────────────────────────────────────────

    async def _obtener_todos_los_residentes(self) -> List[int]:
        """Obtiene los IDs de todos los residentes, miembros y propietarios activos"""
        from app.infrastructure.db.database import SessionLocal
        from app.infrastructure.db.models import (
            ResidenteVivienda, MiembroVivienda, PropietarioVivienda,
        )

        db = SessionLocal()
        try:
            ids = set()
            residentes = db.query(ResidenteVivienda).filter(
                ResidenteVivienda.estado == "activo",
                ResidenteVivienda.eliminado == False,
            ).all()
            for r in residentes:
                ids.add(r.persona_residente_fk)
            miembros = db.query(MiembroVivienda).filter(
                MiembroVivienda.estado == "activo",
                MiembroVivienda.eliminado == False,
            ).all()
            for m in miembros:
                ids.add(m.persona_miembro_fk)
            propietarios = db.query(PropietarioVivienda).filter(
                PropietarioVivienda.estado == "activo",
                PropietarioVivienda.eliminado == False,
            ).all()
            for p in propietarios:
                ids.add(p.persona_propietario_fk)
            return list(ids)
        finally:
            db.close()

    async def _enviar_push(
        self,
        destinatario_ids: List[int],
        titulo: str,
        cuerpo: str,
        notificacion_id: int,
        datos: dict,
    ) -> dict:
        """Envia push notification a todos los destinatarios usando multicast."""
        tokens_por_persona = (
            await self.firestore_sync.obtener_tokens_por_personas(
                destinatario_ids
            )
        )

        if not tokens_por_persona:
            return {
                "exitosos": 0,
                "fallidos": 0,
                "errores": ["Ningun destinatario tiene tokens FCM"],
            }

        datos_fcm = {
            **datos,
            "notificacion_id": str(notificacion_id),
        }

        todos_los_tokens = []
        for persona_id, tokens in tokens_por_persona.items():
            todos_los_tokens.extend(tokens)

        tokens_unicos = list(set(todos_los_tokens))

        if not tokens_unicos:
            return {
                "exitosos": 0,
                "fallidos": 0,
                "errores": ["Tokens FCM vacios"],
            }

        resultado = await self.push_service.enviar_push_multicast(
            tokens=tokens_unicos,
            titulo=titulo,
            cuerpo=cuerpo,
            datos=datos_fcm,
        )

        return {
            "exitosos": resultado.get("exitosos", 0),
            "fallidos": resultado.get("fallidos", 0),
            "errores": resultado.get("errores", []),
        }
