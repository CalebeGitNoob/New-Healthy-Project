🌿 Meu Nutri

App desktop simples para controle de calorias, peso e IMC, feito em Python com CustomTkinter.

Funcionalidades
Login, logout e várias contas de usuário
Cadastro com peso, altura, idade, sexo, nível de atividade e objetivo
Cálculo automático da meta calórica diária
Registro de refeições (com histórico por dia)
Registro de peso (com gráfico de evolução)
Cálculo de IMC
Como rodar

```bash pip install customtkinter python meu_nutri.py ```

Na primeira vez, o app pede para você criar uma conta.

Dados

Tudo é salvo localmente no arquivo `dados_nutri.json`, criado automaticamente na mesma pasta do script. Não é necessário internet.

Recomendado: adicione `dados_nutri.json` ao `.gitignore`, já que ele guarda dados pessoais.

Tecnologias
Python 3
CustomTkinter
tkinter e json (bibliotecas padrão)
Aviso

Este app é apenas uma ferramenta de acompanhamento pessoal e não substitui orientação profissional de nutricionistas.
