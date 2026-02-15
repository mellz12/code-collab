        const editor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
            lineNumbers: true,
            theme: 'dracula',
            mode: 'python',
            indentUnit: 4,
            smartIndent: true,
            tabSize: 4,
            lineWrapping: true
        });

        // Обработчик смены языка
        const languageSelect = document.getElementById('language');
        languageSelect.addEventListener('change', (event) => {
            const mode = event.target.value;
            let cmMode = '';
            if (mode === 'python') {
                cmMode = 'python';
            } else if (mode === 'c') {
                cmMode = 'text/x-csrc';
            } else if (mode === 'cpp') {
                cmMode = 'text/x-c++src';
            }
            editor.setOption('mode', cmMode);
        });


    document.getElementById('run-btn').addEventListener('click', async () => {
        const code = editor.getValue();
        const language = languageSelect.value;

        // Показываем индикатор загрузки
        document.getElementById('output').textContent = 'Выполняется...';

        try {
            const response = await fetch('/run_docker', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ code, language })
            });
            const data = await response.json();

            let outputText = '';
            if (data.error) {
                outputText = 'Ошибка:\n' + data.error;
            } else {
                if (data.output) outputText += data.output;
                if (data.error) outputText += '\nSTDERR:\n' + data.error;
                if (data.time) outputText += `\n\nВремя выполнения: ${data.time.toFixed(3)} с`;
            }
            document.getElementById('output').textContent = outputText || '(пустой вывод)';
        } catch (err) {
            document.getElementById('output').textContent = 'Ошибка при отправке запроса: ' + err;
        }
    });