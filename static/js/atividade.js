// static/js/atividade.js
document.addEventListener('DOMContentLoaded', function() {
    let ultimaAtividade = Date.now();
    const INTERVALO_PING = 30000; // 30 segundos
    const INTERVALO_INATIVIDADE = 120000; // 2 minutos

    // Função para registrar atividade
    function registrarAtividade() {
        ultimaAtividade = Date.now();

        // Enviar ping para o servidor
        fetch('/administrador/registrar-atividade/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'same-origin'
        }).catch(error => {
            console.log('Erro ao registrar atividade:', error);
        });
    }

    // Função para obter cookie CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Registrar atividade em vários eventos
    const eventos = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

    eventos.forEach(evento => {
        document.addEventListener(evento, function() {
            // Debounce: só registrar se passou tempo suficiente
            if (Date.now() - ultimaAtividade > 5000) { // 5 segundos
                registrarAtividade();
            }
        }, true);
    });

    // Ping periódico a cada 30 segundos
    setInterval(function() {
        const tempoDesdeUltimaAtividade = Date.now() - ultimaAtividade;

        // Só enviar ping se teve atividade recente (nos últimos 2 minutos)
        if (tempoDesdeUltimaAtividade < INTERVALO_INATIVIDADE) {
            registrarAtividade();
        }
    }, INTERVALO_PING);

    // Registrar atividade inicial
    registrarAtividade();
});