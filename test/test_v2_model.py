from modelscope import snapshot_download

local_dir = snapshot_download(model_id="Ceceliachenen/paraphrase-multilingual-MiniLM-L12-v2", local_dir="/Users/a123/D盘/学习/尚硅谷/paraphrase-multilingual-MiniLM-L12-v2")

print(local_dir)