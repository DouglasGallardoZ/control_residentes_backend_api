from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredential
import firebase_admin
from firebase_admin import auth as firebase_auth
from app.config import get_settings
from typing import Optional, Dict
from datetime import timedelta
from app.infrastructure.utils.time_utils import ahora_sin_tz

settings = get_settings()
security = HTTPBearer()


class FirebaseAuthenticator:
    """Autenticador usando Firebase Auth"""
    
    @staticmethod
    def verificar_token_firebase(credential: HTTPAuthCredential) -> Dict:
        """
        Verifica un idToken de Firebase
        
        Args:
            credential: Credencial HTTP con el token
            
        Returns:
            Dict con datos del usuario decodificados
        """
        try:
            decoded_token = firebase_auth.verify_id_token(credential.credentials)
            return decoded_token
        except firebase_auth.InvalidIdTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Error autenticando con Firebase"
            )


async def obtener_usuario_firebase(
    credential: HTTPAuthCredential = Depends(security)
) -> Dict:
    """
    Dependency para obtener usuario autenticado con Firebase
    """
    return FirebaseAuthenticator.verificar_token_firebase(credential)


# ============ JWT (Plan de migración) ============
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTHandler:
    """Handler para JWT (plan de migración a futuro)"""
    
    @staticmethod
    def crear_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crea un token JWT
        
        Args:
            data: Datos a incluir en el token
            expires_delta: Duración personalizada del token
            
        Returns:
            Token JWT codificado
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = ahora_sin_tz() + expires_delta
        else:
            expire = ahora_sin_tz() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def verificar_token(token: str) -> Dict:
        """
        Verifica y decodifica un token JWT
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            Datos decodificados del token
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado"
            )


async def obtener_usuario_jwt(
    credential: HTTPAuthCredential = Depends(security)
) -> Dict:
    """
    Dependency para obtener usuario autenticado con JWT (para migración futura)
    """
    try:
        return JWTHandler.verificar_token(credential.credentials)
    except HTTPException:
        raise


# Función que elige qué autenticador usar
async def obtener_usuario_actual(
    credential: HTTPAuthCredential = Depends(security)
) -> Dict:
    """
    Obtiene usuario actual.
    Actualmente usa Firebase Auth, pero puede cambiar a JWT en el futuro.
    """
    return FirebaseAuthenticator.verificar_token_firebase(credential)
