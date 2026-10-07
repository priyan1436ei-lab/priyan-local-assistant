"""Private stdio worker: only local GGUF loading and token generation."""
import json
import os
import sys

# Prevent optional model tooling from looking online. This worker never downloads models.
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
engine=None
signature=None
for line in sys.stdin:
    try:
        from llama_cpp import Llama
        request=json.loads(line)
        sig=(request['model_path'],request['context'],request['gpu_layers'])
        if sig!=signature:
            if engine is not None: engine.close()
            engine=Llama(model_path=sig[0],n_ctx=sig[1],n_gpu_layers=sig[2],
                         n_threads=max(1,min(8,(os.cpu_count() or 4)-1)),n_batch=128,verbose=False)
            signature=sig
        messages=request['messages']
        max_tokens=min(1500,sig[1]//3)
        def size():
            return sum(len(engine.tokenize(m['content'].encode(),add_bos=False))+12 for m in messages)
        # Leave generation headroom. Keep the system, most recent instruction and tool evidence.
        while size()>sig[1]-max_tokens-100 and len(messages)>3:
            messages.pop(1)
        if size()>sig[1]-max_tokens-100:
            raise ValueError('Message/context is too large. Shorten the question, disable document context, or increase the context budget.')
        result=engine.create_chat_completion(messages=messages,temperature=.2,max_tokens=max_tokens,
                                             response_format={'type':'json_object'})
        print(json.dumps({'content':result['choices'][0]['message']['content']},ensure_ascii=False),flush=True)
    except Exception as e:
        print(json.dumps({'error':str(e)},ensure_ascii=False),flush=True)
