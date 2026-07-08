import json
from typing import List, Optional
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from app.domain.ports.notificacion_repositorio_port import NotificacionRepositorioPort
from app.infrastructure.db.models import Notificacion as NotificacionModel
from app.infrastructure.db.models import NotificacionDestino as NotificacionDestinoModel
from app.domain.entities.models import Notificacion as NotificacionEntity
from app.domain.entities.notificacion_entities import NotificacionDestino as NotificacionDestinoEntity
from app.infrastructure.utils.time_utils import ahora_sin_tz


class NotificacionRepositorioImpl(NotificacionRepositorioPort):
    """Adaptador concreto: persistencia de notificaciones en PostgreSQL"""

    def __init__(self, db: Session):
        self.db = db

    async def guardar_notificacion(
        self, notificacion: NotificacionEntity
    ) -> NotificacionModel:
        db_notificacion = NotificacionModel(
            tipo=notificacion.tipo,
            mensaje=notificacion.mensaje,
            persona_emisor_fk=notificacion.persona_emisor_id,
            usuario_creado=notificacion.usuario_creado or "api_system",
        )
        self.db.add(db_notificacion)
        self.db.flush()
        return db_notificacion

    async def guardar_destinos(
        self, destinos: List[NotificacionDestinoEntity]
    ) -> List[NotificacionDestinoEntity]:
        for destino in destinos:
            db_destino = NotificacionDestinoModel(
                notificacion_envio_fk=destino.notificacion_envio_id,
                persona_receptor_fk=destino.persona_receptor_id,
                entregada=destino.entregada,
                hora_entregado=destino.hora_entregado,
                error=destino.error,
                usuario_creado=destino.usuario_creado,
            )
            self.db.add(db_destino)
        self.db.flush()
        return destinos

    async def obtener_notificaciones_por_persona(
        self,
        persona_id: int,
        pagina: int = 1,
        tamano_pagina: int = 20,
    ) -> dict:
        query = (
            self.db.query(NotificacionDestinoModel, NotificacionModel)
            .join(
                NotificacionModel,
                NotificacionDestinoModel.notificacion_envio_fk
                == NotificacionModel.notificacion_pk,
            )
            .filter(NotificacionDestinoModel.persona_receptor_fk == persona_id)
            .filter(NotificacionDestinoModel.eliminado == False)
            .filter(NotificacionModel.eliminado == False)
            .order_by(desc(NotificacionModel.fecha_creado))
        )

        total = query.count()
        offset = (pagina - 1) * tamano_pagina
        resultados = query.offset(offset).limit(tamano_pagina).all()

        no_leidas = (
            self.db.query(func.count(NotificacionDestinoModel.notificacion_destino_pk))
            .join(
                NotificacionModel,
                NotificacionDestinoModel.notificacion_envio_fk
                == NotificacionModel.notificacion_pk,
            )
            .filter(NotificacionDestinoModel.persona_receptor_fk == persona_id)
            .filter(NotificacionDestinoModel.entregada == False)
            .filter(NotificacionDestinoModel.eliminado == False)
            .filter(NotificacionModel.eliminado == False)
            .scalar()
        )

        data = []
        for destino, notif in resultados:
            cuerpo_json = notif.mensaje
            titulo = ""
            cuerpo = cuerpo_json
            prioridad = "normal"
            categoria = "general"
            ruta_accion = None
            datos_accion = None

            if isinstance(cuerpo_json, str) and cuerpo_json.startswith("{"):
                try:
                    parsed = json.loads(cuerpo_json)
                    titulo = parsed.get("titulo", "")
                    cuerpo = parsed.get("cuerpo", cuerpo_json)
                    prioridad = parsed.get("prioridad", "normal")
                    categoria = parsed.get("categoria", "general")
                    ruta_accion = parsed.get("ruta_accion")
                    datos_accion = parsed.get("datos_accion")
                except json.JSONDecodeError:
                    pass

            data.append({
                "notificacion_id": notif.notificacion_pk,
                "titulo": titulo,
                "cuerpo": cuerpo,
                "tipo": notif.tipo,
                "prioridad": prioridad,
                "categoria": categoria,
                "leido": destino.entregada,
                "fecha_creacion": (
                    notif.fecha_creado.isoformat()
                    if notif.fecha_creado
                    else None
                ),
                "ruta_accion": ruta_accion,
                "datos_accion": datos_accion,
            })

        return {
            "data": data,
            "total": total,
            "no_leidas": no_leidas or 0,
            "pagina": pagina,
            "tamano_pagina": tamano_pagina,
            "total_paginas": max(1, (total + tamano_pagina - 1) // tamano_pagina),
            "tiene_mas": (pagina * tamano_pagina) < total,
        }

    async def obtener_notificacion_por_id(
        self, notificacion_id: int
    ) -> Optional[NotificacionModel]:
        return (
            self.db.query(NotificacionModel)
            .filter(
                NotificacionModel.notificacion_pk == notificacion_id,
                NotificacionModel.eliminado == False,
            )
            .first()
        )

    async def marcar_como_entregada(self, destino_id: int) -> None:
        destino = (
            self.db.query(NotificacionDestinoModel)
            .filter(
                NotificacionDestinoModel.notificacion_destino_pk == destino_id
            )
            .first()
        )
        if destino:
            destino.entregada = True
            destino.hora_entregado = ahora_sin_tz()
            self.db.flush()

    async def marcar_error_envio(self, destino_id: int, error: str) -> None:
        destino = (
            self.db.query(NotificacionDestinoModel)
            .filter(
                NotificacionDestinoModel.notificacion_destino_pk == destino_id
            )
            .first()
        )
        if destino:
            destino.error = error
            self.db.flush()
