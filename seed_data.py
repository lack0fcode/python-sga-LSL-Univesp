"""
Seed de dados para testar o caminho de TV (TV1 - Guichê e TV2 - Consultório).

Popula:
  - Usuários (guichê e profissional de saúde)
  - Pacientes com senha + tipo_senha (obrigatório para a TV mostrar algo)
  - Guichês
  - Chamadas (Guichê) com uma ativa + histórico 'confirmado'
  - ChamadasProfissional (Consultório) com uma ativa + histórico 'confirmado'

Depois de rodar:
  - /tv1/  -> mostra chamada ativa + histórico
  - /tv2/  -> mostra chamada ativa + histórico
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sga.settings")
django.setup()

from core.models import (  # noqa: E402
    Paciente,
    CustomUser,
    Guiche,
    Chamada,
    ChamadaProfissional,
)


# Credenciais do novo administrador (ajuste à vontade antes de rodar)
ADMIN_USERNAME = "danilomaciel"
ADMIN_CPF = "00000000000"
ADMIN_FIRST = "Danilo"
ADMIN_LAST = "Maciel"
ADMIN_PASSWORD = "admin123"


def _reset():
    print("--- Limpando TUDO (inclusive usuários) ---")
    Chamada.objects.all().delete()
    ChamadaProfissional.objects.all().delete()
    Guiche.objects.all().delete()
    Paciente.objects.all().delete()
    CustomUser.objects.all().delete()


def _criar_admin():
    print("\n--- Criando administrador ---")
    admin = CustomUser.objects.create(
        username=ADMIN_USERNAME,
        cpf=ADMIN_CPF,
        first_name=ADMIN_FIRST,
        last_name=ADMIN_LAST,
        funcao="administrador",
        is_staff=True,
        is_superuser=True,
    )
    admin.set_password(ADMIN_PASSWORD)
    admin.save()
    print(f"  OK {ADMIN_FIRST} {ADMIN_LAST} (administrador / superuser)")
    return admin


def _criar_usuarios():
    print("\n--- Criando usuários de operação ---")
    usuarios = [
        # (username, cpf, first_name, last_name, funcao, sala)
        ("11111111111", "11111111111", "Ana", "Recepcao", "recepcionista", None),
        ("22222222222", "22222222222", "Paulo", "Guiche", "guiche", None),
        ("33333333333", "33333333333", "Clara", "Medica", "profissional_saude", 10),
        ("44444444444", "44444444444", "Bruno", "Dentista", "profissional_saude", 11),
    ]
    criados = {}
    for username, cpf, first, last, funcao, sala in usuarios:
        user = CustomUser.objects.create(
            username=username,
            cpf=cpf,
            first_name=first,
            last_name=last,
            funcao=funcao,
            sala=sala,
            is_staff=True,
        )
        user.set_password("senha123")
        user.save()
        criados.setdefault(funcao, []).append(user)
        print(f"  OK {first} {last} ({funcao})")
    return criados


def _criar_pacientes(profissionais):
    """Cria pacientes e atribui um médico (profissional_saude) a cada um.

    O médico é distribuído em round-robin entre os profissionais criados.
    Se não houver profissionais, o campo fica vazio (nullable).
    """
    print("\n--- Criando pacientes (com médico atribuído) ---")
    pacientes_data = [
        # (nome, tipo_senha, senha, telefone, observacao)
        ("Maria Silva Oliveira", "G", "G001", "14991234567", "Paciente idoso, requer atenção."),
        ("José Santos",          "G", "G002", "14992345678", ""),
        ("Carla Mendes",         "C", "C001", "14993456789", "Curativo pós-cirúrgico."),
        ("João Ribeiro",         "E", "E001", "14994567890", ""),
        ("Beatriz Costa",        "D", "D001", "14995678901", "Alergia a anestésico local."),
    ]
    pacientes = []
    n_prof = len(profissionais)
    for i, (nome, tipo, senha, tel, obs) in enumerate(pacientes_data):
        medico = profissionais[i % n_prof] if n_prof else None
        p = Paciente.objects.create(
            nome_completo=nome,
            tipo_senha=tipo,
            senha=senha,
            telefone_celular=tel,
            observacoes=obs or None,
            profissional_saude=medico,
        )
        pacientes.append(p)
        medico_str = (
            f"{medico.first_name} {medico.last_name} (sala {medico.sala})"
            if medico else "sem médico"
        )
        print(f"  OK {nome} - senha {senha} - médico: {medico_str}")
    return pacientes


def _criar_guiches(usuarios_guiche):
    print("\n--- Criando guichês ---")
    guiches = []
    # Guichê 1 vinculado ao usuário Paulo; guichês 2 e 3 livres
    for numero in (1, 2, 3):
        func = usuarios_guiche[0] if (numero == 1 and usuarios_guiche) else None
        g = Guiche.objects.create(numero=numero, funcionario=func)
        guiches.append(g)
        print(f"  OK Guichê {numero} ({'vinculado a ' + func.first_name if func else 'livre'})")
    return guiches


def _criar_chamadas_tv1(pacientes, guiches):
    """Popula Chamada (TV1 - Guichê): algumas confirmadas + 1 ativa."""
    print("\n--- Criando chamadas (TV1 / Guichê) ---")
    # Histórico: 3 confirmações
    for paciente, guiche in zip(pacientes[:3], guiches * 2):
        Chamada.objects.create(paciente=paciente, guiche=guiche, acao="confirmado")
        print(f"  OK confirmado: {paciente.senha} no guichê {guiche.numero}")
    # Chamada ATIVA (a que a TV1 vai exibir)
    ativa = Chamada.objects.create(
        paciente=pacientes[3], guiche=guiches[0], acao="chamada"
    )
    print(f"  OK CHAMADA ATIVA: {ativa.paciente.senha} no guichê {ativa.guiche.numero}")


def _criar_chamadas_tv2(pacientes, profissionais):
    """Popula ChamadaProfissional (TV2 - Consultório): confirmadas + 1 ativa.

    Usa sempre o médico já atribuído ao paciente (paciente.profissional_saude),
    caindo para o primeiro profissional da lista se o paciente não tiver um.
    """
    print("\n--- Criando chamadas (TV2 / Consultório) ---")
    if not profissionais:
        print("  (sem profissionais de saúde, pulando)")
        return

    def _prof_do(paciente):
        return paciente.profissional_saude or profissionais[0]

    # Histórico
    for paciente in pacientes[:3]:
        prof = _prof_do(paciente)
        ChamadaProfissional.objects.create(
            paciente=paciente, profissional_saude=prof, acao="confirmado"
        )
        print(f"  OK confirmado: {paciente.senha} com {prof.first_name} (sala {prof.sala})")

    # Chamada ATIVA
    paciente_ativo = pacientes[4]
    prof_ativo = _prof_do(paciente_ativo)
    ativa = ChamadaProfissional.objects.create(
        paciente=paciente_ativo, profissional_saude=prof_ativo, acao="chamada"
    )
    print(
        f"  OK CHAMADA ATIVA: {ativa.paciente.senha} com "
        f"{ativa.profissional_saude.first_name} (sala {ativa.profissional_saude.sala})"
    )


def run_seed():
    print("=== Populando Banco ILSL (seed para testar caminho de TV) ===")
    _reset()
    _criar_admin()
    usuarios = _criar_usuarios()
    pacientes = _criar_pacientes(usuarios.get("profissional_saude", []))
    guiches = _criar_guiches(usuarios.get("guiche", []))
    _criar_chamadas_tv1(pacientes, guiches)
    _criar_chamadas_tv2(pacientes, usuarios.get("profissional_saude", []))

    print("\n=== Seed concluído ===")
    print("Logins (CPF / senha):")
    print(f"  {ADMIN_CPF}  {ADMIN_PASSWORD}   ({ADMIN_FIRST} {ADMIN_LAST} - ADMIN / superuser)")
    print("  11111111111  senha123   (Ana - recepcionista)")
    print("  22222222222  senha123   (Paulo - guichê)")
    print("  33333333333  senha123   (Clara - profissional, sala 10)")
    print("  44444444444  senha123   (Bruno - profissional, sala 11)")
    print("\nAcesse /tv/ ou /tv1/ e /tv2/ para ver as chamadas populadas.")
    print("/admin/ para o painel administrativo do Django.")


if __name__ == "__main__":
    run_seed()
