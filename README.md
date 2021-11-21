This is the source code of the bypy OAuth relay server
======================================================

This is actually quite simple. To run it:

- Install prerequisites (once only)

```bash
pip install -r requirements.txt
```

- Config environments

```bash
export BAIDU_API_KEY=<baidu-pcs-client-id>
export BAIDU_API_SECRET=<baidu-pcs-client-secret>
export PORT=<the port to listen to>
```

- Run
`python app.py`

That's it.
