from collections import defaultdict, deque
from itertools import cycle
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import guiche_required
from .forms import GuicheForm
from django.utils import timezone
from django.http import JsonResponse
from core.models import Chamada, Guiche, Paciente
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from gtts import gTTS
import os
import tempfile
from django.views.decorators.cache import never_cache
from django.urls import reverse
import datetime


@guiche_required
@login_required
def painel_guiche(request):
    senhas = []
    if request.method == 'POST':
        form = GuicheForm(request.POST)
        if form.is_valid():
            tipos_selecionados = []
            proporcoes = {}
            for field_name, field in form.fields.items():
                if field_name.startswith('tipo_senha_'):
                    tipo = field_name.replace('tipo_senha_', '').upper()
                    if form.cleaned_data[field_name]:  # Checkbox está marcado
                        tipos_selecionados.append(tipo)
                        proporcao_field_name = f'proporcao_{tipo.lower()}'
                        # Obtém a proporção do formulário, se fornecida, senão usa 1
                        proporcao = form.cleaned_data.get(proporcao_field_name)
                        try:
                            qtd = int(proporcao) if proporcao is not None else 1
                        except (ValueError, TypeError):
                            qtd = 1  # Garante que qtd seja um inteiro, mesmo se a conversão falhar
                        proporcoes[tipo] = qtd
                    else:
                        # Se o tipo de senha não está selecionado, remove a proporção da sessão (se existir)
                        tipo_lower = tipo.lower()
                        if f'proporcao_{tipo_lower}' in request.session.get('filtros_guiche', {}).get('proporcoes', {}):
                            del request.session['filtros_guiche']['proporcoes'][f'proporcao_{tipo_lower}']

            # Armazenar seleções na sessão
            request.session['filtros_guiche'] = {
                'tipos_selecionados': tipos_selecionados,
                'proporcoes': proporcoes,
            }

            return redirect('guiche:painel_guiche')


    else:  # GET
        form = GuicheForm()

        # Recuperar seleções da sessão
        filtros_guiche = request.session.get('filtros_guiche')
        if filtros_guiche:
            tipos_selecionados = filtros_guiche.get('tipos_selecionados', [])
            proporcoes = filtros_guiche.get('proporcoes', {})

            # Buscar senhas do dia e somente dos tipos selecionados
            pacientes = Paciente.objects.filter(
                horario_geracao_senha__date=(timezone.now() - datetime.timedelta(hours=3)).date(),
                tipo_senha__in=tipos_selecionados,
                atendido=False
            ).order_by('horario_geracao_senha')

            # Agrupa por tipo
            grupos = defaultdict(deque)
            for paciente in pacientes:
                prefixo = paciente.tipo_senha
                if prefixo in proporcoes:
                    grupos[prefixo].append(paciente)

            # Monta fila com base nas proporções
            ordem = []
            for tipo, qtd in proporcoes.items():
                try:
                    qtd = int(qtd) if qtd is not None else 1  # Tenta converter para inteiro ou usa 1
                except (ValueError, TypeError):
                    qtd = 1  # Garante que qtd seja um inteiro, mesmo se a conversão falhar
                ordem.extend([tipo] * qtd)

            ciclo_ordem = cycle(ordem)

            fila = []
            while any(grupos.values()):
                tipo = next(ciclo_ordem)
                if grupos[tipo]:
                    fila.append(grupos[tipo].popleft())

            senhas = fila
        else:
            # Se não há filtros na sessão, mostrar todas as senhas do dia
            senhas = Paciente.objects.filter(horario_geracao_senha__date=(timezone.now() - 
            datetime.timedelta(hours=3)).date(), atendido=False).order_by('horario_geracao_senha')

        # Buscar histórico
        historico_chamadas = Chamada.objects.all().order_by('-data_hora')[:10]

        return render(request, 'guiche/painel_guiche.html', {'form': form, 'senhas': senhas, 'historico_chamadas': historico_chamadas, 'form': form})


