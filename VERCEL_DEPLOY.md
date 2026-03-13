# Guia: Deploy da Interface Completa no Vercel

Para ter toda a sua interface (o projeto `diabeticoimortal`) e o seu backend (`DiabeticAssitant`) funcionando no Vercel, você deve seguir estes passos:

## 1. Estrutura do Projeto
O ideal é que o Vercel gerencie ambos. Como eles estão em pastas separadas, você tem duas opções:

### Opção A: Dois Projetos Separados (Recomendado)
1. **Deploy do Backend:** Conecte a pasta `DiabeticAssitant` ao Vercel. Ele usará o `vercel.json` já existente para servir a API.
2. **Deploy do Frontend:** Conecte a pasta `diabeticoimortal` ao Vercel como um novo projeto. O Vercel detectará automaticamente que é um projeto Vite/React.

### Opção B: Monorepo (Tudo em um link)
Você pode mover a pasta `diabeticoimortal` para dentro de `DiabeticAssitant` e configurar o `vercel.json` para servir os arquivos estáticos do frontend e as rotas da API.

---

## 2. Conectando as Partes (Integração)

O frontend precisa saber onde a API está hospedada. No projeto `diabeticoimortal`, você deve:

1. Criar um arquivo `.env.production` (ou usar as variáveis de ambiente do Vercel).
2. Definir a URL da API:
   ```env
   VITE_API_URL=https://seu-backend-diabetic-assistant.vercel.app
   ```
3. No seu código React, certifique-se de usar `import.meta.env.VITE_API_URL` para fazer as chamadas.

---

## 3. Comandos de Verificação

Antes de subir, você pode testar localmente se tudo está "conversando":

- **Backend:** `venv\Scripts\pytest backend/tests/test_smoke.py`
- **Frontend:** No diretório `diabeticoimortal`, execute `npm run dev`.

> [!TIP]
> Use o **Vercel CLI** para facilitar o deploy direto do seu terminal:
> `npm i -g vercel`
> `vercel` (dentro de cada pasta)
