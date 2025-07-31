import typer

app = typer.Typer()

@app.command()
def run(config: str):
    cfg = load_config(config)
    manager = PipelineManager(cfg)
    manager.run()
