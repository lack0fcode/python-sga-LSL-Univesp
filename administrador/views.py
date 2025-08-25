# administrador/views.py
from django.shortcuts import render, redirect, get_object_or_404
from core.decorators import admin_required
from core.models import CustomUser  # Importe o modelo CustomUser
from core.forms import CadastrarFuncionarioForm
from django.contrib import messages
from django.urls import reverse

@admin_required
def cadastrar_funcionario(request):
    if request.method == 'POST':
        form = CadastrarFuncionarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Funcionário cadastrado com sucesso!')
            return redirect(reverse('administrador:listar_funcionarios'))  # Redireciona para a lista de funcionários
        else:
            messages.error(request, 'Erro ao cadastrar o funcionário. Verifique os dados.')
    else:
        form = CadastrarFuncionarioForm()
    return render(request, 'administrador/cadastrar_funcionario.html', {'form': form})

@admin_required
def listar_funcionarios(request):
    funcionarios = CustomUser.objects.all()  # Obtém todos os usuários
    return render(request, 'administrador/listar_funcionarios.html', {'funcionarios': funcionarios})

@admin_required
def editar_funcionario(request, pk):
    funcionario = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = CadastrarFuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Funcionário atualizado com sucesso!')
            return redirect(reverse('administrador:listar_funcionarios'))
        else:
            messages.error(request, 'Erro ao atualizar o funcionário. Verifique os dados.')
    else:
        form = CadastrarFuncionarioForm(instance=funcionario)
    return render(request, 'administrador/cadastrar_funcionario.html', {'form': form})

@admin_required
def excluir_funcionario(request, pk):
    funcionario = get_object_or_404(CustomUser, pk=pk)
    funcionario.delete()
    messages.success(request, 'Funcionário excluído com sucesso!')
    return redirect(reverse('administrador:listar_funcionarios'))