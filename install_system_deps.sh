#!/usr/bin/env bash
# Script de instalação de dependências do sistema para Render

apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*
