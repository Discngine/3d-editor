# 3d-editor

# Build docker dev environment

`docker build -t discngine/editor .`

# Run dev environment

```bash
docker run -it -p 8000:8000 -v `pwd`:/app discngine/editor bash
> conda activate openforcefield
> python app.py
```

