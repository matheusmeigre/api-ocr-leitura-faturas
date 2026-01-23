# 🔧 Correção de Timeout - Resumo Executivo

## 🎯 O Problema

**Sintoma**: Primeira importação de fatura sempre falha com timeout. Segunda tentativa funciona.

**Causa**: Cold start do PaddleOCR - na primeira requisição, a API precisa carregar modelos ML (~200MB) que demoram 10-15 segundos.

---

## ✅ Solução Implementada

### 1. API Python (✅ CORRIGIDA)

**Arquivo modificado**: `main.py`

**Mudanças**:
- ✅ Adicionado warmup automático do PaddleOCR no startup
- ✅ Criado endpoint `/health/ready` para verificar se API está pronta
- ✅ Flag `ocr_ready` para monitorar estado de inicialização

**Resultado**: API agora carrega PaddleOCR na inicialização, eliminando cold start para usuários.

---

### 2. Cliente TypeScript (⏳ VOCÊ PRECISA CORRIGIR)

**Problema**: Timeout muito curto (padrão ~10-30s)

**Solução**: 

#### Opção Simples - Aumentar Timeout

```typescript
const controller = new AbortController()
const timeoutId = setTimeout(() => controller.abort(), 60000) // 60s

const response = await fetch(OCR_API_URL, {
  method: 'POST',
  body: formData,
  signal: controller.signal,
})
clearTimeout(timeoutId)
```

#### Opção Completa - Com Retry

Use o **prompt detalhado** em [`FIX_TIMEOUT_CLIENT.md`](./FIX_TIMEOUT_CLIENT.md) com uma IA especializada.

---

## 🚀 Deploy

### API (Python)

```bash
git add main.py documents/
git commit -m "fix: add PaddleOCR warmup to prevent cold start timeout"
git push origin main
```

Aguarde 2-3 minutos para Render fazer deploy e inicializar.

### Cliente (TypeScript)

1. Abra [`FIX_TIMEOUT_CLIENT.md`](./FIX_TIMEOUT_CLIENT.md)
2. Copie o prompt para IA especializada
3. Cole no ChatGPT/Claude/Copilot
4. Aplique as correções sugeridas
5. Teste localmente
6. Faça deploy

---

## 🧪 Como Testar

### 1. Verifique se API está pronta

```bash
curl https://sua-api.render.com/health/ready

# Esperado:
# {
#   "status": "ready",
#   "ocr_initialized": true
# }
```

### 2. Faça upload de teste

- Upload de um PDF Nubank
- **Primeira tentativa deve funcionar** (antes falhava)
- Tempo esperado: 5-10 segundos

---

## 📊 Métricas Esperadas

| Métrica | Antes | Depois |
|---------|-------|--------|
| 1ª requisição - sucesso | 0% | 95%+ |
| 1ª requisição - tempo | Timeout | ~6-8s |
| 2ª+ requisição - tempo | ~6s | ~5-6s |
| Necessidade de retry | Alta | Baixa |

---

## 📚 Documentação Completa

1. **[FIX_TIMEOUT_CLIENT.md](./FIX_TIMEOUT_CLIENT.md)** - Guia completo + prompt para IA corrigir cliente
2. **[ANALISE_TIMEOUT.md](./ANALISE_TIMEOUT.md)** - Análise técnica detalhada
3. **[README_TIMEOUT_FIX.md](./README_TIMEOUT_FIX.md)** (este arquivo) - Resumo executivo

---

## ✅ Checklist

API:
- [x] Warmup implementado
- [x] Endpoint /health/ready criado
- [ ] Deploy realizado
- [ ] Logs confirmam: "✅ PaddleOCR aquecido e pronto!"

Cliente:
- [ ] Timeout aumentado para 60s
- [ ] Retry implementado (opcional mas recomendado)
- [ ] Deploy realizado
- [ ] Teste de primeira importação bem-sucedido

---

## 💡 TL;DR

**API**: ✅ Já corrigida - faz warmup do OCR no startup  
**Cliente**: ⏳ Você precisa aumentar timeout de 10s → 60s  
**Solução**: Use o prompt em FIX_TIMEOUT_CLIENT.md com IA  

---

**Status**: 🟢 API pronta | 🟡 Aguardando correção no cliente
