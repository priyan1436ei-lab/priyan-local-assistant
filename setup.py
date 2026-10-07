"""Explicit one-time downloads. Runtime never calls this installer."""
import argparse
import hashlib
from pathlib import Path
import sys
import urllib.request

MODEL='qwen2.5-3b-instruct-q4_k_m.gguf'
SHA256='626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d'
URL='https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/'+MODEL

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def download_model(directory):
    directory.mkdir(parents=True,exist_ok=True)
    target=directory/MODEL
    if target.exists() and digest(target)==SHA256:
        print('Verified model already installed.');return
    partial=target.with_suffix('.gguf.part')
    offset=partial.stat().st_size if partial.exists() else 0
    headers={'User-Agent':'Priyan-Local-Installer/2.0'}
    if offset:headers['Range']=f'bytes={offset}-'
    print('Downloading the official Qwen GGUF model (~2.1 GB). First-time internet is required.',flush=True)
    print('Model license: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF',flush=True)
    req=urllib.request.Request(URL,headers=headers)
    with urllib.request.urlopen(req,timeout=60) as response:
        if response.status!=206:offset=0
        mode='ab' if offset else 'wb'
        total=int(response.headers.get('Content-Length','0'))+offset
        count=offset;reported=0
        with partial.open(mode) as out:
            while True:
                chunk=response.read(1024*1024)
                if not chunk:break
                out.write(chunk);count+=len(chunk)
                if count-reported>30*1024*1024:
                    print(f'{count/1e6:.0f} / {total/1e6:.0f} MB',flush=True);reported=count
    print('Verifying SHA-256...',flush=True)
    if digest(partial)!=SHA256:
        raise ValueError('Checksum mismatch. Delete the .part file and retry. No unverified model was installed.')
    partial.replace(target)
    print('Model installed: '+str(target))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',action='store_true',help='Download and verify the local GGUF model')
    parser.add_argument('--voice',action='store_true',help='Download the optional multilingual Whisper model')
    parser.add_argument('--data',default=str(Path(__file__).parent/'agent-data'))
    args=parser.parse_args()
    if not args.model and not args.voice:parser.error('Choose --model, --voice, or both')
    models=Path(args.data).resolve()/'models'
    if args.model:download_model(models)
    if args.voice:
        try:from huggingface_hub import snapshot_download
        except ImportError:raise SystemExit('Install requirements-voice.txt first.')
        print('Downloading offline multilingual speech recognition weights...',flush=True)
        snapshot_download(repo_id='Systran/faster-whisper-small',local_dir=str(models/'whisper-small'))
        print('Voice model ready. Transcription uses only these local files.')

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('Setup failed: '+str(e),file=sys.stderr);raise SystemExit(1)
