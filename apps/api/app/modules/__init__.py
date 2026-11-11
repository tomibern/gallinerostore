"""Módulos de dominio.

Cada módulo sigue la misma forma y los routers no tienen lógica:

- ``router``: endpoints HTTP; valida entrada y delega en el service.
- ``schemas``: modelos Pydantic de entrada y salida.
- ``service``: reglas de negocio.
- ``repository``: acceso a datos con SQLAlchemy.

En el núcleo no aparece nada de un cliente concreto: lo específico sale de
``config/store.toml``, de ``brand/`` o de la base de datos.
"""
