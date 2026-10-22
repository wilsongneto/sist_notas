from flask import Flask, flash, redirect, render_template, request, url_for

import banco
import utilidades

app = Flask(__name__)
app.secret_key = "chave-de-estudo"   # necessária para usar flash() (mensagens)

banco.criar_tabela()


# ---------- Funções auxiliares ----------

# Dicionário: situação -> nome da classe CSS usada para colorir o selo
CLASSES = {"Aprovado": "aprovado", "Recuperação": "recuperacao", "Reprovado": "reprovado"}

def converter_nota(texto):
    """Converte o texto do formulário em nota. Devolve None se for inválida.

    Na versão terminal, ler_nota() repetia a pergunta com while.
    Na web não dá para "esperar": o servidor responde e pronto.
    Por isso aqui só convertemos e devolvemos o resultado.
    """
    try:
        nota = float(texto.replace(",", "."))
    except ValueError:
        return None
    if 0 <= nota <= 10:
        return nota
    return None


def validar(nome, nota1, nota2):
    """Devolve uma mensagem de erro, ou None se estiver tudo certo."""
    if nome == "":
        return "O nome não pode ficar vazio."
    if nota1 is None or nota2 is None:
        return "As notas devem ser números entre 0 e 10."
    return None


def preparar(alunos):
    """Transforma as tuplas do banco em dicionários com média e situação.

    Dicionários são mais fáceis de usar no HTML: aluno.nome, aluno.media...
    """
    lista = []
    for id_aluno, nome, nota1, nota2 in alunos:
        media = utilidades.calcular_media(nota1, nota2)
        lista.append({
            "id": id_aluno,
            "nome": nome,
            "nota1": nota1,
            "nota2": nota2,
            "media": media,
            "situacao": utilidades.situacao(media),
            # classe CSS do "selo" colorido (sem acento, para usar no HTML)
            "classe": CLASSES[utilidades.situacao(media)],
        })
    return lista


# ---------- Rotas (as "telas" do sistema) ----------

@app.route("/")
def inicio():
    busca = request.args.get("busca", "").strip()
    if busca != "":
        alunos = banco.buscar_por_nome(busca)
    else:
        alunos = banco.listar_alunos()
    return render_template("index.html", alunos=preparar(alunos), busca=busca)


@app.route("/novo", methods=["GET", "POST"])

def novo():
    if request.method == "POST":
        nome = request.form["nome"].strip()
        nota1 = converter_nota(request.form["nota1"])
        nota2 = converter_nota(request.form["nota2"])

        erro = validar(nome, nota1, nota2)
        if erro:
            flash(erro, "erro")
            # devolve o formulário com o que a pessoa já tinha digitado
            aluno = {"nome": nome, "nota1": request.form["nota1"],  "nota2": request.form["nota2"]}
            return render_template("form.html", titulo="Novo aluno", aluno=aluno)

        banco.inserir_aluno(nome, nota1, nota2)
        flash("Aluno cadastrado com sucesso!", "ok")
        return redirect(url_for("inicio"))

    return render_template("form.html", titulo="Novo aluno", aluno=None)


@app.route("/editar/<int:id_aluno>", methods=["GET", "POST"])
def editar(id_aluno):
    aluno = banco.buscar_por_id(id_aluno)
    if aluno is None:
        flash("Aluno não encontrado.", "erro")
        return redirect(url_for("inicio"))

    if request.method == "POST":
        nome = aluno[1]   # o nome não muda; só as notas
        nota1 = converter_nota(request.form["nota1"])
        nota2 = converter_nota(request.form["nota2"])

        erro = validar(nome, nota1, nota2)
        if erro:
            flash(erro, "erro")
            dados = {"nome": nome, "nota1": request.form["nota1"],
                     "nota2": request.form["nota2"]}
            return render_template("form.html", titulo="Editar notas",
                                   aluno=dados, editando=True)

        banco.atualizar_notas(id_aluno, nota1, nota2)
        flash("Notas atualizadas!", "ok")
        return redirect(url_for("inicio"))

    dados = {"nome": aluno[1], "nota1": aluno[2], "nota2": aluno[3]}
    return render_template("form.html", titulo="Editar notas",
                           aluno=dados, editando=True)


@app.route("/remover/<int:id_aluno>", methods=["POST"])
def remover(id_aluno):
    # POST (e não GET) porque remover MUDA dados: não deve ser feito só por abrir um link
    if banco.buscar_por_id(id_aluno) is None:
        flash("Aluno não encontrado.", "erro")
    else:
        banco.remover_aluno(id_aluno)
        flash("Aluno removido.", "ok")
    return redirect(url_for("inicio"))


@app.route("/relatorio")
def relatorio():
    alunos = preparar(banco.listar_alunos())

    soma_medias = 0
    aprovados = 0
    recuperacao = 0
    reprovados = 0
    melhor = None

    for aluno in alunos:
        soma_medias += aluno["media"]
        if aluno["situacao"] == "Aprovado":
            aprovados += 1
        elif aluno["situacao"] == "Recuperação":
            recuperacao += 1
        else:
            reprovados += 1
        if melhor is None or aluno["media"] > melhor["media"]:
            melhor = aluno

    dados = {
        "total": len(alunos),
        "media_turma": soma_medias / len(alunos) if len(alunos) > 0 else 0,
        "aprovados": aprovados,
        "recuperacao": recuperacao,
        "reprovados": reprovados,
        "melhor": melhor,
    }
    return render_template("relatorio.html", dados=dados)


if __name__ == "__main__":
    app.run(debug=True)   # debug=True: reinicia sozinho ao salvar (só para estudo!)