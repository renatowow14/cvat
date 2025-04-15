# CVAT - Anotacao Automatica com YOLOv3, DEXTR, SAM 1 e SAM 2 via Docker + Nuclio

Este repositório/documentação mostra como subir localmente o **CVAT** com suporte a **anotação automática e assistida**, utilizando modelos baseados em deep learning como **YOLOv3**, **DEXTR**, **SAM 1** e **SAM 2**, via **Nuclio**.

---

## 🚀 Pré-requisitos

- Docker + Docker Compose instalados
- Sistema operacional compatível (Ubuntu 20.04+, WSL2 ou Mac)
- GPU + NVIDIA Container Toolkit (para SAM 1 e SAM 2)

---

## 📦 Clonando o repositório

```bash
git clone https://github.com/opencv/cvat
cd cvat
```

---

## ⚙️ Subindo o CVAT com suporte a modelos serverless

Use o `docker-compose.serverless.yml` para ativar os modelos automáticos (YOLO, DEXTR, SAM, etc):

```bash
docker compose -f docker-compose.yml -f components/serverless/docker-compose.serverless.yml up -d --build
```

> ⚠️ Aguarde o download e inicialização de todos os containers (leva alguns minutos na primeira vez).

---

## 🌐 Expondo o CVAT para a rede local (WAN)

Por padrão, o CVAT escuta apenas no `localhost`. Para permitir acesso de outros dispositivos da rede (como `http://192.168.1.15:8080`):

1. No `docker-compose.yml`, altere os blocos de labels:

### `cvat_server`:
```yaml
labels:
  traefik.enable: "true"
  traefik.http.services.cvat.loadbalancer.server.port: "8080"
  traefik.http.routers.cvat.rule: PathPrefix(`/api/`) || PathPrefix(`/static/`) || PathPrefix(`/admin`) || PathPrefix(`/django-rq`)
  traefik.http.routers.cvat.entrypoints: web
```

### `cvat_ui`:
```yaml
labels:
  traefik.enable: "true"
  traefik.http.services.cvat-ui.loadbalancer.server.port: "80"
  traefik.http.routers.cvat-ui.rule: PathPrefix(`/`)
  traefik.http.routers.cvat-ui.entrypoints: web
```

2. Certifique-se que o serviço `traefik` está expondo as portas:
```yaml
ports:
  - 8080:8080
```

3. Reinicie os serviços:
```bash
docker compose down -v
docker compose -f docker-compose.yml -f components/serverless/docker-compose.serverless.yml up -d --build
```

Agora, acesse via IP da máquina:
```
http://192.168.1.15:8080
```

---

## 🔑 Criando usuário administrador

```bash
docker exec -it cvat_server bash -ic 'python3 manage.py createsuperuser'
```

---

## 🔎 Acessando o CVAT

```
http://localhost:8080
```

---

## 📥 Instalação do Nuclio CLI (`nuctl`)

```bash
# Baixar a versão mais recente do nuctl
curl -Lo nuctl https://github.com/nuclio/nuclio/releases/download/1.13.23/nuctl-1.13.23-linux-amd64

# Tornar executável
chmod +x nuctl

# Mover para um diretório do PATH
sudo mv nuctl /usr/local/bin/

# Verificar a instalação
nuctl version
```

> 💡 O comando `nuctl` precisa estar disponível no terminal antes de executar os scripts de deploy.

---

## 💻 Instalação de drivers NVIDIA + CUDA Toolkit (para SAM 1 e SAM 2)

```bash
# Instalar suporte a drivers automáticos e listar opções
apt install ubuntu-drivers-common -y
ubuntu-drivers devices

# Instalar driver recomendado (ex: 550)
sudo apt install nvidia-driver-550 -y

# Instalar toolkit para containers NVIDIA
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# (Opcional) Instalar GCC se não tiver
sudo apt-get install gcc -y

# Instalar CUDA Toolkit 12.8
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-8

# Configurar variáveis de ambiente
export PATH=/usr/local/cuda/bin${PATH:+:$PATH}
export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}

# Testar
nvcc -V
```

---

## 🤖 Deploy dos modelos YOLOv3 e DEXTR (CPU)

```bash
./serverless/deploy_cpu.sh serverless/openvino/dextr
./serverless/deploy_cpu.sh serverless/openvino/omz/public/yolo-v3-tf
```

> Isso registrará os modelos no painel Nuclio (`http://localhost:8070`) e permitirá seu uso no CVAT.

---

## 🧠 Deploy do SAM 1 (GPU)

```bash
./serverless/deploy_gpu.sh serverless/pytorch/facebookresearch/sam
```

> Reinicie os containers CVAT após o deploy:
```bash
docker compose restart
```

---

## 🧪 Deploy do SAM 2 (custom, GPU)

1. Clone ou copie os arquivos `function-gpu.yaml`, `main.py`, `model_handler.py` e `requirements.txt` para uma pasta:

```
sam2/
  └── nuclio/
      ├── function-gpu.yaml
      ├── main.py
      ├── model_handler.py
      └── requirements.txt
```

2. Execute:
```bash
./deploy_gpu.sh sam2/nuclio
```

3. Reinicie o CVAT:
```bash
docker compose restart
```

> O modelo `nuclio-sam2` aparecerá no menu **Actions > Automatic Annotation**.

---

## 🧑‍💻 Usando a anotação automática na interface

1. No CVAT, crie uma `Task`
2. Faça upload de imagens (ex: `lenna.png`)
3. Crie um label (ex: `person`)
4. Acesse o Job da imagem
5. Clique em `Actions → Automatic Annotation`
6. Escolha o modelo (YOLOv3, DEXTR, SAM 1, SAM 2)
7. Mapeie os labels e clique em **Annotate**
8. Clique em **Save**

---

## 📄 Exportando anotações

- `Actions → Export annotations`
- Formatos suportados: COCO, YOLO, Pascal VOC, XML, etc.

---

## 📊 Comparativo de Modelos

| Modelo  | Tipo       | Suporte     | Framework       | Recurso | Labels | Tipos de tarefa |
|---------|------------|-------------|------------------|---------|--------|-----------------|
| YOLOv3  | Detecção   | Oficial     | OpenVINO         | CPU     | person, car... | Caixa delimitadora |
| DEXTR   | Segmentação| Oficial     | OpenVINO         | CPU     | custom          | Segmentação interativa |
| SAM 1   | Segmentação| Oficial     | PyTorch + CUDA    | GPU     | custom          | Segmentação assistida |
| SAM 2   | Segmentação| Custom      | PyTorch 2.4 + CUDA 12.4 | GPU | custom          | Segmentação assistida |

---

## 📚 Referências

- [CVAT Docs](https://docs.cvat.ai/)
- [Nuclio Docs](https://nuclio.io/docs/latest/)
- [Segment Anything v1](https://github.com/facebookresearch/segment-anything)
- [Segment Anything v2](https://github.com/facebookresearch/segment-anything-2)

---

## ✅ TODO

- [ ] Automatizar deploy com Makefile
- [ ] Adicionar suporte ao modelo SAM-HQ
- [ ] Exportação com post-processamento customizado
