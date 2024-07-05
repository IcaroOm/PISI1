# PISI1 Projeto

Projeto com ferramentas basicas para segurança de dados de um usuario comum, como gerador de senha e checagem de vazamento de email.

## Instalação

Guia para instalação do projeto. Python 3.7+

1. Clone o repo:

    ```bash
    git clone https://github.com/IcaroOm/PISI1.git
    cd PISI1
    ```

2. Crie e ative ambiente virtual:

    ```bash
    python -m venv env
    source env/bin/activate  # Windows `env\Scripts\activate`
    ```

3. Instale dependecias:

    ```bash
    pip install -r requirements.txt
    ```

## Uso

Para rodar a aplicação use o seguinte comando:

```bash
uvicorn main:app
```

Isto abrirar um localhost em: `http://127.0.0.1:8000`.