@require_POST
@csrf_exempt
@login_required
@guiche_required
def chamar_senha(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    guiche = get_guiche_do_usuario(request.user)

    # Chama realizar_acao_senha e armazena o resultado
    response = realizar_acao_senha(request, paciente.senha, guiche.numero, paciente.nome_completo, paciente_id, 'chamada')
    
    # Retorna o JsonResponse
    return response

@require_POST
@csrf_exempt
@login_required
@guiche_required
def reanunciar_senha(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    guiche = get_guiche_do_usuario(request.user)

    # Chama realizar_acao_senha e armazena o resultado
    response = realizar_acao_senha(request, paciente.senha, guiche.numero, paciente.nome_completo, paciente_id, 'reanuncio')
    
    # Retorna o JsonResponse
    return response

@require_POST
@csrf_exempt
@login_required
@guiche_required
def confirmar_atendimento(request, paciente_id):
    guiche = get_guiche_do_usuario(request.user)
    paciente = Paciente.objects.get(id=paciente_id)

    Chamada.objects.create(paciente=paciente, guiche=guiche, acao='confirmado')

    # Limpar o guichê (senha_atendida, em_atendimento)
    guiche.senha_atendida = None
    guiche.em_atendimento = False
    guiche.save()

    # Disponibilizar para o profissional de saúde
    paciente.atendido = True  # Marque o paciente como atendido
    paciente.save()
    
    return JsonResponse({'status': 'ok'})


def realizar_acao_senha(request, senha, guiche,nome, paciente_id, acao):
    guiche_obj = Guiche.objects.get(numero=guiche)
    paciente = Paciente.objects.get(id=paciente_id)

    Chamada.objects.create(paciente=paciente, guiche=guiche_obj, acao=acao)
    #Recuperar dados para passar para a tv
    data = {
            'senha': senha,
            'nome_completo': nome,
            'guiche': guiche
            }
    return JsonResponse({'status': 'ok','data':data})


@never_cache
def tv1_view(request):
    try:
        # Obtém a última chamada de todos os guichês
        ultima_chamada = Chamada.objects.filter(acao__in=['chamada', 'reanuncio']).latest('data_hora')
        senha_chamada = ultima_chamada.paciente
        nome_completo = ultima_chamada.paciente.nome_completo
        numero_guiche = ultima_chamada.guiche.numero  # Obtém o número do guichê
        historico_chamadas = Chamada.objects.order_by('-data_hora')[:5]
    except Chamada.DoesNotExist:
        senha_chamada = None
        nome_completo = None
        numero_guiche = None
        historico_chamadas = []
        ultima_chamada = None  # Define ultima_chamada como None
    
    context = {
        'senha_chamada': senha_chamada,
        'nome_completo': nome_completo,
        'numero_guiche': numero_guiche,  # Adiciona o número do guichê
        'historico_senhas': historico_chamadas,
        'ultima_chamada': ultima_chamada,  # Passa a última chamada para o template
        'guiche_numero': numero_guiche, # Garante que guiche_numero esteja no contexto
    }
    return render(request, 'guiche/tv1.html', context)

def get_guiche_do_usuario(user):
    try:
        return user.guiche
    except Guiche.DoesNotExist:
        raise Guiche.DoesNotExist("Nenhum guichê associado a este usuário.")
    
def tv1_api_view(request):
    try:
        # Obtém a última chamada de todos os guichês
        ultima_chamada = Chamada.objects.filter(acao__in=['chamada', 'reanuncio']).latest('data_hora')
        senha = ultima_chamada.paciente.senha
        nome_completo = ultima_chamada.paciente.nome_completo
        numero_guiche = ultima_chamada.guiche.numero
        chamada_id = ultima_chamada.id  # Adiciona o ID da chamada

        data = {
            'senha': senha,
            'nome_completo': nome_completo,
            'guiche': numero_guiche,
            'id': chamada_id,  # Inclui o ID no JSON
        }
    except Chamada.DoesNotExist:
        data = {'senha': '', 'nome_completo': '', 'guiche': '', 'id': ''}  # Garante que o ID também seja vazio

    return JsonResponse(data)