.PHONY: demo ask eval test api

demo:
	PYTHONPATH=src python -m enterprise_graphrag.cli demo

ask:
	PYTHONPATH=src python -m enterprise_graphrag.cli ask "上线前需要完成哪些工作？"

eval:
	PYTHONPATH=src python -m enterprise_graphrag.cli eval --json

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

api:
	uvicorn enterprise_graphrag.api:create_app --factory --host 0.0.0.0 --port 8000
