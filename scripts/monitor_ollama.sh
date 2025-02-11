#!/bin/bash
watch -n 1 "ollama logs | tail -n 20 && \
          nvidia-smi | grep -E '4090|显存' && \
          free -h | grep Mem"
