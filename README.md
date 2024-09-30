# PISI1 Projeto

Projeto de um site com ferramentas para segurança de dados usando FastAPI e Jinja2.

 - ### Principais bibliotecas:
     - FastAPI, o framework escolhido para o projeto. Simples, conhecido por ser um framworke lightweight
     - Pydantic, faz o typecheck para os dados e formularios da aplicação. Como o python não é uma linguagem  fortemente tipada, essa biblioteca ajuda com isso.
     - SQLAlchemy, biblioteca para o ORM e CRUDE do projeto. permite criar e gerir banco de  dados SQL. SQLite foi o escolhido paro o projeto.
     - Jinja2, biblioteca que renderiza os templates HTML.
       
## Instalação

Guia para instalação do projeto. Python 3.9+

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


# Telas
![hgnfgvbdfghhtrf](https://github.com/user-attachments/assets/fce7cad9-4d28-4de1-ab87-bb36909eb0fa)
![hfgbvxcvsdgf](https://github.com/user-attachments/assets/601cd0b1-6e1d-4817-9f2b-8f69c2c51f14)
![ehsgfnsdfgdfg](https://github.com/user-attachments/assets/b1465cdb-66cd-4eda-9c6d-f6966dab251c)
![cdkdjfgbdjlhvd](https://github.com/user-attachments/assets/bceaa992-6a6e-4865-98df-9ca2ee96968d)
![Capturar](https://github.com/user-attachments/assets/dea07fb0-735b-4729-be28-7ee7b404ee11)
![wadsfcsdgregfdsg](https://github.com/user-attachments/assets/3c597b65-fb5d-483d-8504-06921a1da675)
