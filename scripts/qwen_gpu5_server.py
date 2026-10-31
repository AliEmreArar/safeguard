"""Start one workspace-local GGUF server on the explicitly allocated GPU 5."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / '.cache/ollama/lib/ollama/llama-server'
DEPOT = Path('/mnt/aselsanlab_ds/proje3/ollama_models')
GPU = 'GPU-df6a0bca-a90a-9d22-c5c1-69cf30f6f8b6'
GPUS = {4: 'GPU-4b0f4ec3-16a6-2fc5-afcd-d3d4e014e14e', 5: GPU}
MODELS = {
    'qwen38': ('qwen3.8/27b-q4_K_M', 'qwen3.8-27b-q4'),
    'qwen36moe': ('qwen3.6/35b-a3b-q4_K_M', 'qwen3.6-35b-a3b-q4'),
    'qwen35small': ('qwen3.5/9b-q4_K_M', 'qwen3.5-9b-q4'),
}
LOCAL_MODELS = {
    'qwen3erotic': (
        ROOT / 'models/Qwen3-30B-A3B-abliterated-erotic-i1-GGUF'
        / 'Qwen3-30B-A3B-abliterated-erotic.i1-Q4_K_M.gguf',
        'qwen3-30b-a3b-erotic-q4',
        18556686976,
    ),
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('model', choices=(*MODELS, *LOCAL_MODELS))
    p.add_argument('--port', type=int, default=18085)
    p.add_argument('--gpu', type=int, choices=GPUS, default=5)
    p.add_argument('--ctx-size', type=int)
    p.add_argument('--replace-owned-pid', type=int)
    p.add_argument('--parallel', type=int, choices=(1, 8, 16, 32, 64), default=8)
    args = p.parse_args()
    gpu = GPUS[args.gpu]
    if args.replace_owned_pid:
        process = Path(f'/proc/{args.replace_owned_pid}')
        argv = (process / 'cmdline').read_bytes().split(b'\0')
        if (process / 'cwd').resolve() != ROOT or Path(argv[0].decode()).name != 'llama-server':
            raise RuntimeError('Refusing to stop a process outside this workspace')
        os.kill(args.replace_owned_pid, signal.SIGINT)
        import time
        deadline = time.monotonic()+30
        while process.exists() and time.monotonic() < deadline:
            time.sleep(0.2)
        if process.exists():
            raise RuntimeError('Previous server did not stop')
    if args.model in LOCAL_MODELS:
        model, alias, expected_size = LOCAL_MODELS[args.model]
    else:
        manifest_path, alias = MODELS[args.model]
        manifest = json.loads((DEPOT / 'manifests/registry.ollama.ai/library' / manifest_path).read_text())
        layer = next(x for x in manifest['layers'] if x['mediaType'] == 'application/vnd.ollama.image.model')
        model = DEPOT / 'blobs' / layer['digest'].replace(':', '-')
        expected_size = layer['size']
    if model.stat().st_size != expected_size:
        raise ValueError('Model size differs from its manifest')
    env = dict(os.environ)
    lib = BINARY.parent
    env.update(CUDA_VISIBLE_DEVICES=gpu, GGML_BACKEND_PATH=str(lib/'cuda_v13/libggml-cuda.so'),
               LD_LIBRARY_PATH=str(lib/'cuda_v13')+':'+str(lib))
    check = subprocess.run(['nvidia-smi', '-i', gpu, '--query-gpu=memory.free', '--format=csv,noheader,nounits'],
                           capture_output=True, text=True, check=True)
    if int(check.stdout.strip()) < 30000:
        raise RuntimeError(f'GPU {args.gpu} has less than 30000 MiB available')
    log = ROOT / 'results' / f'{args.model}_gpu{args.gpu}_server.log'
    cmd = [str(BINARY), '--model', str(model), '--alias', alias, '--host', '127.0.0.1', '--port', str(args.port),
           '--n-gpu-layers', '99', '--ctx-size', str(args.ctx_size or args.parallel*2048), '--parallel', str(args.parallel), '--threads', '8',
           '--flash-attn', 'on', '--jinja', '--reasoning-budget', '0', '--cache-ram', '0', '--log-file', str(log)]
    print(json.dumps({'alias': alias, 'gpu_uuid': gpu, 'model_bytes': model.stat().st_size, 'log': str(log)}), flush=True)
    os.execvpe(str(BINARY), cmd, env)


if __name__ == '__main__':
    main()
