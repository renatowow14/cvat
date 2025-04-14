# 🫠 CVAT - Anotacao Automatica com YOLOv3 e DEXTR via Docker + Nuclio

Este repositório/documentação mostra como subir localmente o CVAT com suporte a anotação automática usando modelos baseados em deep learning como YOLOv3 e DEXTR, via Nuclio.

---

## 🚀 Pré-requisitos

- Docker + Docker Compose instalados
- Sistema operacional compatível (Ubuntu 20.04+, WSL2 ou Mac)

---

## 📦 Clonando o repositório

```bash
git clone https://github.com/opencv/cvat
cd cvat
```

---

## ⚙️ Subindo o CVAT com suporte a modelos serverless

Use o `docker-compose.serverless.yml` para ativar os modelos automáticos (YOLO, DEXTR, etc):

```bash
docker compose -f docker-compose.yml -f components/serverless/docker-compose.serverless.yml up -d
```

> ⚠️ Aguarde o download e inicialização de todos os containers (leva alguns minutos na primeira vez).

---

## 🔮 Criando usuário administrador

Acesse o container do backend e crie o superusuário:

```bash
docker exec -it cvat_server bash -ic 'python3 manage.py createsuperuser'
```

---

## 🔎 Acessando o CVAT

Abra o navegador e acesse:
```
http://localhost:8080
```

Login com o usuário que você criou no passo anterior.

---

## 🤖 Deploy dos modelos YOLOv3 e DEXTR

Os modelos são implantados como funções Nuclio. Execute os comandos:

```bash
./serverless/deploy_cpu.sh serverless/openvino/dextr
./serverless/deploy_cpu.sh serverless/openvino/omz/public/yolo-v3-tf
```

> Isso irá registrar os modelos no painel Nuclio (`http://localhost:8070`) e deixá-los prontos para uso no CVAT.

---

## 🔌 Testando via terminal (opcional)

```bash
# Baixar imagem de teste
curl -O https://upload.wikimedia.org/wikipedia/en/7/7d/Lenna_%28test_image%29.png
mv Lenna_\(test_image\).png lenna.png

# Codificar em base64
curl -s https://upload.wikimedia.org/wikipedia/en/7/7d/Lenna_%28test_image%29.png | base64 | tr -d '\n' > image.txt

# Testar YOLOv3
echo "{\"image\": \"$(cat image.txt)\"}" | nuctl invoke openvino-omz-public-yolo-v3-tf -c application/json --platform local
```

---

## 🧑‍💻 Usando a anotação automática via interface

1. No CVAT, crie uma `Task`
2. Faça upload da imagem `lenna.png`
3. Crie um label chamado `person`
4. Acesse o Job da imagem
5. Clique em `Actions → Automatic Annotation`
6. Escolha `YOLOv3` e mapeie `person → person`
7. Clique em **Annotate** e depois em **Save**

---

## 📄 Exportando as anotações

Você pode exportar no formato desejado:

- `Actions → Export annotations`
- Formatos: XML, COCO, YOLO, Pascal VOC, etc.

---

## 📦 Componentes do CVAT com suporte a anotação automática

**Serviços principais:**
- `cvat_ui`: Interface web do CVAT (`localhost:8080`)
- `cvat_server`: Backend Django principal
- `cvat_utils`: Utilitários do backend

**Workers:**
- `cvat_worker_import`: Importação de dados
- `cvat_worker_export`: Exportação de anotações
- `cvat_worker_annotation`: Processamento de tarefas de anotação
- `cvat_worker_chunks`, `cvat_worker_consensus`, etc.

**Banco de dados e cache:**
- `cvat_db`: PostgreSQL — armazena tarefas, usuários, anotações
- `cvat_redis_inmem`: Redis in-memory
- `cvat_redis_ondisk`: Redis persistente com Kvrocks
- `cvat_clickhouse`: Banco analítico para métricas

**Monitoramento e segurança:**
- `cvat_vector`: Coletor de logs com Vector
- `cvat_grafana`: Dashboard com métricas via Grafana
- `cvat_opa`: Open Policy Agent — controle de permissões

**Infraestrutura web:**
- `traefik`: Proxy reverso HTTP/HTTPS para rotear tráfego
- `nuclio`: Painel web Nuclio (`localhost:8070`)
- `nuclio-local-storage-reader`: Leitor de arquivos usado por funções Nuclio

---

## 🤖 Modelos de Anotação (Funções Serverless)

- `nuclio-nuclio-openvino-omz-public-yolo-v3-tf`: Modelo YOLOv3-TF
  - 📌 Detecta objetos em tempo real (ex: `person`, `car`, etc.)
- `nuclio-nuclio-openvino-dextr`: Modelo DEXTR
  - 📌 Segmenta objetos com base em 4 pontos extremos (requere intervenção do usuário)

---

## 🧠 Observações:

- Cada modelo é executado de forma independente e acessado sob demanda pelo CVAT GUI.
- O CVAT é modular: pode ser expandido com novos modelos, plugins, cloud storage, etc.

---

## 📚 Referências

- [Documentação Oficial CVAT](https://docs.cvat.ai/)
- [Segment Anything (SAM2)](https://github.com/facebookresearch/segment-anything)

---

## 📌 TODO

- [ ] Adicionar modelo SAM2 customizado
- [ ] Exportar anotação em COCO
- [ ] Automatizar deploy com Makefile ou script `.sh`

---
