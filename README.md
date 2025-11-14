# Protótipo: Automação de Declarações (Testes com Flask e Selenium)

> 🛑 **Repositório Arquivado: Fase de Testes** 🛑
>
> Este projeto foi a **prova de conceito (PoC)** e a fase inicial de testes para o sistema completo de automação de declarações do Ecac.
>
> O projeto final, completo e funcional, está em seu próprio repositório:
>
> ### [>> Acesse o Projeto Final Completo Aqui <<](https://github.com/LipeLou/rpa-ecac)

---

## 🎯 Objetivo deste Protótipo

O objetivo deste repositório era **validar a lógica de automação** em um ambiente controlado antes de aplicá-la ao portal oficial do Ecac.

Para isso, foi desenvolvido um ecossistema de testes local que simulava as interações necessárias:

1.  Um formulário web local (`localhost:5000`) foi criado com **Flask**, replicando os campos essenciais do site do governo.
2.  Um script de automação com **Selenium** foi usado para interagir com este formulário local.
3.  A manipulação e inserção de dados em lote foi testada usando **Pandas**.

Este ambiente permitiu testar e refinar rapidamente os *scrapers*, a lógica de preenchimento e a gestão de dados sem depender do ambiente externo.

## 🛠️ Tecnologias Utilizadas (Neste Protótipo)

* **Python:** Linguagem principal.
* **Flask:** Criação do servidor web local e do formulário de testes (simulação do Ecac).
* **Selenium:** Automação e interação com o formulário web local.
* **Pandas:** Leitura e manipulação dos dados de teste.

## STATUS

✅**Concluído/Arquivado.** Este protótipo cumpriu seu objetivo e todo o desenvolvimento ativo continua no repositório do projeto final.
