"""
Django test file for the core app.

All test classes have been moved to separate files for better organization:
- Model tests: tests_models.py
- Form tests: tests_forms.py
- View tests: tests_views.py
- Integration tests: tests_integration.py
- Utils, decorators, and template tags tests: tests_utils.py

This file now serves as a reference point and maintains necessary imports
for any shared test utilities or base classes.
"""

from django.test import Client, TestCase
from django.urls import reverse
from django.http import HttpResponse
from django.utils import timezone
from unittest.mock import patch

from ..forms import CadastrarFuncionarioForm, CadastrarPacienteForm, LoginForm
from ..models import (
    Atendimento,
    Chamada,
    ChamadaProfissional,
    CustomUser,
    Guiche,
    Paciente,
    RegistroDeAcesso,
)
